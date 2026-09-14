/* Progressive enhancement of Django's existing navigation and forms. */
(() => {
  document.getElementById('content-start')?.setAttribute('role', 'main');
  const sidebar = document.getElementById('nav-sidebar');
  const toggle = document.getElementById('flower-menu-toggle');
  const backdrop = document.querySelector('.flower-nav-backdrop');
  if (!sidebar) return;
  const mobile = window.matchMedia('(max-width: 900px)');
  const setOpen = (open) => {
    document.body.dataset.navOpen = String(open);
    toggle?.setAttribute('aria-expanded', String(open));
    if (backdrop) backdrop.hidden = !open;
    sidebar.inert = mobile.matches && !open;
  };
  setOpen(false);
  toggle?.addEventListener('click', () => {
    const open = document.body.dataset.navOpen !== 'true';
    setOpen(open);
    if (open) {
      // Apply the visibility change before moving keyboard focus into the drawer.
      getComputedStyle(sidebar).visibility;
      sidebar.querySelector('input')?.focus({preventScroll: true});
    }
  });
  backdrop?.addEventListener('click', () => { setOpen(false); toggle?.focus(); });
  mobile.addEventListener('change', () => setOpen(false));
  sidebar.querySelector('[aria-current="page"]')?.closest('details')?.setAttribute('open', '');
  const input = document.getElementById('nav-filter');
  const groups = [...sidebar.querySelectorAll('.flower-nav-group')];
  const initialOpen = new Map(groups.map(group => [group, group.open]));
  const empty = document.getElementById('flower-nav-empty');
  const filter = () => {
    const value = input.value.toLocaleLowerCase().trim();
    let matches = 0;
    groups.forEach(group => {
      let count = 0;
      group.querySelectorAll('[data-nav-item]').forEach(item => {
        const show = item.textContent.toLocaleLowerCase().includes(value);
        item.hidden = !show;
        if (show) count++;
      });
      group.hidden = count === 0;
      group.open = value ? count > 0 : initialOpen.get(group);
      matches += count;
    });
    if (empty) empty.hidden = matches > 0;
  };
  input?.addEventListener('input', filter);
  input?.addEventListener('keyup', filter);
  input?.addEventListener('change', filter);
  if (input?.value) filter();
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (input?.value && document.activeElement === input) { input.value = ''; filter(); }
      else if (mobile.matches && document.body.dataset.navOpen === 'true') { setOpen(false); toggle?.focus(); }
    }
    if (event.key === 'Tab' && mobile.matches && document.body.dataset.navOpen === 'true') {
      const focusable = [...sidebar.querySelectorAll('a[href], input, summary')].filter(node => node.getClientRects().length);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
})();
