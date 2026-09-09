const KEY = 'yacho.request_id';

function createRid() {
  const t = Date.now().toString(36);
  const r = Math.random().toString(36).slice(2, 10);
  return `${t}-${r}`;
}

export function getRequestId() {
  try {
    const current = sessionStorage.getItem(KEY);
    if (current) return current;
    const rid = createRid();
    sessionStorage.setItem(KEY, rid);
    return rid;
  } catch {
    return createRid();
  }
}
