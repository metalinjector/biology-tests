#!/usr/bin/env python3
"""Пакет для внешней проверки: всё содержимое тренажёра в читаемом виде.

Создаёт папку review/:
  README.md            — как устроен пакет и как идёт проверка ответов на сайте;
  keys.md              — сводная таблица ключей всех 203 вопросов;
  <олимпиада>.md       — условия, варианты, ключи, эталонные ответы и разборы
                         (длинные файлы делятся на части *-1.md, *-2.md);
  pdf/<олимпиада>.pdf  — то же с рисунками и схемами (если передан --pdf).

Запуск:  python3 tools/export_review.py [--pdf]
Источник — assets/js/data.js (собирается tools/build_data.py).
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "review"
BRANCH = "claude/intelligent-heisenberg-9woyvy"
RAW = f"https://raw.githubusercontent.com/metalinjector/biology-tests/{BRANCH}/"
PART_LIMIT = 170_000  # байт на файл: удобно прикладывать к чату с ИИ

TYPE_RU = {
    "single": "один ответ",
    "multi": "несколько ответов (засчитывается набор)",
    "match": "соответствие",
    "text": "вписать слово или число",
    "terms": "термины по определениям / по рисунку",
    "table": "заполнить таблицу",
    "open": "открытый ответ (ученица сверяет себя с ключом)",
}
FILE_NAMES = {
    "g7": "7-klass-gorodskoy-2014-2015",
    "g8": "8-klass-shkolny-2016-2017",
    "g8b": "8-klass-2018-2019",
    "r19": "8-klass-rayonny-2019-brest",
    "n16": "8-klass-2016-avtorsky-razbor",
    "obl": "8-klass-oblastnoy-avtorsky-razbor",
}
SUB = str.maketrans("0123456789+-−", "₀₁₂₃₄₅₆₇₈₉₊₋₋")
SUP = str.maketrans("0123456789+-−n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻ⁿ")


def load():
    src = (ROOT / "assets" / "js" / "data.js").read_text(encoding="utf-8")
    return json.loads(src[src.index("{"): src.rindex("}") + 1])


# ---------------------------------------------------------------- HTML → Markdown

def md_inline(node):
    out = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            out.append(re.sub(r"\s+", " ", str(ch)))
            continue
        if not isinstance(ch, Tag):
            continue
        name = ch.name
        if name in ("strong", "b"):
            t = md_inline(ch).strip()
            out.append(f"**{t}**" if t else "")
        elif name in ("em", "i"):
            t = md_inline(ch).strip()
            out.append(f"*{t}*" if t else "")
        elif name == "sub":
            out.append(ch.get_text().translate(SUB))
        elif name == "sup":
            out.append(ch.get_text().translate(SUP))
        elif name == "br":
            out.append(" / ")
        elif name == "svg":
            out.append(f" [схема: {ch.get('aria-label') or 'рисунок'}] ")
        elif name == "img":
            out.append(img_md(ch))
        elif "frac" in (ch.get("class") or []):
            parts = [md_inline(x).strip() for x in ch.find_all("span", recursive=False)]
            out.append("(" + ")/(".join(parts) + ")" if len(parts) == 2 else md_inline(ch))
        elif "ou" in (ch.get("class") or []):
            out.append(" [олимпиадный уровень] ")
        else:
            out.append(md_inline(ch))
    return "".join(out)


def img_md(tag):
    src = tag.get("src", "")
    name = src.split("/")[-1]
    alt = (tag.get("alt") or "").strip() or name
    if src.startswith("assets/"):
        return f"\n\n![{alt}](../{src})\n(файл: `{src}`, ссылка: {RAW}{src})\n\n"
    return f" [картинка: {alt}] "


def md_block(node, depth=0):
    """Блочные элементы → строки Markdown."""
    lines = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            t = re.sub(r"\s+", " ", str(ch)).strip()
            if t:
                lines.append(t)
            continue
        if not isinstance(ch, Tag):
            continue
        cls = ch.get("class") or []
        name = ch.name
        if name in ("script", "style"):
            continue
        if "bl" in cls:  # заголовок блока разбора
            num = ch.find(class_="bn")
            n = num.get_text(strip=True) if num else ""
            if num:
                num.extract()
            lines.append(f"\n#### {n}. {ch.get_text(' ', strip=True)}".replace("#### . ", "#### "))
            continue
        if "svgwrap" in cls or name == "svg":
            svg = ch if name == "svg" else ch.find("svg")
            label = svg.get("aria-label") if svg else ""
            lines.append(f"[Схема в разборе: {label or 'без подписи'}]")
            continue
        if "cap" in cls:
            lines.append(f"*Подпись к схеме: {ch.get_text(' ', strip=True)}*")
            continue
        if name in ("ul", "ol"):
            for i, li in enumerate(ch.find_all("li", recursive=False)):
                mark = f"{i + 1}." if name == "ol" else "-"
                sub_lists = li.find_all(["ul", "ol"], recursive=False)
                for sl in sub_lists:
                    sl.extract()
                lines.append("  " * depth + f"{mark} {md_inline(li).strip()}")
                for sl in sub_lists:
                    wrap = BeautifulSoup("<div></div>", "html.parser").div
                    wrap.append(sl)
                    lines.extend(md_block(wrap, depth + 1))
            lines.append("")
            continue
        if name == "table":
            rows = ch.find_all("tr")
            for ri, tr in enumerate(rows):
                cells = [md_inline(td).strip().replace("|", "/") for td in tr.find_all(["td", "th"])]
                lines.append("| " + " | ".join(cells) + " |")
                if ri == 0:
                    lines.append("|" + "---|" * len(cells))
            lines.append("")
            continue
        if name in ("p", "h3", "h4", "h2", "figcaption", "summary", "dt", "dd"):
            t = md_inline(ch).strip()
            if t:
                lines.append(("### " if name in ("h2", "h3") else "") + t)
                lines.append("")
            continue
        if name == "figure":
            for im in ch.find_all("img"):
                lines.append(img_md(im).strip())
            cap = ch.find("figcaption")
            if cap:
                lines.append(f"*{cap.get_text(' ', strip=True)}*")
            for sv in ch.find_all("svg"):
                lines.append(f"[Схема: {sv.get('aria-label') or 'без подписи'}]")
            lines.append("")
            continue
        if name == "img":
            lines.append(img_md(ch).strip())
            continue
        if name in ("div", "section", "article", "blockquote", "header", "main", "span", "label"):
            if ch.find(["p", "ul", "ol", "table", "div", "figure", "h3", "h4", "svg", "img"]):
                lines.extend(md_block(ch, depth))
            else:
                t = md_inline(ch).strip()
                if t:
                    lines.append(t)
                    lines.append("")
            continue
        t = md_inline(ch).strip()
        if t:
            lines.append(t)
    return lines


def to_md(h):
    if not h:
        return ""
    soup = BeautifulSoup(h, "html.parser")
    text = "\n".join(md_block(soup))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def plain(h):
    return re.sub(r"\s+", " ", BeautifulSoup(h or "", "html.parser").get_text(" ", strip=True)).strip()


# ---------------------------------------------------------------- вопрос

def opt_text(q, key, field="options"):
    for o in q.get(field) or []:
        if o["key"] == key:
            return plain(o["html"])
    return "?"


def key_md(q):
    t = q["type"]
    lines = []
    if t == "single":
        lines.append(f"**Ключ:** {q['answer']}) {opt_text(q, q['answer'])}")
        for k, note in (q.get("alsoAccept") or {}).items():
            lines.append(f"**Также засчитывается:** {k}) {opt_text(q, k)} — {plain(note)}")
    elif t == "multi":
        lines.append("**Ключ (все нужные пункты):** " + ", ".join(q["answer"]))
        for st in (q.get("acceptSets") or [])[1:]:
            lines.append("**Также засчитывается набор:** " + ", ".join(st))
        if q.get("setNote"):
            lines.append(f"**Пояснение к наборам:** {plain(q['setNote'])}")
    elif t == "match":
        lines.append("**Ключ (соответствие):**")
        for k, v in q["answer"].items():
            lines.append(f"- {k}: {opt_text(q, k, 'left')} → {v}: {opt_text(q, v, 'right')}")
        for k, alts in (q.get("altAnswers") or {}).items():
            for v, note in alts.items():
                lines.append(f"- *также засчитывается* {k} → {v}: {opt_text(q, v, 'right')} — {plain(note)}")
    elif t == "text":
        for i, b in enumerate(q["blanks"]):
            ref = f"«{b['word']}»" if b.get("word") else "см. эталонный ответ"
            lines.append(f"**Пропуск {i + 1}:** эталон {ref}; принимаются ответы по шаблонам {b['accept']}")
            for h in b.get("hints") or []:
                lines.append(f"  - подсказка на ответ по шаблону `{h['re']}`: {h['msg']}")
    elif t == "terms":
        for i, it in enumerate(q["items"]):
            lines.append(f"- пункт {it.get('key', i + 1)}: {plain(it.get('html', ''))} → **{it.get('word')}** "
                         f"(принимаются шаблоны {it['accept']})")
    elif t == "table":
        cols = {c["key"]: plain(c.get("label") or c.get("html") or c["key"]) for c in q["columns"]}
        for r in q["rows"]:
            vals = "; ".join(f"{cols[c]}: {q['answer'][r['key']][c]}" for c in cols)
            lines.append(f"- {plain(r.get('label') or r['key'])} — {vals}")
    elif t == "open":
        lines.append("**Ключ:** открытый ответ — см. эталонный ответ ниже.")
    return "\n".join(lines)


def cond_md(q):
    out = [f"**Условие.** {to_md(q['stem'])}"]
    if q.get("instructions"):
        out.append(f"*Указание на сайте:* {q['instructions']}")
    if q.get("media"):
        out.append(to_md(q["media"]))
    if q.get("statements"):
        out.append("Пункты:\n" + "\n".join(f"- {s['key']}) {plain(s['html'])}" for s in q["statements"]))
    if q.get("options"):
        out.append("Варианты:\n" + "\n".join(f"- {o['key']}) {plain(o['html'])}" for o in q["options"]))
    if q["type"] == "match":
        out.append(f"Левый столбец ({q.get('leftTitle', '')}):\n" + "\n".join(
            f"- {x['key']}: {to_md(x['html']).strip()}" for x in q["left"]))
        out.append(f"Правый столбец ({q.get('rightTitle', '')}):\n" + "\n".join(
            f"- {x['key']}: {plain(x['html'])}" for x in q["right"]))
    if q["type"] == "terms":
        out.append("Пункты:\n" + "\n".join(f"- {it.get('key', i + 1)}) {plain(it.get('html', ''))}"
                                          for i, it in enumerate(q["items"])))
    if q["type"] == "table":
        out.append("Строки: " + "; ".join(plain(r.get("label") or r["key"]) for r in q["rows"]))
    return "\n\n".join(x for x in out if x)


def question_md(o, sec, idx, q):
    head = q.get("head") or ""
    topic = q.get("topic") or ""
    title = " · ".join(x for x in [f"№ {q['num']}", head, topic] if x)
    parts = [
        f"### [{o['id']}-q{idx}] {title}",
        f"Раздел: {sec['title']}. Тип: {TYPE_RU.get(q['type'], q['type'])}. "
        f"ID: `{q['id']}`. На сайте: `#{o['id']}-q{idx}`.",
        cond_md(q),
        key_md(q),
        "**Эталонный ответ (карточка «Правильный ответ» на сайте):**\n\n" + to_md(q.get("answerHtml", "")),
    ]
    expl = to_md(q.get("explanation", ""))
    if expl:
        parts.append("**Разбор (шаги 3–8):**\n" + expl)
    return "\n\n".join(p for p in parts if p) + "\n\n---\n"


# ---------------------------------------------------------------- файлы

def write_parts(stem, header, chunks):
    files, cur, size, n = [], [], 0, 1
    for c in chunks:
        b = len(c.encode("utf-8"))
        if cur and size + b > PART_LIMIT:
            files.append(cur)
            cur, size = [], 0
        cur.append(c)
        size += b
    if cur:
        files.append(cur)
    names = []
    for i, body in enumerate(files):
        name = f"{stem}.md" if len(files) == 1 else f"{stem}-{i + 1}.md"
        part = "" if len(files) == 1 else f" (часть {i + 1} из {len(files)})"
        (OUT / name).write_text(header.replace("{PART}", part) + "\n".join(body), encoding="utf-8")
        names.append(name)
    return names


def olympiad_label(o):
    return f"{o['title']} — {o['subtitle']}"


def main():
    data = load()
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.md"):
        f.unlink()
    index, key_rows, images = [], [], {}
    total = 0
    for o in data["olympiads"]:
        chunks = []
        idx = 0
        for sec in o["sections"]:
            for q in sec["questions"]:
                idx += 1
                total += 1
                chunks.append(question_md(o, sec, idx, q))
                k = {"single": lambda: q["answer"], "multi": lambda: ", ".join(q["answer"]),
                     "match": lambda: " ".join(f"{a}{b}" if len(a) <= 2 else f"{a}→{b}" for a, b in q["answer"].items()),
                     "text": lambda: plain(q["answerHtml"])[:60],
                     "terms": lambda: "; ".join(str(it.get("word")) for it in q["items"]),
                     "table": lambda: "таблица (см. файл олимпиады)",
                     "open": lambda: "открытый (см. ключ)"}[q["type"]]()
                extra = []
                if q.get("alsoAccept"):
                    extra.append("+ " + ", ".join(q["alsoAccept"]))
                if q.get("acceptSets") and len(q["acceptSets"]) > 1:
                    extra.append("+ наборы " + " / ".join(",".join(s) for s in q["acceptSets"][1:]))
                if q.get("altAnswers"):
                    extra.append("+ " + ", ".join(f"{a}→{b}" for a, d in q["altAnswers"].items() for b in d))
                key_rows.append(f"| {o['id']}-q{idx} | {q['num']} | {TYPE_RU[q['type']].split(' (')[0]} | "
                                f"{plain(q.get('topic') or q['stem'])[:70].replace('|', '/')} | "
                                f"{str(k).replace('|', '/')} | {' '.join(extra).replace('|', '/')} |")
                for m in re.finditer(r'src=\\?"(assets/img/[^"\\]+)', (q.get("media") or "") + q.get("explanation", "")
                                     + json.dumps(q.get("left", []), ensure_ascii=False)):
                    images.setdefault(m.group(1), set()).add(f"{o['id']}-q{idx}")
        notes = "\n\n".join(f"### Памятка: {n['title']}\n\n{to_md(n['html'])}" for n in o.get("notes", []))
        chunks.append("## Памятки олимпиады\n\n" + notes + "\n")
        header = (f"# {olympiad_label(o)}{{PART}}\n\n"
                  f"Олимпиада `{o['id']}` из тренажёра «Олимпиада под микроскопом». Вопросов: {idx}. "
                  "Каждый вопрос: условие (с рисунками), ключ и допустимые ответы, эталонный ответ, "
                  "разбор по шагам 3–8 (алгоритм, объяснение и разбор вариантов, ловушки, как запомнить, схема, "
                  "олимпиадный горизонт). Схемы в разборах здесь заменены подписями; сами схемы — в PDF-версии.\n\n---\n\n")
        names = write_parts(FILE_NAMES[o["id"]], header, chunks)
        index.append((o, idx, names))

    # сводная таблица ключей
    keys = ["# Ключи всех вопросов", "",
            "Сокращения: «+» — также засчитываемые ответы. Для соответствий: «А4» — строка А ↔ вариант 4.", "",
            "| На сайте | № | Тип | Тема / условие | Ключ | Допускается |", "|---|---|---|---|---|---|"] + key_rows
    (OUT / "keys.md").write_text("\n".join(keys) + "\n", encoding="utf-8")

    # README
    rd = [
        "# Пакет для внешней проверки тренажёра «Олимпиада под микроскопом»", "",
        f"Все {total} вопросов шести олимпиад в обычных текстовых файлах — без архивов и без JavaScript. "
        "Файлы можно прикладывать к чату с любым ИИ по одному или давать ссылки на них.", "",
        "## Файлы", "",
        "| Файл | Олимпиада | Вопросов |", "|---|---|---|",
    ]
    for o, n, names in index:
        for nm in names:
            rd.append(f"| [{nm}]({nm}) | {olympiad_label(o)} | {n} |")
    rd += ["| [keys.md](keys.md) | сводная таблица ключей всех олимпиад | " + str(total) + " |", "",
           "PDF с рисунками и схемами — в папке [pdf/](pdf/) (по одному файлу на олимпиаду).", "",
           "Прямые ссылки на текст (для ИИ, который умеет открывать ссылки):", ""]
    for o, n, names in index:
        for nm in names:
            rd.append(f"- {RAW}review/{nm}")
    rd.append(f"- {RAW}review/keys.md")
    rd += ["", "## Откуда ключи", "",
           "- `g7`, `g8`, `g8b`, `r19` — ключи и разборы из исходных разборов (папка `source/`); при сборке ключи "
           "сверяются с матрицами ответов исходников. Фактические неточности исходных разборов исправлены правками "
           "`SOURCE_FIXES` в `tools/build_data.py`.",
           "- `r19`, часть II, пункт 11 — ключ исправлен с «порошицы» на «сократительную вакуоль» (по чёткой копии "
           "рисунка из PDF-бланка); пояснение есть в самом вопросе.",
           "- `n16` (олимпиада 2016) и `obl` (областной этап) — официальных ключей не было: ответы решены заново, "
           "разборы написаны с нуля (`tools/authored/`). Задания 28 и 30 областного этапа в бланке с опечатками "
           "и переделаны в выбор нескольких пунктов.", "",
           "## Как сайт проверяет ответы", "",
           "- **Один ответ** — совпадение с ключом; варианты из «Также засчитывается» тоже принимаются с пояснением.",
           "- **Несколько ответов** — отмеченный набор должен совпасть с одним из допустимых наборов.",
           "- **Соответствие** — каждая строка сверяется с ключом; допустимые альтернативы указаны отдельно.",
           "- **Слова и числа** — ответ приводится к нижнему регистру, «ё» → «е», знаки препинания убираются; затем "
           "сверка с шаблонами (регулярными выражениями). На типичные ошибки есть подсказки.",
           "- **Открытые задания** — ученица сравнивает свой черновик с ключом и сама отмечает результат.", "",
           "## Изображения", "",
           "Рисунки условий лежат в `assets/img/`. Ниже — где используется каждый (вопросы указаны как на сайте):", ""]
    for src in sorted(images):
        rd.append(f"- `{src}` — {', '.join(sorted(images[src]))} — {RAW}{src}")
    rd += ["", "Пакет создаётся командой `python3 tools/export_review.py --pdf` из `assets/js/data.js`."]
    (OUT / "README.md").write_text("\n".join(rd) + "\n", encoding="utf-8")
    print(f"review/: {total} вопросов, файлов: {sum(len(n) for _, _, n in index) + 2}")

    if "--pdf" in sys.argv:
        make_pdfs(data)


# ---------------------------------------------------------------- PDF

PRINT_CSS = """
body { font-family: "Noto Sans", "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; color: #1f2d2a; margin: 0; }
h1 { font-size: 18pt; margin: 0 0 6pt; } .sub { color: #5b6b66; margin: 0 0 14pt; }
.q { border-top: 2px solid #2153c0; padding-top: 8pt; margin-top: 14pt; }
.q h2 { font-size: 13pt; margin: 0 0 4pt; } .meta { color: #5b6b66; font-size: 9pt; margin-bottom: 6pt; }
.box { border: 1px solid #c9d3cf; border-radius: 6pt; padding: 6pt 9pt; margin: 6pt 0; }
.key { background: #e8f4ec; border-color: #2f7a3b; } .ans { background: #f3f6f5; }
.lbl { font-weight: 700; font-size: 9pt; text-transform: uppercase; letter-spacing: .04em; color: #2153c0; }
img { max-width: 100%; max-height: 210mm; } figure { margin: 6pt 0; } figcaption { font-size: 9pt; color: #5b6b66; }
svg { max-width: 100%; height: auto; } svg text { font-family: "Noto Sans", "DejaVu Sans", sans-serif; }
table { border-collapse: collapse; margin: 4pt 0; font-size: 9.5pt; } td, th { border: 1px solid #c9d3cf; padding: 2pt 5pt; vertical-align: top; }
.blk { margin: 8pt 0; } .bl { font-weight: 700; color: #2153c0; margin-bottom: 3pt; } .bn { margin-right: 4pt; }
.rule { border-left: 3px solid #c2410c; padding-left: 6pt; } .rule-ic { display: none; }
.cap { font-size: 9pt; color: #5b6b66; } .ou { font-size: 8pt; color: #6d4bc4; border: 1px solid #6d4bc4; border-radius: 3pt; padding: 0 3pt; }
.frac { display: inline-flex; flex-direction: column; text-align: center; vertical-align: middle; font-size: 85%; }
.frac > span:first-child { border-bottom: 1px solid currentColor; }
ul, ol { margin: 3pt 0 3pt 14pt; padding: 0; } p { margin: 3pt 0; }
.opts li { margin: 1pt 0; }
"""


def make_pdfs(data):
    pdf_dir = OUT / "pdf"
    pdf_dir.mkdir(exist_ok=True)
    tmp = OUT / ".print"
    tmp.mkdir(exist_ok=True)
    jobs = []
    for o in data["olympiads"]:
        body = [f"<h1>{html.escape(o['title'])}</h1><p class='sub'>{html.escape(o['subtitle'])}</p>"]
        idx = 0
        for sec in o["sections"]:
            for q in sec["questions"]:
                idx += 1
                title = " · ".join(x for x in [f"№ {q['num']}", q.get("head") or "", q.get("topic") or ""] if x)
                cond = [f"<div>{q['stem']}</div>"]
                if q.get("instructions"):
                    cond.append(f"<p><em>{html.escape(q['instructions'])}</em></p>")
                if q.get("media"):
                    cond.append(q["media"])
                if q.get("statements"):
                    cond.append("<ul class='opts'>" + "".join(f"<li><b>{s['key']})</b> {s['html']}</li>" for s in q["statements"]) + "</ul>")
                if q.get("options"):
                    cond.append("<ul class='opts'>" + "".join(f"<li><b>{x['key']})</b> {x['html']}</li>" for x in q["options"]) + "</ul>")
                if q["type"] == "match":
                    cond.append("<table><tr><th>" + html.escape(q.get("leftTitle", "")) + "</th></tr>"
                                + "".join(f"<tr><td><b>{x['key']}</b> {x['html']}</td></tr>" for x in q["left"]) + "</table>")
                    cond.append("<p>" + "; ".join(f"<b>{x['key']}</b> — {x['html']}" for x in q["right"]) + "</p>")
                if q["type"] == "terms":
                    cond.append("<ol>" + "".join(f"<li>{it.get('html', '')}</li>" for it in q["items"]) + "</ol>")
                key_html = html.escape(key_md(q)).replace("\n", "<br>").replace("**", "")
                body.append(
                    f"<section class='q'><h2>[{o['id']}-q{idx}] {html.escape(title)}</h2>"
                    f"<div class='meta'>{html.escape(sec['title'])} · {TYPE_RU[q['type']]}</div>"
                    f"<div class='box'><div class='lbl'>Условие</div>{''.join(cond)}</div>"
                    f"<div class='box key'><div class='lbl'>Ключ</div>{key_html}</div>"
                    f"<div class='box ans'><div class='lbl'>Эталонный ответ</div>{q.get('answerHtml', '')}</div>"
                    f"<div class='expl src-{q['src']}'>{q.get('explanation', '')}</div></section>")
        page = (f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><base href='{ROOT.as_uri()}/'>"
                f"<style>{PRINT_CSS}</style></head><body>{''.join(body)}</body></html>")
        page = page.replace(' loading="lazy"', "")  # иначе картинки ниже первого экрана не попадут в PDF
        hp = tmp / f"{o['id']}.html"
        hp.write_text(page, encoding="utf-8")
        jobs.append((hp, pdf_dir / f"{FILE_NAMES[o['id']]}.pdf"))

    # атлас рисунков: каждая картинка на своей странице в полном размере
    used = {}
    for o in data["olympiads"]:
        idx = 0
        for sec in o["sections"]:
            for q in sec["questions"]:
                idx += 1
                blob = (q.get("media") or "") + q.get("explanation", "") + json.dumps(q.get("left", []), ensure_ascii=False)
                for m in re.finditer(r'src=\\?"(assets/img/[^"\\]+)', blob):
                    used.setdefault(m.group(1), []).append(f"{o['id']}-q{idx} (№ {q['num']})")
        for n in o.get("notes", []):
            for m in re.finditer(r'src="(assets/img/[^"]+)"', n["html"]):
                used.setdefault(m.group(1), []).append(f"{o['id']}: памятка «{n['title']}»")
    pages = [f"<h1>Рисунки тренажёра</h1><p class='sub'>{len(used)} файлов из assets/img/. Каждый рисунок — на отдельной "
             "странице в исходном разрешении; указано, в каких вопросах он используется (как на сайте: олимпиада-qномер).</p>"]
    for src in sorted(used):
        pages.append(f"<section style='page-break-before: always'><h2>{html.escape(src)}</h2>"
                     f"<div class='meta'>Используется: {html.escape(', '.join(dict.fromkeys(used[src])))}</div>"
                     f"<img src='{src}' style='max-height: 240mm'></section>")
    hp = tmp / "atlas.html"
    hp.write_text(f"<!doctype html><html lang='ru'><head><meta charset='utf-8'><base href='{ROOT.as_uri()}/'>"
                  f"<style>{PRINT_CSS}</style></head><body>{''.join(pages)}</body></html>", encoding="utf-8")
    jobs.append((hp, pdf_dir / "risunki-vse.pdf"))
    script = tmp / "print.cjs"
    script.write_text(
        "const { chromium } = require(process.argv[2]);\n"
        "(async () => { const b = await chromium.launch(process.argv[3] ? { executablePath: process.argv[3] } : {});\n"
        "  const p = await b.newPage();\n"
        "  for (let i = 4; i < process.argv.length; i += 2) {\n"
        "    await p.goto('file://' + process.argv[i], { waitUntil: 'load' });\n"
        "    await p.waitForFunction(() => [...document.images].every((im) => im.complete && im.naturalWidth > 0), null, { timeout: 60000 });\n"
        "    await p.pdf({ path: process.argv[i + 1], format: 'A4', printBackground: true,\n"
        "      margin: { top: '14mm', bottom: '14mm', left: '13mm', right: '13mm' } });\n"
        "  }\n  await b.close(); })();\n", encoding="utf-8")
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    exe = "/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else ""
    args = ["node", str(script), str(Path(root) / "playwright"), exe]
    for hp, pp in jobs:
        args += [str(hp), str(pp)]
    subprocess.run(args, check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    for _, pp in jobs:
        print(f"{pp.relative_to(ROOT)}: {pp.stat().st_size // 1024} КБ")


if __name__ == "__main__":
    main()
