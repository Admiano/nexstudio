const assert = require("node:assert/strict");
const { test } = require("node:test");
const Module = require("node:module");
const path = require("node:path");
const { build } = require("esbuild");

const publicOrigin = "https://studio.example.test";
const fixtureKey = "__emailVerificationRedirectTest";

// Exercise the real handler, session creation and cookie code without a database
// or email delivery. Only persistence and the audit sink are replaced.
const handler = build({
  entryPoints: [path.join(__dirname, "../app/api/v1/auth/email/verify/route.ts")],
  bundle: true, write: false, platform: "node", format: "cjs", packages: "external",
  define: {
    "process.env.APP_ORIGIN": JSON.stringify(publicOrigin),
    "process.env.APP_ADDITIONAL_ORIGINS": JSON.stringify("https://scenebam.online"),
    "process.env.STUDIO_TRUST_SECRET": JSON.stringify("email-redirect-regression-test-secret-32-characters"),
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  plugins: [{
    name: "test-persistence",
    setup(builder) {
      builder.onResolve({ filter: /^(?:@\/lib\/db|\.\/db)$/ }, () => ({ path: "db", namespace: "fixture" }));
      builder.onResolve({ filter: /^@\/lib\/audit-log$/ }, () => ({ path: "audit", namespace: "fixture" }));
      builder.onLoad({ filter: /.*/, namespace: "fixture" }, args => ({
        contents: args.path === "db"
          ? `export const getPrisma = () => globalThis.${fixtureKey}.prisma;`
          : `export const appendAuditEvent = async event => globalThis.${fixtureKey}.audits.push(event);`,
        loader: "js",
      }));
    },
  }],
}).then(result => {
  const filename = path.join(__dirname, "email-verification-handler.cjs");
  const compiled = new Module(filename);
  compiled.filename = filename;
  compiled.paths = Module._nodeModulePaths(__dirname);
  compiled._compile(result.outputFiles[0].text, filename);
  return compiled.exports.GET;
});

function fixture(next = "/dashboard", { expired = false, claimed = true } = {}) {
  const state = { sessions: [], audits: [], claims: 0 };
  const user = { id: "test-user", email: "verify@example.test", privacyStatus: "ACTIVE" };
  const tx = {
    authChallenge: {
      findFirst: async () => expired ? null : { id: "test-challenge", identifier: user.email, payload: { next } },
      updateMany: async () => { state.claims++; return { count: claimed ? 1 : 0 }; },
      update: async () => ({}),
    },
    user: { findUnique: async () => user, update: async () => user },
    authIdentity: { upsert: async () => ({}) },
    session: { create: async input => { state.sessions.push(input.data); return input.data; } },
  };
  state.prisma = { $transaction: async callback => callback(tx) };
  globalThis[fixtureKey] = state;
  return state;
}

for (const origin of ["https://0.0.0.0:3000", "http://0.0.0.0:3000", "https://untrusted.example.test"]) {
  test(`verified email redirects to the configured public origin when request origin is ${origin}`, async () => {
    const state = fixture("/dashboard?tab=productions");
    const response = await (await handler)(new Request(`${origin}/api/v1/auth/email/verify?token=test-token`));
    assert.equal(response.status, 303);
    assert.equal(response.headers.get("location"), `${publicOrigin}/dashboard?tab=productions`);
    const cookie = response.headers.get("set-cookie");
    assert.match(cookie, /studio_session=[^;]+/);
    assert.match(cookie, /HttpOnly/i);
    assert.match(cookie, /Secure/i);
    assert.match(cookie, /SameSite=lax/i);
    assert.doesNotMatch(cookie, /Domain=/i);
    assert.equal(state.sessions.length, 1);
    assert.equal(state.audits[0].action, "AUTH_EMAIL_VERIFIED");
  });
}

for (const next of ["//outside.example.test", "/\\outside.example.test", "/\t/outside.example.test", "https://outside.example.test"]) {
  test(`unsafe return path ${JSON.stringify(next)} stays on the Studio origin`, async () => {
    fixture(next);
    const response = await (await handler)(new Request("https://0.0.0.0:3000/api/v1/auth/email/verify?token=test-token"));
    assert.equal(response.status, 303);
    assert.equal(response.headers.get("location"), `${publicOrigin}/studio`);
  });
}

for (const url of ["https://scenebam.online", "http://0.0.0.0:3000"]) {
  test(`configured app alias keeps its sign-in redirect and host-only cookie (${url})`, async () => {
    fixture("/studio");
    const response = await (await handler)(new Request(`${url}/api/v1/auth/email/verify?token=test-token`, {
      headers: { "x-forwarded-host": "scenebam.online", "x-forwarded-proto": "https" },
    }));
    assert.equal(response.status, 303);
    assert.equal(response.headers.get("location"), "https://scenebam.online/studio");
    assert.doesNotMatch(response.headers.get("set-cookie"), /Domain=/i);
  });
}

for (const host of ["outside.example.test", "[invalid-host"]) {
test(`an unconfigured or malformed forwarded host cannot redirect the verified session (${host})`, async () => {
  fixture("/studio");
  const response = await (await handler)(new Request("http://0.0.0.0:3000/api/v1/auth/email/verify?token=test-token", {
    headers: { "x-forwarded-host": host, "x-forwarded-proto": "https" },
  }));
  assert.equal(response.headers.get("location"), `${publicOrigin}/studio`);
});
}

for (const [name, options, status] of [
  ["missing token", {}, 422],
  ["expired token", { expired: true }, 410],
  ["already used token", { claimed: false }, 410],
]) {
  test(`${name} cannot create a session or redirect`, async () => {
    const state = fixture("/dashboard", options);
    const query = name === "missing token" ? "" : "?token=test-token";
    const response = await (await handler)(new Request(`https://0.0.0.0:3000/api/v1/auth/email/verify${query}`));
    assert.equal(response.status, status);
    assert.equal(response.headers.get("location"), null);
    assert.equal(response.headers.get("set-cookie"), null);
    assert.equal(state.sessions.length, 0);
  });
}
