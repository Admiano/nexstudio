const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const dotenv = require('dotenv');

function configure(domain, root = path.resolve(__dirname, '../..'), appDomain) {
  if (!/^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(domain)) {
    throw new Error('Provide the public DNS hostname, without https:// or a path.');
  }
  const folder = path.join(root, 'deploy', 'oracle');
  const filename = path.join(folder, '.env');
  const read = file => fs.existsSync(file) ? dotenv.parse(fs.readFileSync(file)) : {};
  const local = {...read(path.join(root, '.env')), ...read(path.join(root, '.env.local'))};
  const existing = read(filename);
  const values = {...read(path.join(folder, '.env.example')), ...existing};
  values.STUDIO_DOMAIN = domain.toLowerCase();
  values.STUDIO_APP_DOMAIN = (appDomain || existing.STUDIO_APP_DOMAIN || local.STUDIO_APP_DOMAIN || values.STUDIO_APP_DOMAIN || '').toLowerCase();
  if (!/^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(values.STUDIO_APP_DOMAIN)
      || values.STUDIO_APP_DOMAIN === values.STUDIO_DOMAIN || values.STUDIO_APP_DOMAIN === 'app.example.com') {
    throw new Error('Provide the separate full application hostname as the second CLI argument or STUDIO_APP_DOMAIN.');
  }
  const previousDomains = [...(existing.STUDIO_ALIASES || '').split(/\s+/), existing.STUDIO_DOMAIN || ''];
  values.STUDIO_ALIASES = [...new Set(previousDomains.filter(previous => previous && previous !== values.STUDIO_DOMAIN))].join(' ');
  values.APP_ORIGIN = `https://${values.STUDIO_APP_DOMAIN}`;
  values.POSTGRES_PASSWORD ||= crypto.randomBytes(32).toString('hex');
  values.LOCAL_AI_API_KEY ||= crypto.randomBytes(32).toString('hex');
  values.STUDIO_TRUST_SECRET ||= (local.STUDIO_TRUST_SECRET?.length >= 32 ? local.STUDIO_TRUST_SECRET : crypto.randomBytes(32).toString('hex'));
  for (const name of ['RESEND_API_KEY', 'EMAIL_FROM']) values[name] ||= local[name] || '';
  for (const name of ['STUDIO_SCRIPT_OPENAI_API_URL', 'STUDIO_SCRIPT_OPENAI_API_KEY',
    'STUDIO_SCRIPT_MODEL', 'STUDIO_SCRIPT_TIMEOUT_MS',
    'STUDIO_PLAN_PREVIEW_OPENAI_API_URL', 'STUDIO_PLAN_PREVIEW_OPENAI_API_KEY']) {
    if (local[name]?.trim() && !existing[name]?.trim()) values[name] = local[name];
  }
  // Preserve the configured creative/review routes and their referenced keys.
  for (const [name, value] of Object.entries(local)) {
    if (!name.startsWith('NEXMIND_') || !value.trim()) continue;
    values[name] ||= value;
    if (name.endsWith('_API_KEY_ENV') && /^[A-Z][A-Z0-9_]*$/.test(value) && local[value]) {
      values[value] ||= local[value];
    }
  }
  if (!/^[a-f0-9]{32,}$/i.test(values.POSTGRES_PASSWORD)) throw new Error('POSTGRES_PASSWORD must be at least 32 hex characters for this database URL.');
  if (values.STUDIO_TRUST_SECRET.length < 32 || values.LOCAL_AI_API_KEY.length < 32) throw new Error('Trust and local AI secrets must have at least 32 characters.');
  // dotenv strips surrounding quotes but does not decode JSON quote escapes.
  // Choose a delimiter absent from the value to preserve registry JSON exactly.
  const data = Object.entries(values).map(([name, value]) => {
    const delimiter = ["'", '"', '`'].find(quote => !value.includes(quote));
    if (!delimiter) throw new Error(`Configure ${name} manually: it contains every dotenv quoting delimiter.`);
    return `${name}=${delimiter}${value}${delimiter}`;
  }).join('\n') + '\n';
  fs.writeFileSync(filename, data, {mode: 0o600});
  fs.chmodSync(filename, 0o600);
  console.log('Private Oracle configuration saved. Existing secrets were retained.');
  console.log(`Public origin: ${values.APP_ORIGIN}`);
  console.log(`Sign-in email configuration: ${values.RESEND_API_KEY && values.EMAIL_FROM ? 'present' : 'missing RESEND_API_KEY or EMAIL_FROM'}`);
  return filename;
}

if (require.main === module) {
  try { configure(process.argv[2] || '', undefined, process.argv[3]); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = {configure};
