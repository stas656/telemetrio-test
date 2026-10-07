/* Alternative MCP landing page: prompt builder and refinement walkthrough.
   The builder only composes text to copy — it never runs a search. */
(() => {
  const cfg = JSON.parse(document.getElementById('mcp-config').textContent);
  const { track } = window.telemetrioMcp;
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  };

  // ---------- Prompt builder ----------
  const b = cfg.builder;
  const FIELDS = ['category', 'country', 'goal', 'format'];
  const selects = Object.fromEntries(FIELDS.map((f) => [f, document.querySelector(`.builder select[data-field="${f}"]`)]));
  const output = document.getElementById('builder-prompt');
  const copyBtn = document.querySelector('[data-copy="builder-prompt"]');
  const previewBody = document.getElementById('builder-preview-body');
  const chosen = () => Object.fromEntries(FIELDS.map((f) => [f, b.options[f].find((o) => o.id === selects[f].value)]));
  // Same composition rule as AltPage.compose() in lib/alt_page.py.
  const compose = (o) => `${b.sentence.start} ${o.category.label} ${b.sentence.in} ${o.country.label}${o.goal.phrase}${b.sentence.end} ${o.format.phrase}`;
  const avatarColor = (name) => b.avatarColors[[...name].reduce((s, ch) => s + ch.charCodeAt(0), 0) % b.avatarColors.length];

  const channel = (name) => {
    const wrap = el('span', 'ch');
    const ava = el('span', 'ch-ava', name.replace('Demo:', '').trim().charAt(0));
    ava.setAttribute('aria-hidden', 'true');
    ava.style.setProperty('--c', `var(${avatarColor(name)})`);
    wrap.append(ava, name);
    return wrap;
  };
  const linkPlaceholder = () => {
    const span = el('span', 'link-ph', b.linkPlaceholder);
    span.append(el('span', 'sr-only', ` (${b.linkNote})`));
    return span;
  };
  const renderPreview = (o, prompt) => {
    const rows = b.previewNames.map((n) => ({ name: n.replace('{name}', o.category.name), country: o.country.name, category: o.category.name }));
    if (o.format.id === 'list') {
      const ul = el('ul', 'preview-list');
      rows.forEach((r) => {
        const li = el('li');
        li.append(channel(r.name), el('span', 'preview-meta', `${r.country} · ${r.category}`));
        ul.append(li);
      });
      previewBody.replaceChildren(ul);
      return;
    }
    const table = el('table', 'results');
    table.append(el('caption', 'sr-only', prompt));
    const headRow = el('tr');
    ['channel', 'country', 'category', 'link'].forEach((k) => {
      const th = el('th', null, b.columns[k]);
      th.scope = 'col';
      headRow.append(th);
    });
    const thead = el('thead');
    thead.append(headRow);
    const tbody = el('tbody');
    rows.forEach((r) => {
      const tr = el('tr');
      const cells = [['channel', channel(r.name)], ['country', r.country], ['category', el('span', 'chip tone-a', r.category)], ['link', linkPlaceholder()]];
      cells.forEach(([k, content]) => {
        const td = el('td');
        td.dataset.label = b.columns[k];
        td.append(content);
        tr.append(td);
      });
      tbody.append(tr);
    });
    table.append(thead, tbody);
    const wrap = el('div', 'results-wrap');
    wrap.append(table);
    previewBody.replaceChildren(wrap);
  };
  const update = (field) => {
    const o = chosen();
    const id = `builder:${FIELDS.map((f) => o[f].id).join('-')}`;
    const prompt = compose(o);
    output.textContent = prompt;
    output.dataset.promptId = id;
    copyBtn.dataset.promptId = id;
    renderPreview(o, prompt);
    // Only fixed option ids are sent — never freeform text.
    if (field) track('mcp_builder_change', { field, option_id: o[field].id, prompt_id: id });
  };
  if (output) {
    FIELDS.forEach((f) => selects[f].addEventListener('change', () => update(f)));
    // Browsers may restore earlier selections on reload; resync the prompt if so.
    if (FIELDS.some((f) => selects[f].selectedIndex !== 0)) update();
  }

  // ---------- Refinement walkthrough ----------
  const steps = [...document.querySelectorAll('.refine-step')];
  const nextBtn = document.querySelector('.refine-next');
  if (!steps.length || !nextBtn) return;
  const nextLabel = nextBtn.querySelector('.refine-next-label');
  let current = 0;
  const select = (i, { focus = false, user = false } = {}) => {
    current = i;
    steps.forEach((s, j) => {
      const on = j === i;
      s.setAttribute('aria-selected', String(on));
      s.tabIndex = on ? 0 : -1;
      document.getElementById(s.getAttribute('aria-controls')).hidden = !on;
    });
    nextLabel.textContent = i === steps.length - 1 ? nextBtn.dataset.restart : nextBtn.dataset.next;
    if (focus) steps[i].focus();
    if (user) track('mcp_demo_select', { scenario_id: `refine:${steps[i].dataset.step}` });
  };
  steps.forEach((s, i) => {
    s.addEventListener('click', () => select(i, { user: true }));
    s.addEventListener('keydown', (e) => {
      const move = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1, Home: -i, End: steps.length - 1 - i }[e.key];
      if (move === undefined) return;
      e.preventDefault();
      select((i + move + steps.length) % steps.length, { focus: true, user: true });
    });
  });
  // On narrow screens the shortlist sits below the steps, so bring it into view after "Next step".
  const main = document.querySelector('.refine-main');
  const stacked = matchMedia('(max-width: 860px)');
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  nextBtn.addEventListener('click', () => {
    select((current + 1) % steps.length, { user: true });
    if (stacked.matches && main.getBoundingClientRect().top > innerHeight * 0.5) {
      main.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    }
  });
})();
