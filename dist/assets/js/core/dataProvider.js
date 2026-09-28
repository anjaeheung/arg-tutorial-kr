import { u } from './basePath.js';
import { fetchJson } from './fetcher.js';

let pagesPromise = null;
let metaPromise = null;

function sanitize(text) {
  return String(text || '')
    .trim()
    .replace(/[\x00-\x1F\x7F\u2028\u2029]/g, '')
    .replace(/\u3000/g, ' ');
}

function normalizePath(path) {
  const p = String(path || '').trim();
  if (!p) return u('index.html');
  if (/^(https?:)?\/\//i.test(p)) return p;
  if (p.startsWith('/')) return u(p.replace(/^\/+/, ''));
  return u(p.replace(/^\.\/+/, ''));
}

async function loadPages() {
  if (!pagesPromise) {
    pagesPromise = fetchJson('data/structure.json')
      .then((data) => (Array.isArray(data?.pages) ? data.pages : []))
      .then((pages) => pages.filter((p) => (p?.kind ?? 'page') !== 'include'))
      .catch(() => []);
  }
  return pagesPromise;
}

async function loadMeta() {
  if (!metaPromise) {
    metaPromise = fetchJson('data/meta.json').catch(() => null);
  }
  return metaPromise;
}

/**
 * 個別ファイルから検索結果を取得するヘルパー
 */
function parseResults(fileData, defaultTitle) {
  const seen = new Set();
  const results = [];

  // 1語ヒントファイル形式: { results: [...], hint: "needMore" }
  if (Array.isArray(fileData?.results)) {
    for (const item of fileData.results) {
      const path = normalizePath(item?.path);
      if (seen.has(path)) continue;
      seen.add(path);
      results.push({ title: item?.title || defaultTitle, path });
    }
    return { results, hint: fileData.hint || null };
  }

  // 2語ペアファイル形式: [{ title, path }, ...]
  if (Array.isArray(fileData)) {
    for (const item of fileData) {
      const path = normalizePath(item?.path);
      if (seen.has(path)) continue;
      seen.add(path);
      results.push({ title: item?.title || defaultTitle, path });
    }
    return { results, hint: null };
  }

  return { results: [], hint: null };
}

export function createProvider() {
  const provider = {
    async meta() {
      const meta = await loadMeta();
      if (meta && Number.isFinite(Number(meta.total))) {
        return { total: Number(meta.total) };
      }
      const pages = await loadPages();
      return { total: pages.length };
    },

    async page(slug) {
      const pages = await loadPages();
      const targetSlug = String(slug || 'index').trim();
      const found = pages.find((p, i) => {
        const pSlug = String(p?.slug || p?.id || '').trim();
        if (pSlug === targetSlug) return true;
        if (targetSlug === 'index' && i === 0) return true;
        return false;
      });
      const meta = await provider.meta();

      if (!found) {
        return { page_no: null, total: meta.total || pages.length };
      }

      const pageNo = Number.isFinite(Number(found.page_no))
        ? Number(found.page_no)
        : (pages.indexOf(found) + 1);

      return { page_no: pageNo, total: meta.total || pages.length };
    },

    async search(rawInput) {
      const input = sanitize(rawInput);
      if (!input) return { results: [], hint: null };

      const tokens = input.split(/\s+/).filter(Boolean);
      if (tokens.length === 0) return { results: [], hint: null };

      // 1語検索: data/search/{keyword}.json を fetch
      if (tokens.length === 1) {
        try {
          const fileData = await fetchJson('data/search/' + tokens[0] + '.json');
          if (fileData) return parseResults(fileData, tokens[0]);
        } catch { /* ファイルがなければ結果なし */ }
        return { results: [], hint: null };
      }

      // 2語検索: ソートして結合 → data/search/{combined}.json を fetch
      if (tokens.length >= 2) {
        const sorted = [tokens[0], tokens[1]].sort();
        const combined = sorted.join('');
        try {
          const fileData = await fetchJson('data/search/' + combined + '.json');
          if (fileData) {
            const result = parseResults(fileData, `${tokens[0]} ${tokens[1]}`);
            if (result.results.length > 0) return result;
          }
        } catch { /* ファイルがなければ部分一致チェック */ }

        // 部分一致ヒント: 各語で個別ファイルを確認
        let hasPartial = false;
        for (const token of [tokens[0], tokens[1]]) {
          try {
            const fileData = await fetchJson('data/search/' + token + '.json');
            if (fileData) {
              const r = parseResults(fileData, token);
              if (r.results.length > 0 || r.hint) {
                hasPartial = true;
                break;
              }
            }
          } catch { /* ignore */ }
        }

        return { results: [], hint: hasPartial ? 'partial' : null };
      }

      return { results: [], hint: null };
    },
  };

  return provider;
}
