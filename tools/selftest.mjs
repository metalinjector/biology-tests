// Самопроверка тренажёра в настоящем браузере (Playwright + Chromium).
//
//   python3 -m http.server 8765 &        # из корня репозитория
//   node tools/selftest.mjs [http://localhost:8765/index.html] [папка-для-скриншотов]
//
// Что проверяется:
//  1. каждый вопрос обеих олимпиад решается через интерфейс эталонным ответом
//     и получает «Верно!» с тремя звёздами (ключи и проверка согласованы);
//  2. неверный ответ подаёт сигнал (красный отклик, тряска), разбор открывается
//     после попытки и показывает правильный ответ и все рисунки из исходника;
//  3. все картинки загружаются, нет ошибок в консоли, на ширине телефона
//     страница не прокручивается вбок; работают карточки, памятки и итоги.
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch {
  const globalRoot = execSync('npm root -g').toString().trim();
  ({ chromium } = require(path.join(globalRoot, 'playwright')));
}

const URL = process.argv[2] || 'http://localhost:8765/index.html';
const SHOTS = process.argv[3] || '';
if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });

const exe = fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined;
const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const problems = [];
const fail = (m) => { problems.push(m); console.log('  ✗ ' + m); };

async function newPage(opts = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, ...opts });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => fail('ошибка JS: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error' && !/fonts\.g/.test(m.text())) fail('console.error: ' + m.text()); });
  return { ctx, page };
}

const shot = async (page, name) => { if (SHOTS) await page.screenshot({ path: path.join(SHOTS, name + '.png'), fullPage: false }); };

// --------------------------------------------------------------- 1. все вопросы — эталонными ответами
{
  const { page } = await newPage();
  await page.goto(URL);
  await page.waitForSelector('.olymp-card');
  const data = await page.evaluate(() => window.OLYMPIAD_DATA.olympiads.map((o) => ({
    id: o.id,
    qs: o.sections.flatMap((s) => s.questions.map((q) => ({
      id: q.id, type: q.type, answer: q.answer, num: q.num,
      blanks: q.blanks ? q.blanks.length : 0, items: q.items ? q.items.length : 0,
      answerText: q.answerHtml.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(),
      rows: q.rows ? q.rows.map((r) => r.key) : null, cols: q.columns ? q.columns.map((c) => c.key) : null,
      style: q.style || '', svg: (q.explanation.match(/<svg/g) || []).length,
    }))),
  })));
  let total = 0;
  for (const o of data) {
    console.log(`Олимпиада ${o.id}: ${o.qs.length} вопросов`);
    await page.evaluate((oid) => { location.hash = oid + '-q1'; }, o.id);
    await page.reload();
    for (let i = 0; i < o.qs.length; i++) {
      const q = o.qs[i];
      if (i > 0) await page.click(`.qdot[data-idx="${i}"]`);
      await page.waitForSelector(`main[data-qid="${q.id}"]`);
      switch (q.type) {
        case 'single':
          await page.click(`.opt[data-key="${q.answer}"] .opt-card`);
          break;
        case 'multi':
          for (const k of q.answer) await page.click(`.opt[data-key="${k}"] .opt-card`);
          break;
        case 'text': {
          const words = q.answerText.split(';').map((w) => w.replace(/\.$/, '').trim());
          for (let b = 0; b < q.blanks; b++) await page.fill(`#blank-${q.id}-${b}`, words[b]);
          break;
        }
        case 'terms': {
          const found = [...q.answerText.matchAll(/(\d+) — (.*?)(?:;|\.$|$)/g)].map((m) => m[2].replace(/\s*\(.*?\)/, '').trim());
          for (let b = 0; b < q.items; b++) await page.fill(`#term-${q.id}-${b}`, found[b]);
          break;
        }
        case 'match':
          for (const [k, v] of Object.entries(q.answer)) {
            if (q.style === 'segmented') await page.click(`.seg button[data-row="${k}"][data-val="${v}"]`);
            else await page.selectOption(`select[data-row="${k}"]`, v);
          }
          break;
        case 'table':
          for (const r of q.rows) for (const c of q.cols) {
            await page.selectOption(`select[data-row="${r}"][data-col="${c}"]`, { label: q.answer[r][c] });
          }
          break;
        default: fail('неизвестный тип ' + q.type);
      }
      await page.click('#check-btn');
      const ok = await page.waitForSelector('.feedback.fb-ok', { timeout: 3000 }).then(() => true).catch(() => false);
      if (!ok) { fail(`${q.id} (№${q.num}): эталонный ответ не принят`); await shot(page, 'fail-' + q.id); continue; }
      const st = await page.locator('.slide-stars span:not(.off)').count();
      if (st !== 3) fail(`${q.id}: ожидалось 3 звезды, а их ${st}`);
      // разбор: правильный ответ + все рисунки
      await page.click('.drawer-head');
      await page.waitForSelector('.drawer.is-open .answer-card');
      const svgs = await page.locator('#drawer-inner .expl svg').count();
      if (svgs !== q.svg) fail(`${q.id}: в разборе ${svgs} рисунков вместо ${q.svg}`);
      total++;
    }
  }
  console.log(`  решено эталонными ответами, вопросов: ${total}`);
  await page.goto(URL.replace(/#.*/, '') + '#g7-itogi');
  await page.reload();
  await page.waitForSelector('.diploma');
  const dip = await page.textContent('.diploma h2');
  if (!/I степени/.test(dip)) fail('после идеального прохождения 7 класса ожидался диплом I степени, а не ' + dip);
  await shot(page, 'results-g7');
}

// --------------------------------------------------------------- 2. ошибка → сигнал → разбор
{
  const { page } = await newPage();
  await page.goto(URL.replace(/#.*/, '') + '#g7-q1');
  await page.reload();
  await page.waitForSelector('main[data-qid="g7-p1-s1-q1"]');
  await page.click('.drawer-head', { force: true }); // кнопка помечена aria-disabled: должна лишь «тряхнуть»
  await page.waitForTimeout(200);
  if (await page.locator('.drawer.is-open').count()) fail('разбор открылся до первой попытки');
  if (!(await page.locator('.toast').count())) fail('нет подсказки, что разбор откроется после попытки');
  await page.click('.opt[data-key="Г"] .opt-card'); // «отдел» — классическая ловушка
  await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  if (!(await page.locator('#slide.shake').count())) fail('нет тряски при неверном ответе');
  if (!(await page.locator('.opt.is-wrong[data-key="Г"]').count())) fail('неверный вариант не подсвечен');
  await shot(page, 'quiz-wrong');
  await page.click('.drawer-head');
  await page.waitForSelector('.drawer.is-open .answer-card');
  await page.waitForTimeout(700);
  const ans = await page.textContent('.answer-card .ans-body');
  if (!/Б\) класс/.test(ans)) fail('в карточке ответа нет «Б) класс»: ' + ans);
  if (!(await page.locator('#drawer-inner tr.is-picked[data-opt="Г"]').count())) fail('в разборе не отмечен выбранный вариант');
  if (!(await page.locator('.opt.is-right[data-key="Б"], .opt.is-missed[data-key="Б"]').count())) fail('после раскрытия не показан верный вариант');
  await shot(page, 'quiz-drawer');

  // текст: подсказка на бытовое слово
  await page.goto(URL.replace(/#.*/, '') + '#g7-q26');
  await page.reload();
  await page.waitForSelector('main[data-qid="g7-p2-s2-q1"]');
  await page.fill('#blank-g7-p2-s2-q1-0', 'главным');
  await page.fill('#blank-g7-p2-s2-q1-1', 'придаток');
  await page.press('#blank-g7-p2-s2-q1-1', 'Enter');
  await page.waitForSelector('.feedback.fb-bad');
  const fbt = await page.textContent('.feedback');
  if (!/бытовое слово/.test(fbt)) fail('нет подсказки про слово «придаток»');
  if (!(await page.locator('.blank.is-right').count()) || !(await page.locator('.blank.is-wrong').count())) fail('пропуски не размечены верно/неверно');

  // таблица соцветий: частично верно
  await page.goto(URL.replace(/#.*/, '') + '#g7-q34');
  await page.reload();
  await page.waitForSelector('main[data-qid="g7-p2-s4-q1"]');
  await page.selectOption('select[data-row="1"][data-col="name"]', { label: 'колос' });
  await page.selectOption('select[data-row="2"][data-col="name"]', { label: 'колос' });
  await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  if (!(await page.locator('td.is-wrong').count()) || !(await page.locator('td.is-right').count())) fail('клетки таблицы не размечены');
  await shot(page, 'quiz-table');

  // картинки из условий
  for (const n of [23, 33, 34]) {
    await page.goto(URL.replace(/#.*/, '') + '#g7-q' + n);
    await page.reload();
    await page.waitForSelector('.cond-media img');
    const okImg = await page.$eval('.cond-media img', (img) => img.complete && img.naturalWidth > 100);
    if (!okImg) fail('не загрузилась картинка в вопросе ' + n);
  }
}

// --------------------------------------------------------------- 3. телефон, тёмная тема, карточки, памятки
{
  const { page } = await newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, colorScheme: 'dark' });
  const routes = ['', '#g7-q1', '#g7-q22', '#g7-q34', '#g7-q35', '#g8-q2', '#g8-q25', '#g8-q26', '#g7-pamyatki', '#g8-pamyatki', '#kartochki-self', '#g8-itogi'];
  for (const r of routes) {
    await page.goto(URL.replace(/#.*/, '') + r);
    await page.reload();
    await page.waitForSelector('main');
    await page.waitForTimeout(150);
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    if (over > 1) fail(`горизонтальная прокрутка на телефоне (${r || 'главная'}): +${over}px`);
    if (r === '' || r === '#g8-q25' || r === '#g7-q34') await shot(page, 'mobile-dark' + (r || '-home').replace('#', '-'));
  }
  // открыть разбор 8 класса на телефоне
  await page.goto(URL.replace(/#.*/, '') + '#g8-q3');
  await page.reload();
  await page.waitForSelector('main[data-qid="g8-q3"]');
  await page.click('.opt[data-key="а"] .opt-card');
  await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  await page.click('.drawer-head');
  await page.waitForSelector('.drawer.is-open .expl-nav');
  await page.waitForTimeout(800);
  const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (over > 1) fail(`горизонтальная прокрутка в открытом разборе на телефоне: +${over}px`);
  await shot(page, 'mobile-dark-drawer');

  // карточки
  await page.goto(URL.replace(/#.*/, '') + '#kartochki-dict');
  await page.reload();
  await page.waitForSelector('.flip');
  await page.click('.flip');
  await page.waitForTimeout(800);
  if (!(await page.locator('.flip.is-flipped').count())) fail('карточка не переворачивается');
  await shot(page, 'mobile-cards');
  // памятки: ключ под спойлером
  await page.goto(URL.replace(/#.*/, '') + '#g8-pamyatki');
  await page.reload();
  await page.click('.tab:has-text("Ключ ответов")');
  if (!(await page.locator('.spoiler').count())) fail('ключ ответов не спрятан под спойлер');
  await page.click('[data-act="spoil"]');
  if (!(await page.locator('.keygrid').count())) fail('ключ ответов не открылся');
}

// --------------------------------------------------------------- 4. главная на компьютере
{
  const { page } = await newPage({ colorScheme: 'light' });
  await page.goto(URL.replace(/#.*/, ''));
  await page.waitForSelector('.olymp-card');
  await page.waitForTimeout(400);
  await shot(page, 'desktop-home');
  await page.goto(URL.replace(/#.*/, '') + '#g8-q1');
  await page.reload();
  await page.waitForSelector('main[data-qid="g8-q1"]');
  await page.click('.opt[data-key="1"] .opt-card');
  await page.click('.opt[data-key="2"] .opt-card');
  await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  const t = await page.textContent('.feedback');
  if (!/Верно отмечено 1 из 4/.test(t)) fail('неверный подсчёт в задании с несколькими ответами: ' + t);
  await page.click('.drawer-head');
  await page.waitForSelector('.drawer.is-open');
  await page.waitForTimeout(700);
  await shot(page, 'desktop-g8-drawer');
}

// --------------------------------------------------------------- 5. звёзды, «подсмотрела», работа над ошибками
{
  const { page } = await newPage();
  const go = async (h) => { await page.goto(URL.replace(/#.*/, '') + h); await page.reload(); await page.waitForSelector('main'); };
  await go('#g7-q3'); // муреин: сначала ошибка, потом верно → 2 звезды
  await page.click('.opt[data-key="В"] .opt-card'); await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  await page.click('.opt[data-key="Б"] .opt-card'); await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-ok');
  let n = await page.locator('.slide-stars span:not(.off)').count();
  if (n !== 2) fail('со второй попытки ожидалось 2 звезды, а их ' + n);
  if (!(await page.locator('.opt.is-tried[data-key="В"]').count())) fail('неудачная попытка не зачёркнута');
  await go('#g7-q4'); // открыть разбор после ошибки → ответ подсмотрен, 0 звёзд
  await page.click('.opt[data-key="А"] .opt-card'); await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-bad');
  await page.click('.drawer-head');
  await page.waitForSelector('.feedback.fb-info');
  n = await page.locator('.slide-stars span:not(.off)').count();
  if (n !== 0) fail('после раскрытия ответа должно быть 0 звёзд, а их ' + n);
  await go('');
  await page.waitForSelector('[data-act="mistakes"][data-oid="g7"]');
  const label = await page.textContent('[data-act="mistakes"][data-oid="g7"]');
  if (!/· 2/.test(label)) fail('на главной ожидалось 2 вопроса для работы над ошибками: ' + label);
  await page.click('[data-act="mistakes"][data-oid="g7"]');
  await page.waitForSelector('main[data-qid="g7-p1-s1-q3"]');
  if (!/Работа над ошибками · 1 \/ 2/.test(await page.textContent('.qcount'))) fail('счётчик работы над ошибками неверный');
  await page.click('.opt[data-key="Б"] .opt-card'); await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-ok');
  n = await page.locator('.slide-stars span:not(.off)').count();
  if (n !== 3) fail('в работе над ошибками звёзды не вернулись: ' + n);
  await page.click('[data-act="next"].btn-primary');
  await page.waitForSelector('main[data-qid="g7-p1-s1-q4"]');
  await page.click('.opt[data-key="Б"] .opt-card'); await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-ok');
  await page.click('[data-act="next"].btn-primary');
  await page.waitForSelector('.diploma');
  const stars = await page.textContent('.diploma .score');
  if (!/6 из 105/.test(stars)) fail('после работы над ошибками ожидалось 6 звёзд: ' + stars);
}

// --------------------------------------------------------------- 6. подсказка по буквам и «Ответы сразу»
{
  const { page } = await newPage();
  const go = async (h) => { await page.goto(URL.replace(/#.*/, '') + h); await page.reload(); await page.waitForSelector('main'); };
  await go('#g7-q26'); // главным; придаточным
  if ((await page.locator('.hint-btn').count()) !== 2) fail('у двух пропусков должно быть две кнопки подсказки');
  const labels = [];
  for (let k = 0; k < 4; k++) {
    const btn = page.locator('.hint-btn[data-i="0"]');
    if (!(await btn.count())) break;
    labels.push((await btn.textContent()).trim());
    await btn.click();
  }
  const want = ['Показать первую букву', 'Показать вторую букву', 'Показать третью букву'];
  if (JSON.stringify(labels) !== JSON.stringify(want)) fail('кнопки подсказки: ' + JSON.stringify(labels));
  if (!(await page.locator('.hint-end').count())) fail('после трёх букв нет надписи «Больше подсказок нет»');
  const ph = await page.getAttribute('#blank-g7-p2-s2-q1-0', 'placeholder');
  if (ph !== 'гла…') fail('подсказка в поле: ' + ph);
  if (!/«гла…»/.test(await page.textContent('.hint-letters'))) fail('не показаны открытые буквы');
  await page.fill('#blank-g7-p2-s2-q1-0', 'главным');
  await page.fill('#blank-g7-p2-s2-q1-1', 'придаточным');
  await page.click('#check-btn');
  await page.waitForSelector('.feedback.fb-ok');
  let n = await page.locator('.slide-stars span:not(.off)').count();
  if (n !== 2) fail('с подсказкой ожидалось 2 звезды, а их ' + n);
  if (await page.locator('.hint-btn').count()) fail('после верного ответа кнопки подсказок должны исчезнуть');
  await go('#g7-q29'); // «лист»: максимум три буквы, слово целиком не раскрывается
  for (let k = 0; k < 3; k++) await page.click('.hint-btn[data-i="0"]');
  if (await page.getAttribute('#blank-g7-p2-s2-q4-0', 'placeholder') !== 'лис…') fail('подсказка для «лист»');
  await go('#g8-q2');
  if ((await page.locator('.hint-btn').count()) !== 10) fail('у каждого из 10 терминов должна быть подсказка');
  await page.click('.hint-btn[data-i="7"]');
  if (await page.getAttribute('#term-g8-q2-7', 'placeholder') !== 'п…') fail('подсказка у термина 8');

  // «Ответы сразу»
  await go('#g7-q2');
  if (!(await page.locator('.drawer-head[aria-disabled="true"]').count())) fail('без переключателя разбор должен быть закрыт до попытки');
  await page.click('label.switch');
  await page.waitForSelector('#peek-switch:checked');
  if (await page.locator('.drawer-head[aria-disabled="true"]').count()) fail('переключатель не открыл доступ к разбору');
  await page.click('.drawer-head');
  await page.waitForSelector('.drawer.is-open .answer-card');
  if (!/Б\) пеницилл/.test(await page.textContent('.answer-card'))) fail('в учебном режиме не показан ответ');
  await page.waitForSelector('.feedback.fb-info');
  n = await page.locator('.slide-stars span:not(.off)').count();
  if (n !== 0) fail('ответ, открытый до попытки, не должен давать звёзд');
  await go('#g7-q5'); // настройка запоминается
  if (!(await page.locator('#peek-switch:checked').count())) fail('переключатель не сохранился');
  await page.click('label.switch');
  await page.waitForSelector('.drawer-head[aria-disabled="true"]');
  await shot(page, 'peek-off');
}

await browser.close();
if (problems.length) {
  console.log(`\nНайдено проблем: ${problems.length}`);
  process.exit(1);
}
console.log('\nВсё в порядке: проблем не найдено.');
