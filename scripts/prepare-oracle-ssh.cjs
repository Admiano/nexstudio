const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const key = path.join(root, 'certs', 'oracle-nexstudio.key');
fs.mkdirSync(path.dirname(key), {recursive:true});
if (fs.existsSync(key) || fs.existsSync(`${key}.pub`)) {
  if (!fs.existsSync(key) || !fs.existsSync(`${key}.pub`)) throw new Error('Existing key pair is incomplete; refusing to overwrite it.');
} else {
  const result = spawnSync('ssh-keygen', ['-t', 'ed25519', '-f', key, '-N', '', '-C', 'nexstudio-oracle'], {encoding:'utf8', windowsHide:true});
  if (result.error || result.status !== 0) throw new Error(result.error?.message || 'SSH key generation failed.');
}
if (process.platform !== 'win32') fs.chmodSync(key, 0o600);
const fingerprint = spawnSync('ssh-keygen', ['-lf', `${key}.pub`], {encoding:'utf8', windowsHide:true});
if (fingerprint.status !== 0) throw new Error('SSH public key verification failed.');
console.log(`Upload this PUBLIC key to Oracle: ${key}.pub`);
console.log(`Keep this PRIVATE key on your PC: ${key}`);
console.log(fingerprint.stdout.trim());
