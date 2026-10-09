import path from "node:path";
import { existsSync, readdirSync, readFileSync } from "node:fs";

// Render-output storage. STORAGE_DRIVER=local (default): files stay on disk
// under the job dir and the /files route streams them — the dev behaviour.
// STORAGE_DRIVER=s3: after a job finishes the worker uploads files/*.mp4 to
// object storage (S3 / B2 / MinIO) and the /files route 302s to a presigned
// GET. status.json outputs stay site-relative either way, so nothing else
// changes shape.

export type StorageDriver = "local" | "s3";

export function storageDriver(): StorageDriver {
  return process.env.STORAGE_DRIVER === "s3" ? "s3" : "local";
}

type S3Conf = { bucket: string; endpoint?: string; region: string; publicBase?: string };

function s3Conf(): S3Conf | null {
  if (storageDriver() !== "s3") return null;
  const bucket = process.env.S3_BUCKET;
  if (!bucket || !process.env.S3_ACCESS_KEY_ID || !process.env.S3_SECRET_ACCESS_KEY) return null;
  return {
    bucket,
    endpoint: process.env.S3_ENDPOINT,
    region: process.env.S3_REGION ?? "auto",
    publicBase: process.env.S3_PUBLIC_BASE_URL,
  };
}

let clientPromise: Promise<import("@aws-sdk/client-s3").S3Client> | null = null;
async function s3() {
  const conf = s3Conf();
  if (!conf) return null;
  if (!clientPromise) {
    clientPromise = (async () => {
      const { S3Client } = await import("@aws-sdk/client-s3");
      return new S3Client({
        region: conf.region,
        endpoint: conf.endpoint,
        forcePathStyle: Boolean(conf.endpoint),
        credentials: {
          accessKeyId: process.env.S3_ACCESS_KEY_ID!,
          secretAccessKey: process.env.S3_SECRET_ACCESS_KEY!,
        },
      });
    })();
  }
  return clientPromise;
}

export const renderKey = (family: string, jobId: string, name: string) =>
  `renders/${family}/${jobId}/${name}`;

// Upload a finished job's outputs to object storage. Returns the uploaded
// key names, or null when S3 is not configured (caller keeps local serving).
export async function uploadJobOutputs(dir: string, family: string, jobId: string): Promise<string[] | null> {
  const conf = s3Conf();
  const client = await s3();
  if (!conf || !client) return null;
  const filesDir = path.join(dir, "files");
  if (!existsSync(filesDir)) return [];
  const { PutObjectCommand } = await import("@aws-sdk/client-s3");
  const uploaded: string[] = [];
  for (const name of readdirSync(filesDir)) {
    if (!/^[\w.-]+\.mp4$/.test(name)) continue;
    const body = readFileSync(path.join(filesDir, name));
    await client.send(new PutObjectCommand({
      Bucket: conf.bucket, Key: renderKey(family, jobId, name),
      Body: body, ContentType: "video/mp4",
    }));
    uploaded.push(name);
  }
  return uploaded;
}

// How the /files route should serve one output. "local" = stream the file
// under the job dir; "redirect" = 302 to a presigned S3 GET.
export async function resolveOutputFile(dir: string, family: string, jobId: string, name: string):
  Promise<{ kind: "local"; filePath: string } | { kind: "redirect"; url: string } | null> {
  const base = path.basename(name);
  if (!/^[\w.-]+\.mp4$/.test(base)) return null;
  const conf = s3Conf();
  const client = conf && await s3();
  if (conf && client) {
    const { GetObjectCommand } = await import("@aws-sdk/client-s3");
    const { getSignedUrl } = await import("@aws-sdk/s3-request-presigner");
    const url = await getSignedUrl(client, new GetObjectCommand({
      Bucket: conf.bucket, Key: renderKey(family, jobId, base),
    }), { expiresIn: 15 * 60 });
    return { kind: "redirect", url };
  }
  const filePath = path.join(dir, "files", base);
  return existsSync(filePath) ? { kind: "local", filePath } : null;
}
