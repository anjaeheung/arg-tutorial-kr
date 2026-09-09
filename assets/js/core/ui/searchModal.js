export function initSearchModal(provider) {
  const input = document.querySelector('#searchInput');
  const button = document.querySelector('#searchBtn');

  if (!input || !button || !provider || typeof provider.search !== 'function') return;

  // PHPテンプレート: ボタンがform内にある場合はサーバーサイド検索に委ねる
  if (button.closest('form')) return;

  const modal = createModal();
  document.body.appendChild(modal.root);

  const { root, body, close, overlay } = modal;

  const open = () => root.classList.remove('hidden');
  const hide = () => {
    root.classList.add('hidden');
    body.innerHTML = '';
  };

  close.addEventListener('click', hide);
  overlay.addEventListener('click', hide);

  const performSearch = async () => {
    const { results, hint } = await provider.search(input.value);
    renderSearchResults(body, results, hint);
    open();
  };

  button.addEventListener('click', performSearch);

  // Enterキーでの検索もサポート
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      performSearch();
    }
  });
}

function createModal() {
  const root = document.createElement('div');
  root.className = 'search-modal hidden';

  const overlay = document.createElement('div');
  overlay.className = 'search-modal__overlay';

  const content = document.createElement('div');
  content.className = 'search-modal__content';

  const heading = document.createElement('h2');
  heading.textContent = '検索結果';

  const body = document.createElement('div');
  body.className = 'search-modal__body';

  const actions = document.createElement('div');
  actions.className = 'search-modal__actions';

  const close = document.createElement('button');
  close.type = 'button';
  close.textContent = '閉じる';

  actions.appendChild(close);
  content.append(heading, body, actions);
  root.append(overlay, content);

  return { root, overlay, body, close };
}

const HINT_MESSAGES = {
  needMore: 'キーワードはまだ不完全です',
  partial: 'キーワードの一部は正しいようです'
};

function renderSearchResults(body, results, hint) {
  body.innerHTML = '';

  const ul = document.createElement('ul');
  ul.className = 'search-result-list';

  if (!results || results.length === 0) {
    const li = document.createElement('li');
    li.textContent = '該当する記録は見つかりませんでした。';
    ul.appendChild(li);
  } else {
    results.forEach(item => {
      const li = document.createElement('li');

      const a = document.createElement('a');
      a.href = item.path;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = item.title || '無題の記録';

      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  body.appendChild(ul);

  if (hint && HINT_MESSAGES[hint]) {
    const hintEl = document.createElement('p');
    hintEl.className = 'search-hint';
    hintEl.textContent = HINT_MESSAGES[hint];
    body.appendChild(hintEl);
  }
}
