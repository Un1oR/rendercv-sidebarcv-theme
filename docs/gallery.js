for (const sample of document.querySelectorAll('.sample[data-source]')) {
  const preview = sample.querySelector('.paper');
  const image = preview.querySelector('img');
  const controls = sample.querySelector('.sample-pages');
  const buttons = controls.querySelectorAll('button');
  const status = controls.querySelector('.sample-page-status');
  controls.hidden = false;

  controls.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-page]');
    if (!button || button.getAttribute('aria-pressed') === 'true') return;

    image.src = `assets/${sample.dataset.source}-${button.dataset.page}.png`;
    image.alt = button.dataset.alt;
    preview.href = `assets/${sample.dataset.source}.pdf#page=${button.dataset.page}`;
    preview.setAttribute('aria-label', `Open ${sample.dataset.name}'s CV, page ${button.dataset.page}`);
    buttons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
    status.textContent = `Page ${button.dataset.page} of ${buttons.length}`;
  });
}
