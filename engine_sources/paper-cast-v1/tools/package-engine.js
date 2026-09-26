#!/usr/bin/env node
/**
 * Packages Paper Cast as an engine archive, the way the other engines in
 * `engine_sources/` ship: one zip holding the whole runnable package plus the
 * provenance the studio reads before it will execute anything.
 *
 *   node tools/package-engine.js [outDir]     # default ../ (engine_sources)
 *
 * The suite runs first: an archive is a claim that this version works, so a
 * failing test refuses to package rather than shipping a broken engine.
 */
const { execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const NAME = 'PAPER_CAST_V1_ENGINE_SOURCE';
const PKG = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));

/** Everything a consumer needs; nothing a consumer should not receive. */
const INCLUDE = ['runtime', 'manifests', 'paperbook', 'tools', 'cast-explorer.html', 'package.json', 'README.md', 'INSTALL.md', 'CAST_API.md'];
const SKIP = new Set(['.review', 'node_modules', 'proofs', '.DS_Store']);

function walk(dir, base) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    const rel = path.posix.join(base, entry.name);
    if (entry.isDirectory()) out.push(...walk(full, rel));
    else out.push({ full, rel });
  }
  return out;
}

function collect() {
  const files = [];
  for (const item of INCLUDE) {
    const full = path.join(ROOT, item);
    if (!fs.existsSync(full)) continue;
    if (fs.statSync(full).isDirectory()) files.push(...walk(full, item));
    else files.push({ full, rel: item });
  }
  return files.sort((a, b) => a.rel.localeCompare(b.rel));
}

const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

function runTests() {
  const output = execFileSync(process.execPath, [path.join(ROOT, 'tools', 'test-paper-cast.js')], { encoding: 'utf8' });
  const line = output.trim().split('\n').pop();
  const m = /^(\d+)\/(\d+) passed$/.exec(line.trim());
  if (!m || m[1] !== m[2]) throw new Error(`refusing to package: ${line}`);
  return { passed: Number(m[1]), total: Number(m[2]) };
}

function main() {
  const outDir = path.resolve(process.argv[2] || path.join(ROOT, '..'));
  const tests = runTests();
  const files = collect();
  const stamp = new Date().toISOString();

  const staging = fs.mkdtempSync(path.join(require('os').tmpdir(), 'paper-cast-pkg-'));
  const root = path.join(staging, NAME);
  for (const f of files) {
    const dest = path.join(root, f.rel);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(f.full, dest);
  }

  const provenance = {
    schema: 'NexStudioEngineSourceProvenanceV1',
    engine: 'PAPER_CAST_V1',
    package: PKG.name,
    version: PKG.version,
    dialect: 'paper-motion (paperbook)',
    role: 'EXECUTION_ONLY',
    packagedAt: stamp,
    entrypoint: 'runtime/paper-cast.js',
    runtimeDependencies: [],
    capabilities: [
      'parametric bodies from infant to senior, with build, stature and mass as separate axes',
      'contact solving: hands, feet and props reached by goal rather than by pose name',
      'two-body relations: carry on back, supported walk, grip prop',
      'wardrobe: garment silhouettes, trim, overlays, headwear, hair and beards',
      'props: grips and drawing from one definition, drawn from the solved hands',
      'role vocabulary: a script phrase resolves to body, outfit, prop and hold',
      'paperbook figure renderer: flat gouache shapes, toned paper, depth-sorted relations'
    ],
    truthBoundary: 'This package draws characters. It does not choose story, art direction or page layout, and it does not parse arbitrary prose: unrecognised role words are reported as recognised=false rather than guessed.',
    verification: { suite: 'tools/test-paper-cast.js', passed: tests.passed, total: tests.total },
    files: files.map((f) => ({ path: f.rel, bytes: fs.statSync(f.full).size, sha256: sha(f.full) }))
  };
  fs.writeFileSync(path.join(root, 'PAPER_CAST_PROVENANCE.json'), `${JSON.stringify(provenance, null, 2)}\n`);

  const zipPath = path.join(outDir, `${NAME}.zip`);
  fs.mkdirSync(outDir, { recursive: true });
  fs.rmSync(zipPath, { force: true });
  // -X drops platform extras so the same source packages to the same archive.
  execFileSync('zip', ['-q', '-r', '-X', zipPath, NAME], { cwd: staging });
  fs.rmSync(staging, { recursive: true, force: true });

  const size = fs.statSync(zipPath).size;
  console.log(`${tests.passed}/${tests.total} checks passed`);
  console.log(`${files.length + 1} files -> ${path.relative(process.cwd(), zipPath)} (${(size / 1024).toFixed(0)} kB)`);
  console.log(`sha256 ${sha(zipPath)}`);
}

main();
