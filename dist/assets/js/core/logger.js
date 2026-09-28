const LOG_KEY = 'yacho.logs';
const MAX_LOGS = 300;

function readLogs() {
  try {
    const raw = localStorage.getItem(LOG_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeLogs(items) {
  try {
    localStorage.setItem(LOG_KEY, JSON.stringify(items.slice(-MAX_LOGS)));
  } catch {
    // ignore quota/storage errors
  }
}

export function log(level, message, context = {}) {
  const lv = String(level || 'info').toLowerCase();
  const entry = {
    ts: new Date().toISOString(),
    level: lv,
    message: String(message || ''),
    context: {
      rid: context.rid || null,
      yachoBase: window.YACHO_BASE || null,
      ...context,
    },
  };

  const logs = readLogs();
  logs.push(entry);
  writeLogs(logs);

  const fn = lv === 'error' ? console.error : (lv === 'warn' ? console.warn : console.log);
  fn('[yacho]', entry.message, entry.context);
}

export function getLogs() {
  return readLogs();
}
