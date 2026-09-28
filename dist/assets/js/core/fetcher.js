import { u, BASE } from './basePath.js';
import { log } from './logger.js';
import { getRequestId } from './requestId.js';

export async function fetchJson(path, options = {}) {
  const rid = getRequestId();
  const url = /^(https?:)?\/\//i.test(path) ? path : u(path);
  const headers = new Headers(options.headers || {});
  headers.set('X-Request-Id', rid);
  headers.set('Accept', 'application/json');

  let res;
  try {
    res = await fetch(url, {
      ...options,
      headers,
      cache: options.cache || 'no-store',
    });
  } catch (error) {
    log('error', 'fetch_failed', { rid, path, url, base: BASE, error: String(error) });
    throw error;
  }

  if (!res.ok) {
    log('error', 'http_error', { rid, path, url, base: BASE, status: res.status });
    throw new Error(`${path} (${res.status})`);
  }

  try {
    return await res.json();
  } catch (error) {
    log('error', 'json_parse_failed', { rid, path, url, base: BASE, error: String(error) });
    throw error;
  }
}
