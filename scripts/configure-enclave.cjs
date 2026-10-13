// Configure the app's script and plan-preview clients from existing private P8
// Enclave settings. Credentials stay in dotenv files and are never logged.
const fs = require('node:fs');
const path = require('node:path');
const dotenv = require('dotenv');

function quote(value) {
  const delimiter = ["'", '"', '`'].find(character => !value.includes(character));
  if (!delimiter || /[\r\n]/.test(value)) throw new Error('A configuration value cannot be represented safely in dotenv.');
  return delimiter + value + delimiter;
}
function patchEnv(contents, settings) {
  const newline = contents.includes('\r\n') ? '\r\n' : '\n';
  for (const [name, value] of Object.entries(settings)) {
    const pattern = new RegExp('^' + name + '=[^\\r\\n]*', 'gm');
    const line = name + '=' + quote(value);
    if (pattern.test(contents)) contents = contents.replace(pattern, () => line);
    else contents += (contents.endsWith('\n') ? '' : newline) + line + newline;
  }
  return contents;
}
function configure(files) {
  const existing = files.filter(file => fs.existsSync(file));
  if (!existing.length) throw new Error('No private dotenv files were found.');
  const env = Object.assign({}, ...existing.map(file => dotenv.parse(fs.readFileSync(file))));
  const baseUrl = env.NEXMIND_CREATIVE_BASE_URL?.trim();
  const model = env.NEXMIND_CREATIVE_MODEL?.trim();
  const keyEnv = env.NEXMIND_CREATIVE_API_KEY_ENV?.trim() || 'NEXMIND_API_KEY';
  const key = env[keyEnv]?.trim();
  if (env.NEXMIND_CREATIVE_PROVIDER?.trim() !== 'enclave' || !baseUrl || !model || !key) {
    throw new Error('Set the existing NEXMIND_CREATIVE Enclave provider, URL, model and referenced API key first.');
  }
  if (new URL(baseUrl).protocol !== 'https:') throw new Error('The external Enclave URL must use HTTPS.');
  if (!/^[A-Z][A-Z0-9_]*$/.test(keyEnv)) throw new Error('Invalid credential environment variable name.');
  const settings = {
    [keyEnv]: key,
    STUDIO_SCRIPT_OPENAI_API_URL: baseUrl,
    STUDIO_SCRIPT_OPENAI_API_KEY: key,
    STUDIO_SCRIPT_MODEL: model,
    STUDIO_SCRIPT_TIMEOUT_MS: env.STUDIO_SCRIPT_TIMEOUT_MS || '180000',
    STUDIO_PLAN_PREVIEW_OPENAI_API_URL: baseUrl,
    STUDIO_PLAN_PREVIEW_OPENAI_API_KEY: key,
  };
  for (const prefix of ['NEXMIND_STUDIO_SCRIPT', 'NEXMIND_PLAN_PREVIEW', 'NEXMIND_STUDIO_PLAN_PREVIEW']) {
    Object.assign(settings, {
      [prefix + '_PROVIDER']: 'enclave', [prefix + '_MODEL']: model,
      [prefix + '_BASE_URL']: baseUrl, [prefix + '_API_KEY_ENV']: keyEnv,
      [prefix + '_API_MODE']: env.NEXMIND_CREATIVE_API_MODE || 'chat_completions_prompt_json',
    });
  }
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  for (const file of existing) {
    const original = fs.readFileSync(file, 'utf8');
    const updated = patchEnv(original, settings);
    if (original === updated) continue;
    const backup = file + '.enclave-backup-' + stamp;
    fs.writeFileSync(backup, original, { mode: 0o600, flag: 'wx' });
    fs.writeFileSync(file, updated);
    fs.chmodSync(file, 0o600);
  }
  console.log(JSON.stringify({ provider: 'enclave', baseUrl, model, files: existing.map(file => path.basename(file)), credential: 'present' }));
}
if (require.main === module) {
  try { configure(process.argv.length > 2 ? process.argv.slice(2) : ['.env', '.env.local']); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { patchEnv, configure };
