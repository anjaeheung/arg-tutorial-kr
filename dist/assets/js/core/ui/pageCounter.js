export function initPageCounter(provider) {
  const elCurrent = document.getElementById('page-current');
  const elTotal = document.getElementById('page-total');
  if (!elCurrent || !elTotal || !provider || typeof provider.page !== 'function') return;

  const slug = resolveSlug();

  provider.page(slug)
    .then((data) => {
      elCurrent.textContent = data?.page_no ?? '-';
      elTotal.textContent = data?.total ?? '-';
    })
    .catch((e) => {
      console.error('[page-counter]', e);
      elCurrent.textContent = '-';
      elTotal.textContent = '-';
    });
}

export function resolveSlug() {
  let slug = document.body.getAttribute('data-page-slug');
  if (slug) return slug.trim();

  slug = location.pathname
    .split('/')
    .pop()
    .replace('.html', '')
    .replace('.php', '');

  if (!slug) slug = 'index';
  return slug;
}
