/** Load the vendored browser registries into Node for planning and tests. */
const fs = require('fs');
const path = require('path');

const VENDOR = path.join(__dirname, '..', 'vendor', 'paper-motion', 'runtime');

function loadGlobal(file, key) {
  const window = {};
  new Function('window', fs.readFileSync(path.join(VENDOR, file), 'utf8'))(window);
  return window[key] || [];
}

function registries() {
  return {
    typography: loadGlobal('typography-registry.js', 'NEX_TYPOGRAPHY'),
    icons: loadGlobal('icon-registry.js', 'NEX_ICONS'),
    media: loadGlobal('media-container-registry.js', 'NEX_MEDIA_CONTAINERS'),
    motion: loadGlobal('motion-registry.js', 'NEX_MOTIONS')
  };
}

module.exports = { registries, loadGlobal };
