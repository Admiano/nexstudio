// Load the local configuration, probe real routes, and store a fresh build-bound attestation.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
process.chdir(root);
require('dotenv').config({ path: path.join(root, '.env'), quiet: true, override: true });
const python = process.env.STUDIO_NEXMIND_P8_PYTHON_BIN || 'python';
const hashRun = spawnSync(python, ['compute-nexmind-p8-build-hash.py'], { encoding: 'utf8' });
if (hashRun.status !== 0) throw new Error(hashRun.stderr || 'Build hash failed');
const buildHash = hashRun.stdout.split(/\r?\n/)[0];
if (!/^[a-f0-9]{64}$/.test(buildHash)) throw new Error('Invalid build hash');
function set(name, value) {
  let contents = fs.readFileSync('.env', 'utf8');
  const newline = contents.includes('\r\n') ? '\r\n' : '\n';
  const pattern = new RegExp('^' + name + '=.*$', 'm');
  contents = pattern.test(contents) ? contents.replace(pattern, () => name + '=' + value) : contents + newline + name + '=' + value + newline;
  fs.writeFileSync('.env', contents);
}
set('NEXMIND_P8_BUILD_HASH', buildHash);
set('NEXMIND_RUNTIME_BOOT_ATTESTATION_JSON', '');
process.env.NEXMIND_P8_BUILD_HASH = buildHash;
console.log('Running configured NexMind live boot probes with synthetic media.');
const run = spawnSync(python, ['scripts/nexmind-runtime-boot-probe.py'], {
  encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1' }, timeout: 900000, maxBuffer: 2 * 1024 * 1024,
});
if (run.error) throw run.error;
if (run.stderr) process.stderr.write(run.stderr);
const result = JSON.parse(run.stdout.trim());
const output = path.resolve(root, process.argv[2] || 'reports/nexmind-runtime-boot-probe.json');
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(result, null, 2));
set('NEXMIND_RUNTIME_BOOT_ATTESTATION_JSON', JSON.stringify(result));
console.log(JSON.stringify(result, null, 2));
process.exit(run.status || 0);
