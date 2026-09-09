// assets/js/core/basePath.js
// ベースパス検出: window.YACHO_BASE 優先、なければ script src から逆算

let base = '/';
if (
  typeof window !== 'undefined' &&
  typeof window.YACHO_BASE === 'string' &&
  !window.YACHO_BASE.includes('{{')
) {
  base = window.YACHO_BASE || './';
} else {
  const script = document.querySelector('script[src*="core/index.js"]');
  if (script) {
    const src = script.src || script.getAttribute('src') || '';
    const idx = src.indexOf('assets/js/core/index.js');
    if (idx >= 0) {
      base = src.substring(0, idx);
      if (typeof window !== 'undefined' && base.startsWith(window.location.origin)) {
        base = base.slice(window.location.origin.length);
      }
    }
  }
}

if ((base === '/' || base === '') && typeof window !== 'undefined') {
  const path = window.location.pathname || '/';
  const m = path.match(/^(.*?\/)(?:contents\/[^/]+\.(?:html|php)|index\.(?:html|php))$/i);
  if (m && m[1]) {
    base = m[1];
  } else if (!path.endsWith('/')) {
    base = path.replace(/[^/]+$/, '');
  } else {
    base = path;
  }
}

if (!base.endsWith('/')) base += '/';

function u(path) {
  const p = String(path || '').replace(/^\/+/, '');
  return `${base}${p}`;
}

export const BASE = base;
export { u };
