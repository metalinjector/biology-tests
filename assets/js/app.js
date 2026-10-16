/* Олимпиада под микроскопом — логика тренажёра.
   Данные: window.OLYMPIAD_DATA (assets/js/data.js, собирается tools/build_data.py). */
(() => {
  'use strict';

  const DATA = window.OLYMPIAD_DATA;
  if (!DATA) { document.getElementById('app').textContent = 'Не удалось загрузить задания.'; return; }
  const OLY = DATA.olympiads;
  const app = document.getElementById('app');
  const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ------------------------------------------------------------ подготовка данных
  for (const o of OLY) {
    o.flat = [];
    o.sections.forEach((s) => {
      s.bonus = s.id === 'g8-train';
      s.questions.forEach((q) => { q.sec = s; q.olymp = o; q.index = o.flat.length; o.flat.push(q); });
    });
    o.main = o.flat.filter((q) => !q.sec.bonus);
  }
  const byId = {};
  OLY.forEach((o) => o.flat.forEach((q) => { byId[q.id] = q; }));

  // ------------------------------------------------------------ хранилище (только в этом браузере)
  const STORE_KEY = 'olymp-microscope-v1';
  const blankState = () => ({ answers: {}, hints: {}, settings: { sound: true, theme: '', peek: false }, last: {}, name: '' });
  const store = (() => {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        const s = JSON.parse(raw);
        const b = blankState();
        return { ...b, ...s, settings: { ...b.settings, ...(s.settings || {}) } };
      }
    } catch (e) { /* приватный режим или запрет хранилища */ }
    return blankState();
  })();
  const save = () => { try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch (e) { /* ничего */ } };

  if (store.settings.theme) document.documentElement.setAttribute('data-theme', store.settings.theme);

  // ------------------------------------------------------------ иконки
  const I = {
    star: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.8l2.75 5.86 6.42.75-4.75 4.38 1.26 6.34L12 17.02l-5.68 3.11 1.26-6.34L2.83 9.41l6.42-.75z"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    cross: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" d="M6.5 6.5l11 11M17.5 6.5l-11 11"/></svg>',
    info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 11v6M12 7.3v.2" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
    chev: '<svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6"/></svg>',
    back: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M15 5l-7 7 7 7"/></svg>',
    next: '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>',
    book: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M4 5.5C6.5 4 9.5 4 12 6c2.5-2 5.5-2 8-.5V19c-2.5-1.5-5.5-1.5-8 .5-2.5-2-5.5-2-8-.5z"/><path d="M12 6v13.5" stroke="currentColor" stroke-width="2"/></svg>',
    bulb: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M9 18h6M10 21h4M12 3a6 6 0 00-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0012 3z"/></svg>',
    lock: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8.5 10.5V8a3.5 3.5 0 017 0v2.5" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    sun: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="2"/><path stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>',
    moon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M19.5 14.5A8 8 0 019.5 4.5a8 8 0 1010 10z"/></svg>',
    auto: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 3.5a8.5 8.5 0 010 17z" fill="currentColor"/></svg>',
    soundOn: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M15.5 9a4 4 0 010 6M18 6.5a7.5 7.5 0 010 11"/></svg>',
    soundOff: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M16 9.5l5 5M21 9.5l-5 5"/></svg>',
    seal: '<svg class="seal" viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="currentColor"><circle cx="50" cy="50" r="44" stroke-width="2"/><circle cx="50" cy="50" r="37" stroke-width="1" stroke-dasharray="2 3"/></g><path fill="currentColor" d="M50 26l6.4 13.6 14.9 1.8-11 10.2 2.9 14.7L50 59l-13.2 7.3 2.9-14.7-11-10.2 14.9-1.8z"/><text x="50" y="79" text-anchor="middle" font-size="6.6" font-family="IBM Plex Mono, monospace" fill="currentColor" letter-spacing="1.2">БИОЛОГИЯ</text></svg>',
    brand: '<svg class="brand-mark" viewBox="0 0 40 40" aria-hidden="true"><rect x="2" y="11" width="36" height="18" rx="3" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/><rect x="3" y="12" width="10" height="16" rx="2" fill="var(--frost)"/><path d="M5 15h6M5 18h6M5 21h4" stroke="var(--muted)" stroke-width="1.2" stroke-linecap="round"/><circle cx="26" cy="20" r="6.2" fill="var(--accent)" opacity=".22"/><circle cx="26" cy="20" r="6.2" fill="none" stroke="var(--accent)" stroke-width="1.6"/><circle cx="27.4" cy="18.8" r="1.9" fill="var(--accent)"/></svg>',
  };
  const stars = (n, max = 3) => Array.from({ length: max }, (_, i) => `<span class="${i < n ? '' : 'off'}">${I.star}</span>`).join('');

  // ------------------------------------------------------------ утилиты
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const stripTags = (h) => { const t = document.createElement('template'); t.innerHTML = h; return t.content.textContent.replace(/\s+/g, ' ').trim(); };
  const norm = (s) => String(s || '').toLowerCase().replace(/ё/g, 'е').replace(/[«»"'().,;:!?…]/g, ' ').replace(/[—–]/g, ' ').replace(/\s+/g, ' ').trim();
  const reCache = {};
  const rx = (src) => (reCache[src] ||= new RegExp(src));
  const plural = (n, one, few, many) => {
    const m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  };
  const truncate = (s, n) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s);
  const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];

  // ------------------------------------------------------------ состояние ответов
  const rec = (q) => store.answers[q.id];
  function status(q) {
    const r = rec(q);
    if (!r) return 'none';
    if (r.revealed) return 'rev';
    if (r.solved) return r.attempts > 1 ? 'ok2' : 'ok';
    return r.attempts > 0 ? 'bad' : 'none';
  }
  const starsOf = (q) => { const r = rec(q); return r && r.solved && !r.revealed ? r.stars : 0; };
  function olympStats(o, list = o.main) {
    const st = { total: list.length, ok: 0, ok2: 0, rev: 0, bad: 0, none: 0, stars: 0, max: list.length * 3 };
    list.forEach((q) => { st[status(q)]++; st.stars += starsOf(q); });
    st.done = st.ok + st.ok2 + st.rev;
    return st;
  }
  const allStars = () => OLY.reduce((a, o) => a + o.flat.reduce((b, q) => b + starsOf(q), 0), 0);
  const allMax = () => OLY.reduce((a, o) => a + o.flat.length * 3, 0);

  // ------------------------------------------------------------ звук, вибрация, конфетти
  let actx = null;
  function tone(seq) {
    if (!store.settings.sound) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      if (actx.state === 'suspended') actx.resume();
      const t0 = actx.currentTime + 0.01;
      seq.forEach(([f, start, dur, type = 'sine', vol = 0.16]) => {
        const osc = actx.createOscillator();
        const g = actx.createGain();
        osc.type = type; osc.frequency.value = f;
        g.gain.setValueAtTime(0.0001, t0 + start);
        g.gain.exponentialRampToValueAtTime(vol, t0 + start + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + start + dur);
        osc.connect(g).connect(actx.destination);
        osc.start(t0 + start); osc.stop(t0 + start + dur + 0.05);
      });
    } catch (e) { /* звук недоступен */ }
  }
  const sfx = {
    ok: () => tone([[659.3, 0, 0.16], [880, 0.1, 0.2], [1318.5, 0.2, 0.32, 'sine', 0.1]]),
    bad: () => tone([[220, 0, 0.18, 'triangle', 0.2], [164.8, 0.13, 0.32, 'triangle', 0.18]]),
    tick: () => tone([[540, 0, 0.07, 'sine', 0.06]]),
  };
  const buzz = (ms) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { /* нет вибрации */ } };

  const fx = document.getElementById('fx');
  let fxParts = [], fxRaf = 0;
  function burst(x, y, n = 70) {
    if (!fx || reducedMotion()) return;
    const cs = getComputedStyle(document.documentElement);
    const cols = ['--accent', '--ok', '--amber', '--c-violet', '--c-teal'].map((v) => cs.getPropertyValue(v).trim()).concat(['#e86a92']);
    for (let i = 0; i < n; i++) {
      const a = (Math.PI * 2 * i) / n + Math.random() * 0.4;
      const sp = 4 + Math.random() * 7;
      fxParts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 4, r: 4 + Math.random() * 6, c: pick(cols), life: 1, rot: Math.random() * 6, e: 0.75 + Math.random() * 0.5 });
    }
    if (!fxRaf) fxRaf = requestAnimationFrame(fxStep);
  }
  function fxStep() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const w = window.innerWidth, h = window.innerHeight;
    if (fx.width !== Math.round(w * dpr) || fx.height !== Math.round(h * dpr)) { fx.width = Math.round(w * dpr); fx.height = Math.round(h * dpr); }
    const ctx = fx.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    fxParts = fxParts.filter((p) => p.life > 0);
    for (const p of fxParts) {
      p.vy += 0.28; p.vx *= 0.985; p.x += p.vx; p.y += p.vy; p.life -= 0.012; p.rot += 0.05;
      ctx.save();
      ctx.globalAlpha = Math.max(0, Math.min(1, p.life * 1.4));
      ctx.translate(p.x, p.y); ctx.rotate(p.rot);
      // «клетка»: оболочка, цитоплазма и ядро
      ctx.beginPath(); ctx.ellipse(0, 0, p.r, p.r * p.e, 0, 0, Math.PI * 2);
      ctx.fillStyle = p.c; ctx.globalAlpha *= 0.35; ctx.fill();
      ctx.globalAlpha = Math.max(0, Math.min(1, p.life * 1.4));
      ctx.lineWidth = 1.5; ctx.strokeStyle = p.c; ctx.stroke();
      ctx.beginPath(); ctx.arc(p.r * 0.2, -p.r * 0.1, p.r * 0.32, 0, Math.PI * 2); ctx.fillStyle = p.c; ctx.fill();
      ctx.restore();
    }
    if (fxParts.length) fxRaf = requestAnimationFrame(fxStep);
    else { fxRaf = 0; ctx.clearRect(0, 0, w, h); }
  }

  // ------------------------------------------------------------ навигация
  const view = { screen: 'home', oid: null, idx: 0, noteId: null, deck: null, queue: null };
  let leaveHook = null;
  let entering = true; // анимация появления — только при смене экрана, не при перерисовке
  const enterCls = () => (entering ? ' screen' : '');

  function token() {
    switch (view.screen) {
      case 'quiz': return `${view.oid}-q${view.idx + 1}`;
      case 'results': return `${view.oid}-itogi`;
      case 'notes': return `${view.oid}-pamyatki`;
      case 'cards': return `kartochki-${view.deck}`;
      default: return '';
    }
  }
  function parseToken(t) {
    t = (t || '').replace(/^#/, '');
    let m;
    if ((m = t.match(/^(g7|g8)-q(\d+)$/))) return { screen: 'quiz', oid: m[1], idx: Math.max(0, +m[2] - 1) };
    if ((m = t.match(/^(g7|g8)$/))) return { screen: 'quiz', oid: m[1], idx: store.last[m[1]] || 0 };
    if ((m = t.match(/^(g7|g8)-itogi$/))) return { screen: 'results', oid: m[1] };
    if ((m = t.match(/^(g7|g8)-pamyatki$/))) return { screen: 'notes', oid: m[1] };
    if ((m = t.match(/^kartochki-(self|dict)$/))) return { screen: 'cards', deck: m[1] };
    return { screen: 'home' };
  }
  function go(next, { push = true, scroll = true } = {}) {
    const run = () => {
      if (leaveHook) { leaveHook(); leaveHook = null; }
      Object.assign(view, { noteId: null, queue: view.screen === 'quiz' && next.screen === 'quiz' && next.oid === view.oid ? view.queue : null }, next);
      if (view.oid && !OLY.find((o) => o.id === view.oid)) view.screen = 'home';
      entering = !document.startViewTransition || reducedMotion();
      render();
      entering = false;
      if (scroll) window.scrollTo(0, 0);
      const tk = token();
      try {
        const url = tk ? '#' + tk : location.pathname + location.search;
        if (push) history.pushState({ tk }, '', url); else history.replaceState({ tk }, '', url);
      } catch (e) { /* в песочнице история может быть недоступна */ }
    };
    if (document.startViewTransition && !reducedMotion()) document.startViewTransition(run);
    else run();
  }
  window.addEventListener('popstate', () => go(parseToken(location.hash), { push: false }));

  const olymp = () => OLY.find((o) => o.id === view.oid);

  // ------------------------------------------------------------ шапка
  function topbar(extra = '') {
    const th = store.settings.theme;
    const themeIco = th === 'dark' ? I.moon : th === 'light' ? I.sun : I.auto;
    const themeLbl = th === 'dark' ? 'Тема: тёмная' : th === 'light' ? 'Тема: светлая' : 'Тема: как в системе';
    return `<header class="topbar"><div class="topbar-inner">
      <button class="brand" data-act="home" aria-label="На главную">${I.brand}<span class="brand-text">Под микроскопом<small>олимпиадная биология</small></span></button>
      <span class="topbar-spacer"></span>
      ${extra}
      <span class="top-stat" title="Звёзды за все олимпиады"><span class="star" style="display:inline-flex;width:18px">${I.star}</span><span class="tabnum">${allStars()}</span><span class="lbl">из ${allMax()}</span></span>
      <span class="top-actions">
        <button class="icon-btn" data-act="sound" aria-pressed="${store.settings.sound}" aria-label="${store.settings.sound ? 'Выключить звук' : 'Включить звук'}" title="Звук">${store.settings.sound ? I.soundOn : I.soundOff}</button>
        <button class="icon-btn" data-act="theme" aria-label="${themeLbl}" title="${themeLbl}">${themeIco}</button>
      </span>
    </div></header>`;
  }

  // ------------------------------------------------------------ главная
  let factPool = null;
  function facts() {
    if (factPool) return factPool;
    factPool = [];
    const t = document.createElement('template');
    OLY.forEach((o) => o.flat.forEach((q) => {
      t.innerHTML = q.explanation;
      t.content.querySelectorAll('.mem').forEach((m) => {
        const lbl = m.querySelector('b.m'); if (lbl) lbl.remove();
        const html = m.innerHTML.trim();
        if (stripTags(html).length > 40) factPool.push({ kind: 'Как запомнить', html, q });
      });
      t.content.querySelectorAll('.b-hor li').forEach((li) => {
        li.querySelectorAll('.ou').forEach((x) => x.remove());
        factPool.push({ kind: 'Олимпиадный горизонт', html: li.innerHTML.trim(), q });
      });
    }));
    return factPool;
  }
  let factIdx = -1;

  function renderHome() {
    const totalQ = OLY.reduce((a, o) => a + o.main.length, 0);
    const doneQ = OLY.reduce((a, o) => a + olympStats(o).done, 0);
    const pool = facts();
    if (factIdx < 0) factIdx = Math.floor(Math.random() * pool.length);
    const fact = pool[factIdx % pool.length];
    const cards = OLY.map((o) => {
      const st = olympStats(o);
      const pct = (n) => (st.total ? (100 * n) / st.total : 0);
      const figs = o.flat.reduce((a, q) => a + ((q.explanation + q.media).match(/<svg|<img/g) || []).length, 0);
      const mistakes = o.main.filter((q) => ['bad', 'rev', 'ok2'].includes(status(q))).length;
      const started = st.done + st.bad > 0;
      return `<article class="olymp-card">
        <div class="olymp-head">
          <div class="grade">${o.grade}<small>класс</small></div>
          <div><h3>${esc(o.stage)} · ${esc(o.year)}</h3><p>${esc(o.subtitle.split(' · ').slice(2).join(' · ') || 'теоретическая часть')}</p></div>
        </div>
        <div class="olymp-body">
          <ul class="olymp-facts">
            <li><b>${o.main.length}</b> ${plural(o.main.length, "задание", "задания", "заданий")}</li>
            <li><b>${figs}</b> ${plural(figs, "рисунок", "рисунка", "рисунков")} и схем</li>
            ${o.flat.length > o.main.length ? `<li><b>+${o.flat.length - o.main.length}</b> бонусных</li>` : ''}
          </ul>
          <div class="meter" role="img" aria-label="Решено ${st.done} из ${st.total}">
            <span class="m-ok" style="width:${pct(st.ok)}%"></span><span class="m-mid" style="width:${pct(st.ok2)}%"></span><span class="m-bad" style="width:${pct(st.rev)}%"></span>
          </div>
          <div class="meter-legend"><span><i style="background:var(--ok)"></i>с первой попытки: ${st.ok}</span><span><i style="background:var(--amber)"></i>не сразу: ${st.ok2}</span><span><i style="background:var(--bad)"></i>подсмотрено: ${st.rev}</span><span class="tabnum">★ ${st.stars} из ${st.max}</span></div>
        </div>
        <div class="olymp-actions">
          <button class="btn btn-primary" data-act="open" data-oid="${o.id}">${started ? 'Продолжить' : 'Начать'}${I.next}</button>
          ${mistakes ? `<button class="btn" data-act="mistakes" data-oid="${o.id}">Работа над ошибками · ${mistakes}</button>` : ''}
          <button class="btn btn-ghost" data-act="notes" data-oid="${o.id}">Памятки</button>
          ${st.done ? `<button class="btn btn-ghost" data-act="results" data-oid="${o.id}">Итоги</button>` : ''}
        </div>
      </article>`;
    }).join('');

    const g8 = OLY.find((o) => o.id === 'g8');
    app.innerHTML = topbar() + `<main class="wrap-wide${enterCls()}">
      <section class="hero">
        <div>
          <p class="eyebrow">Тренажёр по олимпиадам · биология <span style="white-space:nowrap">7–8 класс</span></p>
          <h1>Олимпиада <em>под&nbsp;микроскопом</em></h1>
          <p class="hero-lead">Настоящие задания городского и школьного этапов. Отвечай сама, а если ошибёшься — тренажёр подскажет, и можно раскрыть подробный разбор с рисунками, ловушками и приёмами запоминания.</p>
          <div class="hero-stats">
            <span class="chip-stat"><b>${doneQ}</b> из ${totalQ} заданий решено</span>
            <span class="chip-stat"><span class="star" style="display:inline-flex;width:16px;align-self:center">${I.star}</span><b>${allStars()}</b> звёзд собрано</span>
          </div>
        </div>
        <figure class="eyepiece"><div class="eyepiece-ring"><canvas id="eyepiece" width="300" height="300" aria-label="Клетки кожицы лука под микроскопом"></canvas></div>
          <figcaption>Кожица лука · ×400 · окраска метиленовым синим</figcaption></figure>
      </section>

      <h2 class="section-title">Олимпиады</h2>
      <div class="olymp-grid">${cards}</div>

      <h2 class="section-title">Как это работает</h2>
      <ol class="how">
        <li><b>Отвечай.</b> Выбери вариант, впиши слово или собери соответствие и нажми «Проверить».</li>
        <li><b>Ошиблась — пробуй ещё.</b> Неверное подсвечивается красным. С первой попытки — три звезды, со второй — две, дальше — одна.</li>
        <li><b>Раскрой разбор.</b> После первой попытки открывается подробное объяснение: почему верно, где ловушка и как запомнить. Переключатель «Ответы сразу» открывает его и до ответа. Где нужно вписать слово, можно подсмотреть до трёх первых букв.</li>
      </ol>

      <h2 class="section-title">Повторить и запомнить</h2>
      <div class="extras">
        <button class="extra" data-act="cards" data-deck="self"><span class="tag">карточки</span><b>Самопроверка</b><span>${g8.cards.length} вопросов-карточек: переверни и проверь себя</span></button>
        <button class="extra" data-act="cards" data-deck="dict"><span class="tag">карточки</span><b>Корни терминов</b><span>${g8.dictCards.length} терминов: откуда слово и что значит</span></button>
        <button class="extra" data-act="notes" data-oid="g7"><span class="tag">7 класс</span><b>Главные ловушки</b><span>Памятки, ключ ответов и правила разбора</span></button>
        <button class="extra" data-act="notes" data-oid="g8"><span class="tag">8 класс</span><b>Шпаргалка и словарь</b><span>Экспресс-шпаргалка, словарь корней, ключ</span></button>
      </div>

      <h2 class="section-title">Знаешь ли ты?</h2>
      <article class="prose fact src-${fact.q.src}">
        <p class="eyebrow" style="margin-bottom:8px">${esc(fact.kind)} · ${esc(fact.q.olymp.grade)} класс, ${esc(qLabel(fact.q))}</p>
        <div>${fact.html}</div>
        <div class="actions" style="margin-top:14px"><button class="btn btn-sm" data-act="fact">Ещё факт</button><button class="btn btn-sm btn-ghost" data-act="goto" data-qid="${fact.q.id}">К этому вопросу${I.next}</button></div>
      </article>

      <p class="footnote">Задания и разборы взяты из материалов олимпиад: городской этап, 7 класс, 2014/2015 и школьный этап, 8 класс, 2016/2017. Прогресс хранится только в этом браузере.</p>
    </main>`;
    startEyepiece();
  }

  // ------------------------------------------------------------ окуляр: клетки кожицы лука
  function startEyepiece() {
    const cv = document.getElementById('eyepiece');
    if (!cv) return;
    const ctx = cv.getContext('2d');
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const size = Math.max(160, Math.round(cv.getBoundingClientRect().width || 280));
    cv.width = size * dpr; cv.height = size * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // кирпичная кладка вытянутых клеток со случайным разбросом
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const cw = size * 0.36, ch = size * 0.105;
    const rows = Math.ceil(size / ch) + 3;
    const field = cw * 6;
    const cells = [];
    for (let r = -1; r < rows; r++) {
      let x = (r % 2) * cw * 0.5 - cw;
      while (x < field + cw) {
        const w = cw * (0.75 + rnd() * 0.5);
        cells.push({ x, y: r * ch, w, h: ch, nx: 0.3 + rnd() * 0.4, ny: 0.35 + rnd() * 0.3, nr: ch * (0.17 + rnd() * 0.06), tint: 0.1 + rnd() * 0.12 });
        x += w;
      }
    }
    let raf = 0, t0 = performance.now(), visible = true;
    const draw = (off) => {
      ctx.clearRect(0, 0, size, size);
      ctx.save();
      ctx.beginPath(); ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2); ctx.clip();
      ctx.fillStyle = '#f5f0e3'; ctx.fillRect(0, 0, size, size);
      ctx.translate(-(off % field), -size * 0.05);
      for (let rep = 0; rep < 2; rep++) {
        for (const c of cells) {
          const x = c.x + rep * field;
          if (x > (off % field) + size + cw || x + c.w < (off % field) - cw) continue;
          ctx.beginPath();
          ctx.roundRect ? ctx.roundRect(x + 1.5, c.y + 1.5, c.w - 3, c.h - 3, 5) : ctx.rect(x + 1.5, c.y + 1.5, c.w - 3, c.h - 3);
          ctx.fillStyle = `rgba(52, 96, 196, ${c.tint})`; ctx.fill();
          ctx.lineWidth = 1.6; ctx.strokeStyle = 'rgba(33, 72, 160, .6)'; ctx.stroke();
          ctx.beginPath(); ctx.ellipse(x + c.w * c.nx, c.y + c.h * c.ny, c.nr * 1.25, c.nr, 0, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(28, 52, 140, .78)'; ctx.fill();
          ctx.beginPath(); ctx.arc(x + c.w * c.nx + c.nr * 0.35, c.y + c.h * c.ny - c.nr * 0.2, c.nr * 0.32, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(12, 26, 80, .9)'; ctx.fill();
        }
      }
      ctx.restore();
      // виньетка, перекрестие и масштабная линейка
      const g = ctx.createRadialGradient(size / 2, size / 2, size * 0.32, size / 2, size / 2, size / 2);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(10,20,25,.55)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(20, 30, 35, .35)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(size / 2, size * 0.12); ctx.lineTo(size / 2, size * 0.88); ctx.moveTo(size * 0.12, size / 2); ctx.lineTo(size * 0.88, size / 2); ctx.stroke();
      for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(size / 2 + i * size * 0.06, size / 2 - 4); ctx.lineTo(size / 2 + i * size * 0.06, size / 2 + 4); ctx.stroke(); }
      const bx = size * 0.56, by = size * 0.78, bl = size * 0.18;
      ctx.fillStyle = 'rgba(15, 25, 30, .85)'; ctx.fillRect(bx, by, bl, 3);
      ctx.font = `600 ${Math.max(9, size * 0.042)}px "IBM Plex Mono", monospace`; ctx.textAlign = 'center';
      ctx.fillText('50 мкм', bx + bl / 2, by - 6);
    };
    const loop = (now) => { draw((now - t0) * 0.006); raf = requestAnimationFrame(loop); };
    draw(0);
    let io = null;
    if (!reducedMotion()) {
      if ('IntersectionObserver' in window) {
        io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible && !raf) raf = requestAnimationFrame(loop); if (!visible && raf) { cancelAnimationFrame(raf); raf = 0; } });
        io.observe(cv);
      } else raf = requestAnimationFrame(loop);
    }
    leaveHook = () => { if (raf) cancelAnimationFrame(raf); raf = 0; if (io) io.disconnect(); };
  }

  // ------------------------------------------------------------ вопрос
  const KIND = { single: 'Один ответ', multi: 'Несколько верных', text: 'Пропущенное слово', terms: 'Термины', match: 'Соответствие', table: 'Таблица' };
  function qLabel(q) {
    if (q.sec.bonus) return 'бонус ' + q.num;
    if (q.src === 'g8') return q.head || 'задание ' + q.num;
    const sec = q.sec.short.split(' · ')[0];
    return `${sec}, № ${q.num}`;
  }
  const work = {}; // незавершённые ответы на экране: qid → ответ

  function getResp(q) {
    if (work[q.id] !== undefined) return work[q.id];
    const r = rec(q);
    if (r && r.response !== undefined) return JSON.parse(JSON.stringify(r.response));
    switch (q.type) {
      case 'single': return null;
      case 'multi': return [];
      case 'text': return q.blanks.map(() => '');
      case 'terms': return q.items.map(() => '');
      case 'match': return {};
      case 'table': return {};
      default: return null;
    }
  }
  function correctResp(q) {
    switch (q.type) {
      case 'single': return q.answer;
      case 'multi': return q.answer.slice();
      case 'match': return { ...q.answer };
      case 'table': return JSON.parse(JSON.stringify(q.answer));
      case 'text': return null;
      case 'terms': return null;
      default: return null;
    }
  }
  const sameSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x));

  function evaluate(q, resp) {
    const res = { ok: false, parts: {}, notes: [], filled: true };
    switch (q.type) {
      case 'single':
        res.filled = !!resp; res.ok = resp === q.answer; break;
      case 'multi': {
        res.filled = resp.length > 0;
        resp.forEach((k) => { res.parts[k] = q.answer.includes(k); });
        res.ok = sameSet(resp, q.answer);
        res.hit = resp.filter((k) => q.answer.includes(k)).length;
        res.extra = resp.length - res.hit;
        break;
      }
      case 'text':
      case 'terms': {
        const specs = q.type === 'text' ? q.blanks : q.items;
        res.filled = resp.some((v) => norm(v));
        specs.forEach((sp, i) => {
          const v = norm(resp[i]);
          let ok = !!v && sp.accept.some((r) => rx(r).test(v));
          let note = null;
          if (!ok && v && sp.near) { const n = sp.near.find((h) => rx(h.re).test(v)); if (n) { ok = true; note = { cls: 'okish', msg: n.msg }; } }
          if (!ok && v && sp.hints) { const h = sp.hints.find((h) => rx(h.re).test(v)); if (h) note = { cls: 'bad', msg: h.msg }; }
          if (!ok && !v) note = { cls: 'bad', msg: 'Пропуск не заполнен.' };
          res.parts[i] = ok;
          if (note) res.notes[i] = note;
        });
        res.ok = specs.every((_, i) => res.parts[i]);
        break;
      }
      case 'match': {
        res.filled = Object.values(resp).some(Boolean);
        q.left.forEach((l) => { res.parts[l.key] = resp[l.key] === q.answer[l.key]; });
        res.ok = q.left.every((l) => res.parts[l.key]);
        break;
      }
      case 'table': {
        res.filled = Object.values(resp).some((r) => r && Object.values(r).some(Boolean));
        q.rows.forEach((r) => q.columns.forEach((c) => {
          res.parts[r.key + '|' + c.key] = ((resp[r.key] || {})[c.key] || '') === q.answer[r.key][c.key];
        }));
        res.ok = Object.values(res.parts).every(Boolean);
        break;
      }
      default: break;
    }
    const vals = Object.values(res.parts);
    res.right = vals.filter(Boolean).length;
    res.total = q.type === 'multi' ? q.answer.length : vals.length;
    return res;
  }

  // --- подсказка «Показать первую букву» (до трёх букв, слово целиком не раскрывается)
  const HINT_NAMES = ['первую', 'вторую', 'третью'];
  const hintCount = (q, i) => ((store.hints[q.id] || {})[i]) || 0;
  const hintMax = (word) => Math.min(3, Array.from(word.replace(/\s+/g, '')).length - 1);
  const hintLetters = (word, n) => Array.from(word).slice(0, n).join('');
  const hintUsed = (q) => Object.values(store.hints[q.id] || {}).some((n) => n > 0);
  const clearQuestion = (q) => { delete store.answers[q.id]; delete store.hints[q.id]; delete work[q.id]; delete work['stmt:' + q.id]; };
  function hintHTML(q, i, spec, locked) {
    if (locked || !spec.word) return '';
    const n = hintCount(q, i);
    const shown = n ? `<span class="hint-letters">Начинается на «<b>${esc(hintLetters(spec.word, n))}</b>…»</span>` : '';
    const btn = n < hintMax(spec.word)
      ? `<button type="button" class="hint-btn" data-act="hint" data-i="${i}" title="Подсказка по буквам снимает одну звезду за вопрос">${I.bulb}Показать ${HINT_NAMES[n]} букву</button>`
      : '<span class="hint-end">Больше подсказок нет</span>';
    return `<div class="hint-row">${btn}${shown}</div>`;
  }
  function textHintsHTML(q, locked) {
    if (locked) return '';
    const many = q.blanks.length > 1;
    return `<div class="hints">${q.blanks.map((b, i) => `<div class="hint-line">${many ? `<span class="hint-lbl">Пропуск ${i + 1}</span>` : ''}${hintHTML(q, i, b, locked)}</div>`).join('')}</div>`;
  }
  const placeholderFor = (q, i, spec, base) => { const n = hintCount(q, i); return n ? hintLetters(spec.word, n) + '…' : base; };
  // разбор доступен после первой попытки, а с переключателем «Ответы сразу» — в любой момент
  const canOpen = (q) => { const r = rec(q); return !!store.settings.peek || !!(r && (r.attempts > 0 || r.revealed || r.solved)); };

  // --- разметка ответа по типам
  function optionsHTML(q, resp, r, locked, lastEval) {
    const tried = (r && r.tried) || [];
    const name = 'opt-' + q.id;
    const isMulti = q.type === 'multi';
    const solvedOrRev = r && (r.solved || r.revealed);
    const stmtSel = q.statements ? (work['stmt:' + q.id] || []) : null;
    return `<fieldset class="options ${locked ? 'locked' : ''}"><legend class="sr-only">Варианты ответа</legend>${q.options.map((o) => {
      const checked = isMulti ? resp.includes(o.key) : resp === o.key;
      let cls = '', flag = '';
      if (solvedOrRev) {
        const correct = isMulti ? q.answer.includes(o.key) : q.answer === o.key;
        if (correct) { cls = checked ? 'is-right' : 'is-missed'; flag = 'верно'; }
        else if (checked) { cls = 'is-wrong'; flag = 'неверно'; }
        else if (!isMulti && tried.includes(o.key)) { cls = 'is-wrong is-tried'; flag = 'было'; }
      } else if (lastEval && !lastEval.ok) {
        if (isMulti && checked && lastEval.parts[o.key] === false) { cls = 'is-wrong'; flag = 'лишнее'; }
        if (!isMulti && checked && resp !== q.answer) { cls = 'is-wrong'; flag = 'неверно'; }
      }
      if (!solvedOrRev && !isMulti && tried.includes(o.key) && !checked) { cls = 'is-tried'; flag = 'было'; }
      let matchBadge = '';
      if (stmtSel && stmtSel.length && !solvedOrRev) {
        const nums = (stripTags(o.html).match(/\d+/g) || []);
        if (sameSet(nums, stmtSel)) matchBadge = '<span class="opt-match">= твои отметки</span>';
      }
      return `<label class="opt ${cls}" data-key="${esc(o.key)}">
        <input type="${isMulti ? 'checkbox' : 'radio'}" name="${name}" value="${esc(o.key)}" ${checked ? 'checked' : ''} ${locked ? 'disabled' : ''} data-input="opt">
        <span class="opt-card"><span class="opt-key">${esc(o.key)}</span><span class="opt-text">${o.html}</span><span class="opt-flag">${flag || matchBadge}</span></span>
      </label>`;
    }).join('')}</fieldset>`;
  }

  function statementsHTML(q, locked) {
    const sel = work['stmt:' + q.id] || [];
    return `<p class="statements-hint">Сначала отметь подходящие пункты — это черновик. Вариант, который совпадёт с отметками, подсветится.</p>
      <ul class="statements">${q.statements.map((s) => `<li><button type="button" class="stmt" data-act="stmt" data-key="${esc(s.key)}" aria-pressed="${sel.includes(s.key)}" ${locked ? 'disabled' : ''}><b>${esc(s.key)})</b><span>${s.html}</span></button></li>`).join('')}</ul>`;
  }

  function matchHTML(q, resp, r, locked, lastEval) {
    const solvedOrRev = r && (r.solved || r.revealed);
    const longRight = q.right.some((x) => stripTags(x.html).length > 34);
    const legend = longRight && q.style !== 'segmented'
      ? `<ul class="match-legend">${q.right.map((x) => `<li><b>${esc(x.key)}</b><span>${x.html}</span></li>`).join('')}</ul>` : '';
    const rows = q.left.map((l, i) => {
      const val = resp[l.key] || '';
      let cls = '', fix = '';
      if (solvedOrRev || (lastEval && !lastEval.ok && val)) {
        const ok = val === q.answer[l.key];
        cls = ok ? 'is-right' : (val || solvedOrRev ? 'is-wrong' : '');
        if (solvedOrRev && !ok) {
          const right = q.right.find((x) => x.key === q.answer[l.key]);
          fix = `<p class="match-fix">Верно: ${esc(right.key)} — ${stripTags(right.html)}</p>`;
        }
      }
      const control = q.style === 'segmented'
        ? `<div class="seg" role="group" aria-label="${esc(stripTags(l.html))}">${q.right.map((x) => `<button type="button" data-act="seg" data-row="${esc(l.key)}" data-val="${esc(x.key)}" aria-pressed="${val === x.key}" ${locked ? 'disabled' : ''}>${x.html}</button>`).join('')}</div>`
        : `<select class="select ${val ? 'is-filled' : ''}" id="sel-${q.id}-${i}" data-input="match" data-row="${esc(l.key)}" ${locked ? 'disabled' : ''} aria-label="${esc(stripTags(l.html))}">
            <option value="">— выбери —</option>
            ${q.right.map((x) => `<option value="${esc(x.key)}" ${val === x.key ? 'selected' : ''}>${esc(x.key)}${longRight ? '. ' + esc(truncate(stripTags(x.html), 44)) : ') ' + esc(stripTags(x.html))}</option>`).join('')}
          </select>`;
      const keyBubble = q.style === 'segmented' || q.hideLeftKey ? '' : `<span class="opt-key">${esc(l.key)}</span>`;
      return `<div class="match-row ${cls}${q.style === 'segmented' ? ' seg-row' : ''}">
        <div class="match-left">${keyBubble}<span>${l.html}</span></div>
        ${control}${fix}
      </div>`;
    }).join('');
    return `${legend}<div class="match">
      ${q.style === 'segmented' ? '' : `<div class="match-head"><span>${esc(q.leftTitle || '')}</span><span>${esc(q.rightTitle || '')}</span></div>`}
      ${rows}</div>`;
  }

  function tableHTML(q, resp, r, locked, lastEval) {
    const solvedOrRev = r && (r.solved || r.revealed);
    const wide = q.columns.length > 2;
    return `<div class="table-wrap"><table class="grid-table ${wide ? 'gt-wide' : ''}">
      <thead><tr><th scope="col">${esc(q.corner || '')}</th>${q.columns.map((c) => `<th scope="col">${esc(c.title)}</th>`).join('')}</tr></thead>
      <tbody>${q.rows.map((row, ri) => `<tr><th scope="row">${esc(row.label)}</th>${q.columns.map((c, ci) => {
        const opts = row.options || c.options;
        const val = (resp[row.key] || {})[c.key] || '';
        const correct = q.answer[row.key][c.key];
        let cls = '', fix = '';
        if (solvedOrRev || (lastEval && !lastEval.ok && val)) {
          cls = val === correct ? 'is-right' : (val || solvedOrRev ? 'is-wrong' : '');
          if (solvedOrRev && val !== correct) fix = `<span class="fix">Верно: ${esc(correct)}</span>`;
        }
        return `<td class="${cls}" data-label="${esc(c.title)}"><select class="select ${val ? 'is-filled' : ''}" id="cell-${q.id}-${ri}-${ci}" data-input="cell" data-row="${esc(row.key)}" data-col="${esc(c.key)}" ${locked ? 'disabled' : ''} title="${esc(val)}" aria-label="${esc(row.label)}: ${esc(c.title)}">
          <option value="">—</option>${opts.map((o) => `<option ${val === o ? 'selected' : ''}>${esc(o)}</option>`).join('')}</select>${fix}</td>`;
      }).join('')}</tr>`).join('')}</tbody></table></div>`;
  }

  function textStemHTML(q, resp, r, locked, lastEval) {
    const parts = q.stem.split('……');
    const solvedOrRev = r && (r.solved || r.revealed);
    let out = parts[0];
    for (let i = 1; i < parts.length; i++) {
      const v = resp[i - 1] || '';
      let cls = '';
      if (lastEval || solvedOrRev) {
        const ok = lastEval ? lastEval.parts[i - 1] : (solvedOrRev && r.solved);
        cls = ok ? 'is-right' : (v ? 'is-wrong' : '');
      }
      out += `<input class="blank ${cls}" id="blank-${q.id}-${i - 1}" data-input="blank" data-i="${i - 1}" value="${esc(v)}" ${locked ? 'disabled' : ''} autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="${esc(placeholderFor(q, i - 1, q.blanks[i - 1], 'впиши слово'))}" aria-label="Пропуск ${i}">` + parts[i];
    }
    return out;
  }

  function termsHTML(q, resp, r, locked, lastEval) {
    const solvedOrRev = r && (r.solved || r.revealed);
    const answers = solvedOrRev ? termAnswers(q) : null;
    return `<ol class="terms">${q.items.map((it, i) => {
      const v = resp[i] || '';
      let cls = '', hint = '';
      if (lastEval) {
        cls = lastEval.parts[i] ? 'is-right' : 'is-wrong';
        const n = lastEval.notes[i];
        if (n) hint = `<p class="term-hint ${n.cls}">${esc(n.msg)}</p>`;
      }
      if (solvedOrRev && answers) {
        const ok = !!v && (it.accept.some((re) => rx(re).test(norm(v))) || (it.near || []).some((h) => rx(h.re).test(norm(v))));
        cls = ok ? 'is-right' : 'is-wrong';
        if (!ok) hint = `<p class="term-hint okish">Верно: ${esc(answers[i])}</p>`;
      }
      return `<li class="term ${cls}"><b>${i + 1}</b><span>${it.html}</span>
        <input class="blank ${cls}" id="term-${q.id}-${i}" data-input="term" data-i="${i}" value="${esc(v)}" ${locked ? 'disabled' : ''} autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="${esc(placeholderFor(q, i, it, 'термин'))}" aria-label="Термин ${i + 1}">${hintHTML(q, i, it, locked)}${hint}</li>`;
    }).join('')}</ol>`;
  }
  function termAnswers(q) {
    const t = stripTags(q.answerHtml);
    const out = [];
    const re = /(\d+) — (.*?)(?:;|\.$|$)/g;
    let m;
    while ((m = re.exec(t))) out[+m[1] - 1] = m[2].trim();
    return out;
  }

  // --- экран вопроса
  let lastEval = null;
  let drawerOpen = false;

  function renderQuiz() {
    const o = olymp();
    if (!o) return go({ screen: 'home' }, { push: false });
    view.idx = Math.min(Math.max(0, view.idx), o.flat.length - 1);
    const q = o.flat[view.idx];
    if (view.queue && view.queue.fresh && view.queue.fresh.has(view.idx)) {
      view.queue.fresh.delete(view.idx);
      clearQuestion(q);
    }
    store.last[o.id] = view.idx; save();
    const r = rec(q);
    const resp = getResp(q);
    const locked = !!(r && (r.solved || r.revealed));
    const st = olympStats(o);

    const queue = view.queue;
    const pos = queue ? queue.indexOf(view.idx) : -1;
    const counter = queue && pos >= 0
      ? `Работа над ошибками · ${pos + 1} / ${queue.length}`
      : `Вопрос ${view.idx + 1} / ${o.flat.length}`;

    const map = o.sections.map((s) => `<div class="qmap-sec"><span>${esc(s.short)}</span><div class="qmap-dots">${s.questions.map((qq) => {
      const s2 = status(qq);
      const cls = { ok: 'is-ok', ok2: 'is-ok2', bad: 'is-bad', rev: 'is-rev', none: '' }[s2];
      const labels = { ok: 'решён с первой попытки', ok2: 'решён не с первой попытки', bad: 'есть ошибка', rev: 'ответ подсмотрен', none: 'не решён' };
      return `<button class="qdot ${cls} ${qq.index === view.idx ? 'is-cur' : ''}" data-act="jump" data-idx="${qq.index}" aria-label="Вопрос ${esc(qq.num)}: ${labels[s2]}" ${qq.index === view.idx ? 'aria-current="step"' : ''}>${esc(qq.num)}</button>`;
    }).join('')}</div></div>`).join('');

    let body = '';
    if (q.type === 'text') body += `<div class="stem">${textStemHTML(q, resp, r, locked, lastEvalFor(q))}</div>` + textHintsHTML(q, locked);
    else body += `<div class="stem">${q.stem}</div>`;
    if (q.instructions) body += `<p class="q-instr">${esc(q.instructions)}</p>`;
    if (q.note) body += `<p class="q-note">${q.note}</p>`;
    if (q.media) body += `<div class="cond-media">${q.media}</div>`;
    if (q.statements) body += statementsHTML(q, locked);
    switch (q.type) {
      case 'single': case 'multi': body += optionsHTML(q, resp, r, locked, lastEvalFor(q)); break;
      case 'match': body += matchHTML(q, resp, r, locked, lastEvalFor(q)); break;
      case 'table': body += tableHTML(q, resp, r, locked, lastEvalFor(q)); break;
      case 'terms': body += termsHTML(q, resp, r, locked, lastEvalFor(q)); break;
      default: break;
    }

    const solved = r && r.solved && !r.revealed;
    const actions = locked
      ? `<button class="btn btn-primary" data-act="next">${view.idx < o.flat.length - 1 || queue ? 'Следующий вопрос' : 'К итогам'}${I.next}</button>
         <button class="btn btn-ghost" data-act="retry">Решить заново</button>`
      : `<button class="btn btn-primary" data-act="check" id="check-btn">Проверить</button>
         <button class="btn btn-ghost" data-act="skip">Пропустить</button>
         <span class="grow"></span><span class="kbd-hint"><kbd>Enter</kbd> проверить · <kbd>←</kbd><kbd>→</kbd> листать</span>`;

    const yourStars = solved ? r.stars : 0;
    app.innerHTML = topbar(`<button class="btn btn-sm btn-ghost" data-act="home">${I.back}<span class="lbl">Олимпиады</span></button>`) + `<main class="wrap${enterCls()}" data-qid="${q.id}">
      <div class="qhead"><h2><b>${o.grade} класс</b> · ${esc(q.sec.title)}</h2>
        <div class="qhead-tools">
          <label class="switch" title="Разрешить открывать разбор и ответ до того, как ответишь">
            <input type="checkbox" role="switch" id="peek-switch" data-input="peek" ${store.settings.peek ? 'checked' : ''}>
            <span class="switch-track" aria-hidden="true"></span><span class="switch-lbl">Ответы сразу</span>
          </label>
          <span class="qcount tabnum">${counter}</span>
        </div>
      </div>
      <nav class="qmap" aria-label="Карта вопросов">${map}</nav>
      <article class="slide" id="slide" aria-labelledby="slide-num">
        <aside class="slide-label">
          <div class="slide-num" id="slide-num"><small>${q.sec.bonus ? 'бонус' : q.src === 'g8' && /^\d+$/.test(q.num) && q.type === 'single' ? 'тест' : 'вопрос'}</small>${esc(q.num)}</div>
          <div class="slide-stars" aria-label="Звёзды за вопрос: ${yourStars} из 3">${stars(yourStars)}</div>
          <div class="slide-kind">${KIND[q.type]}</div>
        </aside>
        <div class="slide-body">
          ${q.head && q.src === 'g8' ? `<p class="q-topic">${esc(q.head)}${q.topic ? ' · ' + esc(q.topic) : ''}</p>` : `<p class="q-topic">${esc(q.sec.short)}</p>`}
          ${body}
          <div class="actions">${actions}</div>
          <div id="fb" aria-live="polite">${feedbackHTML(q)}</div>
        </div>
      </article>
      ${drawerHTML(q)}
      <nav class="pager">
        <button class="btn btn-ghost" data-act="prev" ${view.idx === 0 && !queue ? 'disabled' : ''}>${I.back}Назад</button>
        <button class="btn btn-ghost" data-act="results" data-oid="${o.id}">Итоги · ★ ${st.stars}</button>
        <button class="btn btn-ghost" data-act="next">Вперёд${I.next}</button>
      </nav>
    </main>`;
    const cur = app.querySelector('.qdot.is-cur');
    const qmap = app.querySelector('.qmap');
    if (cur && qmap) {
      const a = cur.getBoundingClientRect(), b = qmap.getBoundingClientRect();
      qmap.scrollLeft += a.left - b.left - (b.width - a.width) / 2;
    }
    if (drawerOpen) fillDrawer(q, false);
  }
  const lastEvalFor = (q) => (lastEval && lastEval.qid === q.id ? lastEval : null);

  function feedbackHTML(q) {
    const r = rec(q);
    const ev = lastEvalFor(q);
    if (r && r.revealed) {
      return `<div class="feedback fb-info"><span class="fb-ico">${I.info}</span><div><h3>Ответ открыт</h3><p>Звёзд за этот вопрос не будет, зато теперь ты знаешь, как его решать. Нажми «Решить заново», чтобы закрепить.</p></div></div>`;
    }
    if (r && r.solved) {
      const praise = r.attempts === 1 ? (ev ? ev.praise : 'Решено с первой попытки.') : `Решено с ${r.attempts}-й попытки.`;
      return `<div class="feedback fb-ok"><span class="fb-ico">${I.check}</span><div><h3>Верно!<span class="fb-stars">${stars(r.stars)}</span></h3><p>${esc(praise)}${r.hinted ? ' Подсказка по буквам сняла одну звезду.' : ''} Загляни в разбор: там приёмы, которые пригодятся в похожих вопросах.</p>${ev && ev.notes.some(Boolean) ? `<ul>${ev.notes.filter(Boolean).map((n) => `<li>${esc(n.msg)}</li>`).join('')}</ul>` : ''}</div></div>`;
    }
    if (ev && !ev.filled) {
      return `<div class="feedback fb-info"><span class="fb-ico">${I.info}</span><div><h3>Сначала ответь</h3><p>${q.type === 'single' ? 'Выбери один вариант.' : 'Заполни хотя бы часть ответа.'}</p></div></div>`;
    }
    if (ev && !ev.ok) {
      let msg = '';
      const items = [];
      if (q.type === 'single') {
        msg = `Вариант «${esc(ev.resp)}» не подходит. Перечитай условие: часто всё решает одно слово.`;
        if (q.optionNotes && q.optionNotes[ev.resp]) items.push(q.optionNotes[ev.resp]);
      } else if (q.type === 'multi') {
        msg = `Верно отмечено ${ev.hit} из ${q.answer.length}.` + (ev.extra ? ` Лишних отметок: ${ev.extra} — они подсвечены красным.` : ' Каких-то верных суждений не хватает.');
      } else if (q.type === 'text' || q.type === 'terms') {
        msg = `Верно ${ev.right} из ${ev.total}. Красным отмечено то, что нужно исправить.`;
        if (q.type === 'text') ev.notes.forEach((n) => { if (n && n.cls === 'bad') items.push(n.msg); });
      } else {
        msg = `Совпало ${ev.right} из ${ev.total}. Красным отмечено то, что нужно исправить.`;
      }
      const tries = (r && r.attempts) || 1;
      return `<div class="feedback fb-bad"><span class="fb-ico">${I.cross}</span><div><h3>Пока неверно${tries > 1 ? ` · попытка ${tries}` : ''}</h3><p>${msg}</p>${items.length ? `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}<p style="margin-top:6px">Исправь и проверь ещё раз — или раскрой разбор ниже.</p></div></div>`;
    }
    return '';
  }

  function drawerHTML(q) {
    const r = rec(q);
    const can = canOpen(q);
    const done = !!(r && (r.solved || r.revealed));
    const sub = !can ? 'Откроется после первой попытки ответа (или включи «Ответы сразу»)'
      : done ? 'Почему так, где ловушка и как запомнить'
        : 'Покажет правильный ответ — звёзд за вопрос уже не будет';
    return `<section class="drawer ${drawerOpen && can ? 'is-open' : ''}" id="drawer">
      <button class="drawer-head" data-act="drawer" aria-expanded="${drawerOpen && can}" aria-controls="drawer-body" ${can ? '' : 'aria-disabled="true"'}>
        <span class="drawer-ico">${can ? I.book : I.lock}</span>
        <span class="drawer-title"><b>Подробный разбор</b><span>${sub}</span></span>
        ${I.chev}
      </button>
      <div class="drawer-body" id="drawer-body"><div class="drawer-clip"><div class="drawer-inner" id="drawer-inner"></div></div></div>
    </section>`;
  }

  const BLOCK_NAMES = { 'b-algo': 'Алгоритм', 'b-expl': 'Объяснение', 'b-traps': 'Ловушки', 'b-mem': 'Запомнить', 'b-viz': 'Схема', 'b-hor': 'Горизонт' };
  const BLOCK_COLORS = { 'b-algo': 'var(--c-blue)', 'b-expl': 'var(--muted)', 'b-traps': 'var(--c-orange)', 'b-mem': 'var(--c-violet)', 'b-viz': 'var(--c-green)', 'b-hor': 'var(--c-teal)' };
  function fillDrawer(q, animate) {
    const inner = document.getElementById('drawer-inner');
    if (!inner) return;
    const r = rec(q) || {};
    let your = '';
    if (q.type === 'single' && r.tried && r.tried.length) your = `<span class="your-answer">Твои неверные попытки: ${r.tried.map(esc).join(', ')}</span>`;
    let nav = '';
    if (q.src === 'g8') {
      const t = document.createElement('template'); t.innerHTML = q.explanation;
      const blocks = [...t.content.querySelectorAll('.blk')].map((b) => [...b.classList].find((c) => BLOCK_NAMES[c])).filter(Boolean);
      if (blocks.length > 2) nav = `<nav class="expl-nav" aria-label="Шаги разбора">${blocks.map((c) => `<button type="button" data-act="blk" data-blk="${c}" style="--nav-c:${BLOCK_COLORS[c]}">${BLOCK_NAMES[c]}</button>`).join('')}</nav>`;
    }
    inner.innerHTML = `<div class="answer-card"><span>Правильный ответ</span><div class="ans-body">${q.answerHtml || ''}</div>${your}</div>${nav}<div class="expl src-${q.src}">${q.explanation}</div>`;
    // подсветить в разборе вариант, который выбирала ученица
    (r.tried || []).forEach((k) => inner.querySelectorAll(`.expl [data-opt="${CSS.escape(k)}"]`).forEach((el) => el.classList.add('is-picked')));
    inner.querySelectorAll('.blk').forEach((b) => { const c = [...b.classList].find((x) => BLOCK_NAMES[x]); if (c) b.id = `${q.id}-${c}`; });
    inner.querySelectorAll('.expl img').forEach((img) => { img.loading = 'lazy'; });
    if (animate) {
      const d = document.getElementById('drawer');
      setTimeout(() => d.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' }), 120);
    }
  }

  function setDrawer(open) {
    const q = olymp().flat[view.idx];
    const d = document.getElementById('drawer');
    if (!d) return;
    if (!canOpen(q)) {
      d.classList.remove('shake'); void d.offsetWidth; d.classList.add('shake');
      toast('Сначала попробуй ответить — или включи «Ответы сразу» вверху');
      return;
    }
    const r = rec(q) || (store.answers[q.id] = { attempts: 0, solved: false, revealed: false, stars: 0, tried: [] });
    if (open && !r.solved && !r.revealed) {
      // открыть разбор до верного ответа = посмотреть ответ
      r.revealed = true; r.stars = 0; r.response = getResp(q); save();
      delete work[q.id];
      drawerOpen = false; lastEval = null;
      renderQuiz();
      drawerOpen = true;
      fillDrawer(q, true);
      const dd = document.getElementById('drawer');
      requestAnimationFrame(() => requestAnimationFrame(() => {
        dd.classList.add('is-open');
        dd.querySelector('.drawer-head').setAttribute('aria-expanded', 'true');
      }));
      return;
    }
    drawerOpen = open;
    const head = d.querySelector('.drawer-head');
    if (open) { fillDrawer(q, true); requestAnimationFrame(() => d.classList.add('is-open')); }
    else d.classList.remove('is-open');
    head.setAttribute('aria-expanded', String(open));
  }

  let toastTimer = 0;
  function toast(msg) {
    let t = document.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.textContent = msg;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.remove(), 2800);
  }

  const PRAISE = ['Точно в цель!', 'Отлично, ты ответила верно!', 'Блестяще — как настоящий олимпиадник!', 'Верно! Видно, что ты разобралась.', 'Именно так!'];

  function doCheck() {
    const o = olymp();
    const q = o.flat[view.idx];
    const resp = getResp(q);
    const ev = evaluate(q, resp);
    ev.qid = q.id; ev.resp = resp;
    if (!ev.filled) { lastEval = ev; renderQuiz(); return; }
    const r = store.answers[q.id] || (store.answers[q.id] = { attempts: 0, solved: false, revealed: false, stars: 0, tried: [] });
    r.attempts += 1;
    r.response = JSON.parse(JSON.stringify(resp));
    if (ev.ok) {
      r.solved = true;
      r.stars = r.revealed ? 0 : Math.max(1, 4 - r.attempts);
      r.hinted = hintUsed(q);
      if (r.hinted) r.stars = Math.min(r.stars, 2);
      ev.praise = pick(PRAISE);
    } else if (q.type === 'single' && !r.tried.includes(resp)) {
      r.tried.push(resp);
    }
    save();
    delete work[q.id];
    lastEval = ev;
    renderQuiz();
    const slide = document.getElementById('slide');
    if (ev.ok) {
      sfx.ok(); buzz(30);
      slide.classList.add('flash-ok');
      const b = slide.querySelector('.feedback') || slide;
      const rc = b.getBoundingClientRect();
      burst(rc.left + Math.min(60, rc.width / 2), rc.top + 20);
    } else {
      sfx.bad(); buzz([90, 60, 90]);
      slide.classList.add('shake', 'flash-bad');
      const fb = document.getElementById('fb');
      if (fb && fb.getBoundingClientRect().bottom > window.innerHeight) fb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function move(delta) {
    const o = olymp();
    lastEval = null; drawerOpen = false;
    if (view.queue) {
      const pos = view.queue.indexOf(view.idx);
      const np = pos + delta;
      if (np >= view.queue.length) return go({ screen: 'results', oid: o.id });
      if (np < 0) return;
      return go({ screen: 'quiz', oid: o.id, idx: view.queue[np] }, { push: false });
    }
    const ni = view.idx + delta;
    if (ni >= o.flat.length) return go({ screen: 'results', oid: o.id });
    if (ni < 0) return;
    go({ screen: 'quiz', oid: o.id, idx: ni }, { push: false });
  }

  // ------------------------------------------------------------ итоги
  function diplomaFor(st) {
    const p = st.max ? st.stars / st.max : 0;
    if (p >= 0.85) return { t: 'Диплом I степени', d: 'Почти всё с первой попытки. Так держат олимпиадную планку!' };
    if (p >= 0.7) return { t: 'Диплом II степени', d: 'Очень сильный результат. Пройди работу над ошибками — и до первой степени рукой подать.' };
    if (p >= 0.55) return { t: 'Диплом III степени', d: 'Хорошая база. Разборы и памятка ловушек помогут добрать баллы.' };
    return { t: 'Сертификат участника', d: 'Начало положено. Разборы, карточки и работа над ошибками быстро поднимут результат.' };
  }
  function renderResults() {
    const o = olymp();
    if (!o) return go({ screen: 'home' }, { push: false });
    const st = olympStats(o);
    const dip = diplomaFor(st);
    const finished = st.done === st.total;
    const todo = o.flat.filter((q) => status(q) !== 'ok');
    const rows = o.sections.map((s) => {
      const ss = olympStats(o, s.questions);
      return `<div class="bd-row"><span>${esc(s.short)}</span><div class="meter"><span class="m-ok" style="width:${(100 * ss.stars) / ss.max}%"></span></div><span class="tabnum">★ ${ss.stars}/${ss.max}</span></div>`;
    }).join('');
    const lbl = { ok2: 'не с первой попытки', bad: 'есть ошибка', rev: 'подсмотрено', none: 'не решён' };
    app.innerHTML = topbar(`<button class="btn btn-sm btn-ghost" data-act="home">${I.back}<span class="lbl">Олимпиады</span></button>`) + `<main class="wrap${enterCls()}">
      <div class="qhead"><h2><b>${o.grade} класс</b> · итоги</h2><span class="qcount">${st.done} из ${st.total} вопросов</span></div>
      <section class="diploma">
        <span class="kicker">${esc(o.stage)} · ${esc(o.year)} · ${o.grade} класс${finished ? '' : ' · промежуточный итог'}</span>
        ${I.seal}
        <h2>${dip.t}</h2>
        <div class="who"><label for="who-name">Вручается</label><input id="who-name" data-input="name" value="${esc(store.name || '')}" placeholder="впиши своё имя" autocomplete="given-name"></div>
        <div class="score"><span class="star">★</span> ${st.stars} из ${st.max} · с первой попытки ${st.ok} из ${st.total}</div>
        <p>${finished ? esc(dip.d) : `Осталось ответить на ${st.total - st.done} ${plural(st.total - st.done, 'вопрос', 'вопроса', 'вопросов')}. Диплом пересчитается по мере решения.`}</p>
      </section>
      <h3 class="section-title" style="font-size:1.25rem">По заданиям</h3>
      <div class="breakdown">${rows}</div>
      <div class="actions" style="margin-bottom:20px">
        ${todo.filter((q) => !q.sec.bonus).length ? `<button class="btn btn-primary" data-act="mistakes" data-oid="${o.id}">Работа над ошибками</button>` : ''}
        <button class="btn" data-act="notes" data-oid="${o.id}">Памятки и ключ ответов</button>
        <button class="btn btn-ghost" data-act="reset" data-oid="${o.id}">Начать олимпиаду заново</button>
      </div>
      ${todo.length ? `<h3 class="section-title" style="font-size:1.25rem">Стоит вернуться</h3><ul class="todo">${todo.map((q) => {
        const s2 = status(q);
        return `<li><button data-act="jump" data-idx="${q.index}"><span class="qdot ${{ ok2: 'is-ok2', bad: 'is-bad', rev: 'is-rev', none: '' }[s2]}">${esc(q.num)}</span><span>${esc(truncate(stripTags(q.stem).replace(/……/g, '…'), 90))}</span><small>${lbl[s2]}</small></button></li>`;
      }).join('')}</ul>` : ''}
    </main>`;
  }

  // ------------------------------------------------------------ памятки
  function renderNotes() {
    const o = olymp();
    if (!o) return go({ screen: 'home' }, { push: false });
    const id = view.noteId || o.notes[0].id;
    const n = o.notes.find((x) => x.id === id) || o.notes[0];
    const shown = view['spoil:' + n.id];
    app.innerHTML = topbar(`<button class="btn btn-sm btn-ghost" data-act="home">${I.back}<span class="lbl">Олимпиады</span></button>`) + `<main class="wrap${enterCls()}">
      <div class="qhead"><h2><b>${o.grade} класс</b> · памятки</h2><button class="btn btn-sm" data-act="open" data-oid="${o.id}">К вопросам${I.next}</button></div>
      <div class="tabs" role="tablist">${o.notes.map((x) => `<button class="tab" role="tab" id="tab-${x.id}" aria-selected="${x.id === n.id}" aria-controls="note-panel" data-act="note" data-note="${x.id}">${esc(x.title)}</button>`).join('')}</div>
      <article class="prose src-${o.id}" id="note-panel" role="tabpanel" aria-labelledby="tab-${n.id}">
        ${n.spoiler && !shown ? `<div class="spoiler"><b>${esc(n.title)}</b><p>Здесь все правильные ответы. Лучше открыть после того, как попробуешь решить сама.</p><button class="btn btn-primary" data-act="spoil" data-note="${n.id}">Показать ключ</button></div>` : n.html}
      </article>
    </main>`;
  }

  // ------------------------------------------------------------ карточки
  const deckState = {};
  function deckCards(deck) {
    const g8 = OLY.find((o) => o.id === 'g8');
    return deck === 'dict' ? g8.dictCards : g8.cards;
  }
  function renderCards() {
    const deck = view.deck === 'dict' ? 'dict' : 'self';
    const all = deckCards(deck);
    const ds = deckState[deck] || (deckState[deck] = { order: all.map((_, i) => i), pos: 0, flipped: false, known: 0 });
    const left = ds.order.length;
    const card = left ? all[ds.order[0]] : null;
    const title = deck === 'dict' ? 'Корни терминов' : 'Самопроверка';
    app.innerHTML = topbar(`<button class="btn btn-sm btn-ghost" data-act="home">${I.back}<span class="lbl">Главная</span></button>`) + `<main class="wrap${enterCls()}">
      <div class="qhead"><h2><b>Карточки</b> · ${title}</h2><span class="qcount tabnum">знаю ${ds.known} из ${all.length}</span></div>
      <div class="deck-bar tabs" role="tablist">
        <button class="tab" role="tab" aria-selected="${deck === 'self'}" data-act="cards" data-deck="self">Самопроверка · ${deckCards('self').length}</button>
        <button class="tab" role="tab" aria-selected="${deck === 'dict'}" data-act="cards" data-deck="dict">Корни терминов · ${deckCards('dict').length}</button>
        <span class="topbar-spacer"></span>
        <button class="btn btn-sm btn-ghost" data-act="shuffle">Перемешать</button>
      </div>
      ${card ? `<div class="flip-stage">
        <button class="flip ${ds.flipped ? 'is-flipped' : ''}" data-act="flip" aria-label="Перевернуть карточку">
          <span class="flip-face flip-front"><span class="fl-tag">${deck === 'dict' ? 'термин' : 'вопрос'} · нажми, чтобы перевернуть</span><span class="fl-main">${card.front}</span></span>
          <span class="flip-face flip-back" aria-hidden="${!ds.flipped}"><span class="fl-tag">${deck === 'dict' ? 'корни и перевод' : 'ответ'}</span><span>${card.back}</span></span>
        </button>
      </div>
      <div class="deck-controls">
        <button class="btn" data-act="again">Повторить позже</button>
        <button class="btn btn-ok" data-act="know">${I.check.replace('<svg', '<svg class="ico"')}Знаю</button>
      </div>
      <p class="deck-progress">В колоде осталось ${left} · <kbd>пробел</kbd> переворачивает</p>`
      : `<div class="spoiler"><b>Колода пройдена!</b><p>Все ${all.length} ${plural(all.length, 'карточка', 'карточки', 'карточек')} — в копилке. Можно пройти ещё раз вперемешку.</p><button class="btn btn-primary" data-act="restart-deck">Пройти ещё раз</button></div>`}
    </main>`;
  }

  // ------------------------------------------------------------ рендер
  function render() {
    switch (view.screen) {
      case 'quiz': renderQuiz(); break;
      case 'results': renderResults(); break;
      case 'notes': renderNotes(); break;
      case 'cards': renderCards(); break;
      default: renderHome();
    }
  }

  // ------------------------------------------------------------ события
  const resetArm = {};
  app.addEventListener('click', (e) => {
    const img = e.target.closest('.cond-media img');
    if (img) { openLightbox(img); return; }
    const el = e.target.closest('[data-act]');
    if (!el || el.disabled) return;
    const act = el.dataset.act;
    const o = view.oid ? olymp() : null;
    switch (act) {
      case 'home': lastEval = null; drawerOpen = false; go({ screen: 'home' }); break;
      case 'open': {
        const oid = el.dataset.oid;
        lastEval = null; drawerOpen = false;
        go({ screen: 'quiz', oid, idx: store.last[oid] || 0, queue: null });
        break;
      }
      case 'mistakes': {
        const oo = OLY.find((x) => x.id === el.dataset.oid);
        const queue = oo.main.filter((q) => ['bad', 'rev', 'ok2'].includes(status(q))).map((q) => q.index);
        if (!queue.length) { toast('Ошибок нет: всё решено с первой попытки!'); break; }
        // в работе над ошибками вопрос решается заново (звёзды можно вернуть);
        // старый результат стирается, только когда ученица до него дошла
        queue.fresh = new Set(queue);
        lastEval = null; drawerOpen = false;
        go({ screen: 'quiz', oid: oo.id, idx: queue[0], queue });
        break;
      }
      case 'results': lastEval = null; drawerOpen = false; go({ screen: 'results', oid: el.dataset.oid || view.oid }); break;
      case 'notes': go({ screen: 'notes', oid: el.dataset.oid }); break;
      case 'note': view.noteId = el.dataset.note; renderNotes(); break;
      case 'spoil': view['spoil:' + el.dataset.note] = true; renderNotes(); break;
      case 'cards': go({ screen: 'cards', deck: el.dataset.deck }); break;
      case 'goto': {
        const q = byId[el.dataset.qid];
        lastEval = null; drawerOpen = false;
        go({ screen: 'quiz', oid: q.olymp.id, idx: q.index, queue: null });
        break;
      }
      case 'fact': factIdx = (factIdx + 1 + Math.floor(Math.random() * 7)) % facts().length; renderHome(); document.querySelector('.fact')?.scrollIntoView({ block: 'nearest' }); break;
      case 'sound': store.settings.sound = !store.settings.sound; save(); render(); if (store.settings.sound) sfx.tick(); break;
      case 'theme': {
        const order = ['', 'dark', 'light'];
        const nx = order[(order.indexOf(store.settings.theme || '') + 1) % order.length];
        store.settings.theme = nx; save();
        if (nx) document.documentElement.setAttribute('data-theme', nx); else document.documentElement.removeAttribute('data-theme');
        render();
        toast(nx === 'dark' ? 'Тёмная тема' : nx === 'light' ? 'Светлая тема' : 'Тема как в системе');
        break;
      }
      case 'jump': {
        lastEval = null; drawerOpen = false;
        const idx = +el.dataset.idx;
        const keepQueue = view.queue && view.queue.includes(idx) ? view.queue : null;
        go({ screen: 'quiz', oid: view.oid, idx, queue: keepQueue }, { push: view.screen !== 'quiz' });
        break;
      }
      case 'check': doCheck(); break;
      case 'skip': move(1); break;
      case 'next': move(1); break;
      case 'prev': move(-1); break;
      case 'retry': {
        clearQuestion(o.flat[view.idx]);
        save(); lastEval = null; drawerOpen = false; renderQuiz();
        break;
      }
      case 'hint': {
        const q = o.flat[view.idx];
        const i = +el.dataset.i;
        const spec = q.type === 'text' ? q.blanks[i] : q.items[i];
        const h = store.hints[q.id] || (store.hints[q.id] = {});
        h[i] = Math.min(hintMax(spec.word), (h[i] || 0) + 1);
        save(); sfx.tick();
        renderQuiz();
        const input = document.getElementById(q.type === 'text' ? `blank-${q.id}-${i}` : `term-${q.id}-${i}`);
        (app.querySelector(`.hint-btn[data-i="${i}"]`) || input)?.focus({ preventScroll: true });
        break;
      }
      case 'drawer': {
        const d = document.getElementById('drawer');
        setDrawer(!d.classList.contains('is-open'));
        break;
      }
      case 'blk': {
        const q = o.flat[view.idx];
        const t = document.getElementById(`${q.id}-${el.dataset.blk}`);
        if (t) t.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
        break;
      }
      case 'stmt': {
        const q = o.flat[view.idx];
        const k = el.dataset.key;
        const cur = work['stmt:' + q.id] || [];
        work['stmt:' + q.id] = cur.includes(k) ? cur.filter((x) => x !== k) : [...cur, k].sort((a, b) => a - b);
        refreshOptions(q);
        break;
      }
      case 'seg': {
        const q = o.flat[view.idx];
        const resp = getResp(q);
        resp[el.dataset.row] = el.dataset.val;
        work[q.id] = resp;
        el.parentElement.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b === el)));
        const row = el.closest('.match-row'); if (row) row.classList.remove('is-wrong', 'is-right');
        break;
      }
      case 'reset': {
        const oid = el.dataset.oid;
        if (!resetArm[oid]) {
          resetArm[oid] = true;
          el.textContent = 'Точно сбросить? Нажми ещё раз';
          setTimeout(() => { resetArm[oid] = false; if (el.isConnected) el.textContent = 'Начать олимпиаду заново'; }, 3500);
          break;
        }
        resetArm[oid] = false;
        const oo = OLY.find((x) => x.id === oid);
        oo.flat.forEach(clearQuestion);
        store.last[oid] = 0; save();
        toast('Прогресс олимпиады сброшен');
        go({ screen: 'quiz', oid, idx: 0, queue: null });
        break;
      }
      case 'flip': {
        const ds = deckState[view.deck === 'dict' ? 'dict' : 'self'];
        ds.flipped = !ds.flipped;
        el.classList.toggle('is-flipped', ds.flipped);
        el.querySelector('.flip-back').setAttribute('aria-hidden', String(!ds.flipped));
        sfx.tick();
        break;
      }
      case 'know': case 'again': {
        const ds = deckState[view.deck === 'dict' ? 'dict' : 'self'];
        const first = ds.order.shift();
        if (act === 'again') ds.order.push(first); else ds.known++;
        ds.flipped = false;
        if (act === 'know') { sfx.ok(); if (!ds.order.length) { const rc = el.getBoundingClientRect(); burst(rc.left + rc.width / 2, rc.top); } }
        renderCards();
        break;
      }
      case 'shuffle': case 'restart-deck': {
        const deck = view.deck === 'dict' ? 'dict' : 'self';
        const all = deckCards(deck);
        const order = all.map((_, i) => i);
        for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
        deckState[deck] = { order, pos: 0, flipped: false, known: 0 };
        renderCards();
        break;
      }
      default: break;
    }
  });

  function refreshOptions(q) {
    const r = rec(q);
    const locked = !!(r && (r.solved || r.revealed));
    const fs = app.querySelector('.options');
    if (fs) fs.outerHTML = optionsHTML(q, getResp(q), r, locked, lastEvalFor(q));
    app.querySelectorAll('.stmt').forEach((b) => b.setAttribute('aria-pressed', String((work['stmt:' + q.id] || []).includes(b.dataset.key))));
  }

  app.addEventListener('change', (e) => {
    const el = e.target;
    if (!el.dataset || !el.dataset.input || view.screen !== 'quiz') return;
    if (el.dataset.input === 'peek') {
      store.settings.peek = el.checked; save();
      renderQuiz();
      document.getElementById('peek-switch')?.focus({ preventScroll: true });
      toast(el.checked ? 'Ответы сразу: разбор можно открыть до ответа (без звёзд за вопрос)' : 'Разбор снова открывается после первой попытки');
      return;
    }
    const q = olymp().flat[view.idx];
    const resp = getResp(q);
    switch (el.dataset.input) {
      case 'opt':
        if (q.type === 'multi') {
          const set = new Set(resp); el.checked ? set.add(el.value) : set.delete(el.value);
          work[q.id] = [...set].sort((a, b) => a - b);
        } else work[q.id] = el.value;
        if (lastEvalFor(q)) {
          lastEval = null; refreshOptions(q); document.getElementById('fb').innerHTML = '';
          app.querySelector(`.opt[data-key="${CSS.escape(el.value)}"] input`)?.focus();
        }
        break;
      case 'match':
        resp[el.dataset.row] = el.value; work[q.id] = resp;
        el.classList.toggle('is-filled', !!el.value);
        el.closest('.match-row')?.classList.remove('is-wrong', 'is-right');
        break;
      case 'cell': {
        const row = resp[el.dataset.row] || (resp[el.dataset.row] = {});
        row[el.dataset.col] = el.value; work[q.id] = resp;
        el.classList.toggle('is-filled', !!el.value);
        el.closest('td')?.classList.remove('is-wrong', 'is-right');
        break;
      }
      default: break;
    }
  });
  app.addEventListener('input', (e) => {
    const el = e.target;
    if (!el.dataset) return;
    if (el.dataset.input === 'name') { store.name = el.value.slice(0, 60); save(); return; }
    if (view.screen !== 'quiz') return;
    if (el.dataset.input === 'blank' || el.dataset.input === 'term') {
      const q = olymp().flat[view.idx];
      const resp = getResp(q);
      resp[+el.dataset.i] = el.value;
      work[q.id] = resp;
      el.classList.remove('is-wrong', 'is-right');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target.tagName || '').toLowerCase();
    const typing = tag === 'input' || tag === 'textarea' || tag === 'select';
    if (document.querySelector('.lightbox') && e.key === 'Escape') { document.querySelector('.lightbox').remove(); return; }
    if (view.screen === 'cards' && !typing) {
      if (e.key === ' ' || e.key === 'Enter') { const f = app.querySelector('.flip'); if (f && e.target !== f) { e.preventDefault(); f.click(); } }
      if (e.key === 'ArrowRight') app.querySelector('[data-act="know"]')?.click();
      if (e.key === 'ArrowLeft') app.querySelector('[data-act="again"]')?.click();
      return;
    }
    if (view.screen !== 'quiz') return;
    const q = olymp().flat[view.idx];
    const r = rec(q);
    const locked = !!(r && (r.solved || r.revealed));
    if (e.key === 'Enter' && (tag === 'input' || !typing)) {
      if (tag === 'button' || tag === 'a' || tag === 'summary' || e.target.type === 'checkbox' && e.target.id === 'peek-switch') return;
      e.preventDefault();
      if (locked) move(1); else doCheck();
      return;
    }
    if (typing) return;
    if (e.key === 'ArrowRight') { move(1); return; }
    if (e.key === 'ArrowLeft') { move(-1); return; }
    if ((q.type === 'single' || q.type === 'multi') && !locked) {
      const k = e.key.toLowerCase();
      const opt = q.options.find((x) => x.key.toLowerCase() === k) || (/^[1-9]$/.test(k) && q.type === 'single' ? q.options[+k - 1] : null);
      if (opt) {
        const input = app.querySelector(`.opt[data-key="${CSS.escape(opt.key)}"] input`);
        if (input) { input.click(); input.focus(); }
      }
    }
  });

  function openLightbox(img) {
    const lb = document.createElement('button');
    lb.className = 'lightbox'; lb.type = 'button'; lb.setAttribute('aria-label', 'Закрыть увеличенный рисунок');
    lb.innerHTML = `<img src="${img.getAttribute('src')}" alt="">`;
    lb.addEventListener('click', () => lb.remove());
    document.body.appendChild(lb);
    lb.focus();
  }

  // ------------------------------------------------------------ старт
  const start = parseToken(location.hash);
  Object.assign(view, start);
  render();
  entering = false;
  try { history.replaceState({ tk: token() }, '', token() ? '#' + token() : location.pathname + location.search); } catch (e) { /* ничего */ }
})();
