(() => {
  const activeFindingIds = new Set();
  const cards = Array.from(document.querySelectorAll('.record-card'));
  const filterButtons = Array.from(document.querySelectorAll('.filter-btn[data-finding-id]'));
  const summaryRows = Array.from(document.querySelectorAll('.summary tr[data-finding-id]'));
  const visibleCountEl = document.getElementById('visible-count');
  const showAllBtn = document.getElementById('show-all-btn');

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
      const findingId = card.dataset.findingId;
      const visible = activeFindingIds.size === 0 || activeFindingIds.has(findingId);
      card.classList.toggle('hidden', !visible);
      if (visible) visibleCount += 1;
    }

    if (visibleCountEl) {
      visibleCountEl.textContent = String(visibleCount);
    }

    for (const button of filterButtons) {
      button.classList.toggle('active', activeFindingIds.has(button.dataset.findingId));
    }
    for (const row of summaryRows) {
      row.classList.toggle('active', activeFindingIds.has(row.dataset.findingId));
    }
  }

  function toggleFinding(findingId) {
    if (activeFindingIds.has(findingId)) {
      activeFindingIds.delete(findingId);
    } else {
      activeFindingIds.add(findingId);
    }
    updateVisibility();
  }

  for (const button of filterButtons) {
    button.addEventListener('click', () => toggleFinding(button.dataset.findingId));
  }
  for (const row of summaryRows) {
    row.addEventListener('click', () => toggleFinding(row.dataset.findingId));
  }

  if (showAllBtn) {
    showAllBtn.addEventListener('click', () => {
      activeFindingIds.clear();
      updateVisibility();
    });
  }

  applyNativeScaleTweaks();
  updateVisibility();
})();
