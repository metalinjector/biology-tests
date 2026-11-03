# Пакет для внешней проверки тренажёра «Олимпиада под микроскопом»

Все 203 вопросов шести олимпиад в обычных текстовых файлах — без архивов и без JavaScript. Файлы можно прикладывать к чату с любым ИИ по одному или давать ссылки на них.

## Файлы

| Файл | Олимпиада | Вопросов |
|---|---|---|
| [7-klass-gorodskoy-2014-2015.md](7-klass-gorodskoy-2014-2015.md) | Олимпиада 7 класса — Городской этап · 2014/2015 · теоретическая часть | 35 |
| [8-klass-shkolny-2016-2017-1.md](8-klass-shkolny-2016-2017-1.md) | Олимпиада 8 класса — Школьный этап · 2016/2017 · 25 заданий, 43 вопроса | 29 |
| [8-klass-shkolny-2016-2017-2.md](8-klass-shkolny-2016-2017-2.md) | Олимпиада 8 класса — Школьный этап · 2016/2017 · 25 заданий, 43 вопроса | 29 |
| [8-klass-2018-2019-1.md](8-klass-2018-2019-1.md) | Олимпиада 8 класса, 2018/2019 — Олимпиада · 2018/2019 · 29 тестов и 3 практических задания | 36 |
| [8-klass-2018-2019-2.md](8-klass-2018-2019-2.md) | Олимпиада 8 класса, 2018/2019 — Олимпиада · 2018/2019 · 29 тестов и 3 практических задания | 36 |
| [8-klass-2018-2019-3.md](8-klass-2018-2019-3.md) | Олимпиада 8 класса, 2018/2019 — Олимпиада · 2018/2019 · 29 тестов и 3 практических задания | 36 |
| [8-klass-rayonny-2019-brest.md](8-klass-rayonny-2019-brest.md) | Районный этап 2019, 8 класс — Районный этап · 2019 · 14 тестов, 15 вопросов по рисункам, 11 суждений | 21 |
| [8-klass-2016-avtorsky-razbor-1.md](8-klass-2016-avtorsky-razbor-1.md) | Олимпиада 8 класса, 2016 — Олимпиадные задания · 2016 · 30 тестов, рисунки, задачи и «исключения» | 40 |
| [8-klass-2016-avtorsky-razbor-2.md](8-klass-2016-avtorsky-razbor-2.md) | Олимпиада 8 класса, 2016 — Олимпиадные задания · 2016 · 30 тестов, рисунки, задачи и «исключения» | 40 |
| [8-klass-oblastnoy-avtorsky-razbor-1.md](8-klass-oblastnoy-avtorsky-razbor-1.md) | Областной этап, 8 класс — Областной этап · 8 класс · 36 заданий части I и 2 задания части II | 42 |
| [8-klass-oblastnoy-avtorsky-razbor-2.md](8-klass-oblastnoy-avtorsky-razbor-2.md) | Областной этап, 8 класс — Областной этап · 8 класс · 36 заданий части I и 2 задания части II | 42 |
| [keys.md](keys.md) | сводная таблица ключей всех олимпиад | 203 |
| [analiz-otvetov-8-klass.md](analiz-otvetov-8-klass.md) | Анализ ответов по биологии, 8 класс | — |

PDF с рисунками и схемами — в папке [pdf/](pdf/) (по одному файлу на олимпиаду).

Прямые ссылки на текст (для ИИ, который умеет открывать ссылки):

- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/7-klass-gorodskoy-2014-2015.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-shkolny-2016-2017-1.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-shkolny-2016-2017-2.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-2018-2019-1.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-2018-2019-2.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-2018-2019-3.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-rayonny-2019-brest.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-2016-avtorsky-razbor-1.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-2016-avtorsky-razbor-2.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-oblastnoy-avtorsky-razbor-1.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/8-klass-oblastnoy-avtorsky-razbor-2.md
- https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/review/keys.md

## Откуда ключи

- `g7`, `g8`, `g8b`, `r19` — ключи и разборы из исходных разборов (папка `source/`); при сборке ключи сверяются с матрицами ответов исходников. Фактические неточности исходных разборов исправлены правками `SOURCE_FIXES` в `tools/build_data.py`.
- `r19`, часть II, пункт 11 — ключ исправлен с «порошицы» на «сократительную вакуоль» (по чёткой копии рисунка из PDF-бланка); пояснение есть в самом вопросе.
- `n16` (олимпиада 2016) и `obl` (областной этап) — официальных ключей не было: ответы решены заново, разборы написаны с нуля (`tools/authored/`). Задания 28 и 30 областного этапа в бланке с опечатками и переделаны в выбор нескольких пунктов.

## Как сайт проверяет ответы

- **Один ответ** — совпадение с ключом; варианты из «Также засчитывается» тоже принимаются с пояснением.
- **Несколько ответов** — отмеченный набор должен совпасть с одним из допустимых наборов.
- **Соответствие** — каждая строка сверяется с ключом; допустимые альтернативы указаны отдельно.
- **Слова и числа** — ответ приводится к нижнему регистру, «ё» → «е», знаки препинания убираются; затем сверка с шаблонами (регулярными выражениями). На типичные ошибки есть подсказки.
- **Открытые задания** — ученица сравнивает свой черновик с ключом и сама отмечает результат.

## Изображения

Рисунки условий лежат в `assets/img/`. Ниже — где используется каждый (вопросы указаны как на сайте):

- `assets/img/g7-drozhzhi-pochkovanie.png` — g7-q23 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g7-drozhzhi-pochkovanie.png
- `assets/img/g7-mikroskop.png` — g7-q33 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g7-mikroskop.png
- `assets/img/g7-socvetiya.png` — g7-q34 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g7-socvetiya.png
- `assets/img/g8b-p1-1.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-1.jpg
- `assets/img/g8b-p1-2.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-2.jpg
- `assets/img/g8b-p1-3.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-3.jpg
- `assets/img/g8b-p1-4.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-4.jpg
- `assets/img/g8b-p1-5.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-5.jpg
- `assets/img/g8b-p1-6.png` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-6.png
- `assets/img/g8b-p1-kollazh.jpg` — g8b-q30 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p1-kollazh.jpg
- `assets/img/g8b-p2-1.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-1.jpg
- `assets/img/g8b-p2-2.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-2.jpg
- `assets/img/g8b-p2-3.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-3.jpg
- `assets/img/g8b-p2-4.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-4.jpg
- `assets/img/g8b-p2-5.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-5.jpg
- `assets/img/g8b-p2-6.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-6.jpg
- `assets/img/g8b-p2-7.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-7.jpg
- `assets/img/g8b-p2-8.jpg` — g8b-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p2-8.jpg
- `assets/img/g8b-p3-list.jpg` — g8b-q32 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-p3-list.jpg
- `assets/img/g8b-t08-kletka.jpg` — g8b-q8 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t08-kletka.jpg
- `assets/img/g8b-t09-spirogira.jpg` — g8b-q9 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t09-spirogira.jpg
- `assets/img/g8b-t10-koren-irisa.png` — g8b-q10 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t10-koren-irisa.png
- `assets/img/g8b-t17-veliger.jpg` — g8b-q17 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t17-veliger.jpg
- `assets/img/g8b-t18-lichinki.jpg` — g8b-q18 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t18-lichinki.jpg
- `assets/img/g8b-t27-pauk.png` — g8b-q26 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/g8b-t27-pauk.png
- `assets/img/n16-p1-mollusk.png` — n16-q31 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-p1-mollusk.png
- `assets/img/n16-p3-list.jpg` — n16-q33 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-p3-list.jpg
- `assets/img/n16-t05-rot.png` — n16-q5 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-t05-rot.png
- `assets/img/n16-t07-skelet.png` — n16-q7 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-t07-skelet.png
- `assets/img/n16-t21-serdce.png` — n16-q21 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-t21-serdce.png
- `assets/img/n16-t22-meduza.jpg` — n16-q22 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-t22-meduza.jpg
- `assets/img/n16-t24-cherep.jpg` — n16-q24 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/n16-t24-cherep.jpg
- `assets/img/obl-t27-strekoza.png` — obl-q27 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/obl-t27-strekoza.png
- `assets/img/r19-ch2-list.png` — r19-q15 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/r19-ch2-list.png
- `assets/img/r19-ch2-protisty-pdf.png` — r19-q16 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/r19-ch2-protisty-pdf.png
- `assets/img/r19-ch2-protisty.png` — r19-q16 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/r19-ch2-protisty.png
- `assets/img/r19-t08-pauk.png` — r19-q8 — https://raw.githubusercontent.com/metalinjector/biology-tests/claude/intelligent-heisenberg-9woyvy/assets/img/r19-t08-pauk.png

Пакет создаётся командой `python3 tools/export_review.py --pdf` из `assets/js/data.js`.
