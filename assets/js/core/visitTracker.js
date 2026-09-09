// assets/js/core/visitTracker.js
// 閲覧履歴コア — localStorage 永続化 + structure.json ベースのスラグ管理

import { fetchJson } from './fetcher.js';
import { BASE } from './basePath.js';

const DEBOUNCE_MS = 1000;

let state = null;       // { history: number[], visitedSet: Set<number> }
let slugToIndex = null;  // { [slug]: index }
let pagesList = null;    // structure.pages (include 除外済み)
let saveTimer = null;
let initialized = false;
let initPromise = null;

// ── ストレージキー生成 ──────────────────────────

function getStorageKey() {
  const origin = (typeof window !== 'undefined' && window.location.origin) || '';
  const siteId = simpleHash(origin || '/');
  return `yacho.visit.${siteId}`;
}

function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash).toString(36);
}

// ── 内部ユーティリティ ──────────────────────────

function createEmptyState() {
  return {
    history: [],
    visitedSet: new Set(),
  };
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (!raw) return null;
    const data = JSON.parse(raw);
    const history = Array.isArray(data.history) ? data.history : [];
    return {
      history,
      visitedSet: new Set(history),
    };
  } catch {
    return null;
  }
}

function saveToStorage() {
  try {
    const data = {
      history: state.history,
      updatedAt: new Date().toISOString(),
    };
    localStorage.setItem(getStorageKey(), JSON.stringify(data));
  } catch { /* ignore — private browsing etc. */ }
}

function debounceSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(saveToStorage, DEBOUNCE_MS);
}

async function loadStructure() {
  try {
    const data = await fetchJson('data/structure.json');
    const pages = Array.isArray(data?.pages) ? data.pages : [];
    return pages.filter((p) => (p?.kind ?? 'page') !== 'include');
  } catch {
    return [];
  }
}

function buildSlugIndex(pages) {
  const map = {};
  pages.forEach((p, i) => {
    const slug = String(p?.slug || p?.id || '').trim();
    if (slug) map[slug] = i;
  });
  return map;
}

// ── 初期化 ──────────────────────────────────

async function doInit() {
  pagesList = await loadStructure();
  slugToIndex = buildSlugIndex(pagesList);
  state = loadFromStorage() || createEmptyState();
  initialized = true;
}

/**
 * 初期化（ページ読み込み直後に呼ぶ）。
 * 現在表示中のページを自動で閲覧済みに記録する。
 */
export function initVisitTracker() {
  if (initPromise) return initPromise;
  initPromise = doInit().then(() => {
    // 現在のページを閲覧済みに記録
    const slug = resolveCurrentSlug();
    if (slug && slugToIndex && slug in slugToIndex) {
      markVisited(slugToIndex[slug]);
    }
  });
  return initPromise;
}

/** 初期化完了まで待機 */
export function whenReady() {
  return initPromise || Promise.resolve();
}

// ── 現在ページのスラグ解決 ─────────────────────

function resolveCurrentSlug() {
  // data-page-slug 属性があればそちらを優先
  const bodySlug = document.body.getAttribute('data-page-slug');
  if (bodySlug) return bodySlug.trim();

  let slug = location.pathname
    .split('/')
    .pop()
    .replace('.html', '')
    .replace('.php', '');

  if (!slug) slug = 'index';
  return slug;
}

// ── 閲覧記録操作 ────────────────────────────

function markVisited(pageIndex) {
  if (!state || typeof pageIndex !== 'number') return;
  if (state.visitedSet.has(pageIndex)) return;
  state.visitedSet.add(pageIndex);
  state.history.push(pageIndex);
  saveToStorage();
}

/** 閲覧進捗情報を取得 */
export function getProgress() {
  if (!pagesList || !state) {
    return { visited: 0, total: 0, percent: 0, pages: [] };
  }

  const total = pagesList.length;
  const visited = state.visitedSet.size;
  const percent = total > 0 ? Math.round((visited / total) * 100) : 0;

  const pages = pagesList.map((p, i) => ({
    slug: String(p?.slug || p?.id || '').trim(),
    title: String(p?.title || '').trim(),
    page_no: p?.page_no ?? (i + 1),
    path: p?.path || '',
    visited: state.visitedSet.has(i),
  }));

  return { visited, total, percent, pages };
}

/** 閲覧済みページ数を返す */
export function getVisitedCount() {
  if (!state) return 0;
  return state.visitedSet.size;
}

/** 総ページ数を返す */
export function getTotalCount() {
  if (!pagesList) return 0;
  return pagesList.length;
}

/** 履歴をクリア */
export function clearHistory() {
  state = createEmptyState();
  saveToStorage();
}
