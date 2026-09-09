// assets/js/core/contentLoader.js
// structure.json からページのパスを取得し、コンテンツを fetch して .article-body に挿入
import { u } from './basePath.js';
import { log } from './logger.js';

function renderError(el, message) {
  el.innerHTML = `<p style="color:#c00;white-space:pre-wrap">${message}</p>`;
}

function renderGlobalError(message) {
  const box = document.createElement('div');
  box.style.cssText = 'padding:12px;margin:12px;border:1px solid #c00;color:#c00;background:#fff;white-space:pre-wrap;';
  box.textContent = message;
  if (document.body) {
    document.body.prepend(box);
  }
}

function extractContentFragment(text) {
  const raw = String(text ?? '');
  if (!/<!doctype|<html|<head|<body/i.test(raw)) {
    return raw;
  }

  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(raw, 'text/html');

    const articleBody = doc.querySelector('.article-body');
    if (articleBody && typeof articleBody.innerHTML === 'string' && articleBody.innerHTML !== '') {
      return articleBody.innerHTML;
    }

    if (doc.body && typeof doc.body.innerHTML === 'string' && doc.body.innerHTML !== '') {
      return doc.body.innerHTML;
    }

    return raw;
  } catch (_e) {
    return raw;
  }
}

/**
 * structure.json からスラグに対応するページパスを取得
 */
async function resolveContentUrl(slug) {
  try {
    const structureUrl = u('data/structure.json');
    const res = await fetch(structureUrl, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      const pages = data.pages || [];
      const page = pages.find(p => p.slug === slug);
      if (page && page.path) {
        // page.path は "/index.html" や "/contents/shika.html" のような形式
        return u(page.path.replace(/^\//, ''));
      }
    }
  } catch (_e) {
    // structure.json の読み込みに失敗した場合はフォールバック
  }
  // フォールバック: contents/{slug}.html
  return u(`contents/${slug}.html`);
}

export async function initContentLoader() {
  const el = document.querySelector('.article-body[data-yacho-content]');
  if (!el) {
    // 静的ページ（data-yacho-static）では対象要素が無い。正常。
    console.log('[contentLoader] .article-body[data-yacho-content] not found – static page, skipping.');
    return;
  }

  const slug = el.getAttribute('data-yacho-content');
  if (!slug) {
    const message = 'data-yacho-content が見つかりません';
    log('error', 'content_slug_missing', { message });
    renderError(el, message);
    return;
  }

  const url = await resolveContentUrl(slug);

  fetch(url, { cache: 'no-store' })
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res.text();
    })
    .then((text) => {
      el.innerHTML = extractContentFragment(text);
      log('info', 'content_loaded', { slug, url, format: 'html' });
    })
    .catch((err) => {
      const message = `コンテンツの読み込みに失敗しました\nslug: ${slug}\nurl: ${url}\nerror: ${String(err)}`;
      log('error', 'content_load_failed', { slug, url, error: String(err) });
      renderError(el, message);
    });
}
