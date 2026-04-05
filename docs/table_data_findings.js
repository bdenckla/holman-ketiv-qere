(() => {
  const activeFilterIds = new Set();
  const cards = Array.from(document.querySelectorAll('.record-card'));
  const filterButtons = Array.from(document.querySelectorAll('.filter-btn[data-filter-id]'));
  const summaryRows = Array.from(document.querySelectorAll('.summary tr[data-filter-id]'));
  const visibleCountEl = document.getElementById('visible-count');
  const showAllBtn = document.getElementById('show-all-btn');

  function cardFilterIds(card) {
    const raw = card.dataset.filterIds || card.dataset.findingId || '';
    return raw.split(/\s+/).filter(Boolean);
  }

  function applyNativeScaleTweaks() {
    const images = Array.from(document.querySelectorAll('img.image-thumb[data-native-scale]'));

    for (const image of images) {
      const scale = Number(image.dataset.nativeScale);
      if (!Number.isFinite(scale) || scale <= 0) {
        continue;
      }

      const applyScale = () => {
        if (!image.naturalWidth) {
          return;
        }
        const widthPx = Math.max(1, Math.round(image.naturalWidth * scale));
        image.style.width = `${widthPx}px`;
      };

      if (image.complete) {
        applyScale();
      } else {
        image.addEventListener('load', applyScale, { once: true });
      }
    }
  }

  function updateVisibility() {
    let visibleCount = 0;
    for (const card of cards) {
      const filterIds = cardFilterIds(card);
      const visible = activeFilterIds.size === 0 || filterIds.some((id) => activeFilterIds.has(id));
      card.classList.toggle('hidden', !visible);
      if (visible) visibleCount += 1;
    }

    if (visibleCountEl) {
      visibleCountEl.textContent = String(visibleCount);
    }

    for (const button of filterButtons) {
      button.classList.toggle('active', activeFilterIds.has(button.dataset.filterId));
    }
    for (const row of summaryRows) {
      row.classList.toggle('active', activeFilterIds.has(row.dataset.filterId));
    }
  }

  function toggleFilter(filterId) {
    if (activeFilterIds.has(filterId)) {
      activeFilterIds.delete(filterId);
    } else {
      activeFilterIds.add(filterId);
    }
    updateVisibility();
  }

  for (const button of filterButtons) {
    button.addEventListener('click', () => toggleFilter(button.dataset.filterId));
  }
  for (const row of summaryRows) {
    row.addEventListener('click', () => toggleFilter(row.dataset.filterId));
  }

  if (showAllBtn) {
    showAllBtn.addEventListener('click', () => {
      activeFilterIds.clear();
      updateVisibility();
    });
  }

  applyNativeScaleTweaks();
  updateVisibility();
})();
