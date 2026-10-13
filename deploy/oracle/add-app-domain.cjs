const fs = require('node:fs');
const dotenv = require('dotenv');
const { patchEnv } = require('../../scripts/configure-enclave.cjs');

function addAppDomain(filename, hostname) {
  hostname = hostname.toLowerCase();
  if (!/^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(hostname)) {
    throw new Error('Provide a DNS hostname without https:// or a path.');
  }
  const original = fs.readFileSync(filename, 'utf8');
  const settings = dotenv.parse(original);
  if (!settings.STUDIO_APP_DOMAIN || !settings.APP_ORIGIN) throw new Error('Configure the primary application hostname first.');
  if (hostname === settings.STUDIO_DOMAIN) throw new Error('The restricted public site cannot also serve the full app.');
  const aliases = new Set((settings.STUDIO_APP_ALIASES || '').split(/\s+/).filter(Boolean));
  const origins = new Set((settings.APP_ADDITIONAL_ORIGINS || '').split(/[\s,]+/).filter(Boolean));
  if (hostname !== settings.STUDIO_APP_DOMAIN) aliases.add(hostname);
  if (`https://${hostname}` !== new URL(settings.APP_ORIGIN).origin) origins.add(`https://${hostname}`);
  if (aliases.has(settings.STUDIO_DOMAIN) || origins.has(`https://${settings.STUDIO_DOMAIN}`)) {
    throw new Error('Remove the restricted public site from full-app aliases and origins.');
  }
  const updated = patchEnv(original, {
    STUDIO_APP_ALIASES: [...aliases].join(' '),
    APP_ADDITIONAL_ORIGINS: [...origins].join(' '),
  });
  if (updated !== original) {
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    fs.writeFileSync(`${filename}.domain-backup-${stamp}`, original, { mode: 0o600, flag: 'wx' });
    fs.writeFileSync(filename, updated);
    fs.chmodSync(filename, 0o600);
  }
  console.log(JSON.stringify({ primaryOrigin: settings.APP_ORIGIN, addedDomain: hostname, aliases: [...aliases] }));
}

if (require.main === module) {
  try { addAppDomain(process.argv[2] || '', process.argv[3] || ''); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
module.exports = { addAppDomain };
