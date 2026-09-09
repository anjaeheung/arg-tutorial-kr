import { createProvider } from './dataProvider.js';
import { initContentLoader } from './contentLoader.js';
import { initSearchModal } from './ui/searchModal.js';
import { initPageCounter } from './ui/pageCounter.js';
import { initVisitTracker } from './visitTracker.js';

const provider = createProvider();

document.addEventListener('DOMContentLoaded', () => {
  initContentLoader();
  initSearchModal(provider);
  initPageCounter(provider);
  initVisitTracker();
});

console.log('[yacho] initialized');
