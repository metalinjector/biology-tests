#!/usr/bin/env python3
"""Собирает данные тренажёра из исходных HTML-разборов олимпиад.

Источник истины для текста — файлы в папке source/: условия, разборы,
рисунки (SVG и PNG) и памятки переносятся оттуда без пересказа.
Ключи ответов и типы заданий заданы в этом файле явно и сверяются
с итоговыми матрицами ответов из тех же исходников (см. verify()).

Запуск:  python3 tools/build_data.py
Результат: assets/js/data.js и картинки из условий в assets/img/.
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
SRC7 = ROOT / "source" / "olimpiada-7-klass-2014-2015.html"
SRC8 = ROOT / "source" / "olimpiada-8-klass-2016-2017.html"
OUT_JS = ROOT / "assets" / "js" / "data.js"
IMG_DIR = ROOT / "assets" / "img"

RU_UP = "АБВГДЕЖ"
RU_LO = "абвгдежзи"


# ---------------------------------------------------------------- helpers

def inner(tag):
    return tag.decode_contents().strip()


def outer(tag):
    return str(tag)


def text_of(tag):
    return re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()


def fail(msg):
    print("ОШИБКА:", msg, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- KaTeX → HTML
# Формулы в исходнике отрендерены KaTeX без MathML. Переводим их в обычный
# HTML (<sub>, <sup>, <i>, стрелка с подписью), чтобы не тянуть шрифты KaTeX.

def _katex_node(node):
    if isinstance(node, NavigableString):
        t = str(node).replace("​", "")
        return html.escape(t, quote=False)
    if not isinstance(node, Tag):
        return ""
    cls = node.get("class", [])
    if node.name == "svg":
        return ""
    if {"katex-strut", "pstrut", "vlist-s"} & set(cls):
        return ""
    if "msupsub" in cls:
        out = []
        for sp in node.select(".vlist > span"):
            m = re.search(r"top:\s*(-?[\d.]+)em", sp.get("style", ""))
            if not m:
                continue
            content = "".join(_katex_node(c) for c in sp.children).strip()
            if not content:
                continue
            tag = "sub" if float(m.group(1)) > -2.8 else "sup"
            out.append(f"<{tag}>{content}</{tag}>")
        return "".join(out)
    if "x-arrow" in cls:
        label = ""
        for sp in node.select(".x-arrow-pad"):
            label += sp.get_text("", strip=True)
        return (f' <span class="xarrow"><span class="xarrow-label">{html.escape(label)}</span>'
                f'<span class="xarrow-line" aria-hidden="true">⟶</span></span> ')
    if "mathnormal" in cls:
        return "<i>" + html.escape(node.get_text("", strip=True)) + "</i>"
    if "mspace" in cls:
        return " "
    body = "".join(_katex_node(c) for c in node.children)
    if "mrel" in cls or "mbin" in cls:
        return " " + body.strip() + " "
    return body


def convert_katex(soup):
    for disp in soup.select(".katex-display"):
        k = disp.select_one(".katex")
        h = _katex_node(k.select_one(".katex-html"))
        h = re.sub(r"\s+", " ", h).strip()
        new = BeautifulSoup(f'<span class="formula formula-block">{h}</span>', "html.parser")
        disp.replace_with(new)
    for k in soup.select("span.katex"):
        h = _katex_node(k.select_one(".katex-html"))
        h = re.sub(r"\s+", " ", h).strip()
        new = BeautifulSoup(f'<span class="formula">{h}</span>', "html.parser")
        k.replace_with(new)


# ---------------------------------------------------------------- стили
# Встроенные цвета исходника рассчитаны на белую бумагу. Переводим их
# в классы, которые раскрашиваются токенами темы (светлой и тёмной).

STYLE_TO_CLASS = {
    "color:#777;font-weight:bold": "tx-muted tx-b",
    "color:#a4262c;font-weight:bold": "tx-bad tx-b",
    "color:#7a5f17;font-weight:bold": "tx-amber tx-b",
    "color:#a4262c": "tx-bad",
    "background:#e6f0fa": "bg-okrow",
    "margin-left:1.4em": "indent",
    "font-size:8pt;color:#5d6f6a": "tx-muted tx-small",
    "font-size:9pt;color:#5d6f6a": "tx-muted tx-small",
    "font-size:8.6pt;color:#5d6f6a;margin-top:6px": "tx-muted tx-small",
    "text-align:center": "tx-center",
    # легенда разбора 8 класса: цвет блока = тип шага
    "background:#f5f7f6;border-color:#9aaca6": "lg lg-cond",
    "background:#e6f4f1;border-color:#0f7b6c": "lg lg-ans",
    "background:#eef4fb;border-color:#2463a6": "lg lg-algo",
    "background:#fff;border-color:#4b5d58;border:1px solid #d7e0dd;border-left:3px solid #4b5d58": "lg lg-expl",
    "background:#fff4ec;border-color:#c2410c": "lg lg-traps",
    "background:#f4f0fd;border-color:#6d4bc4": "lg lg-mem",
    "background:#fff;border:1px solid #d7e0dd;border-left:3px solid #2f7a3b": "lg lg-viz",
    "background:#e9f6f9;border-color:#0e7490": "lg lg-hor",
}


def fix_styles(root):
    for el in root.find_all(True):
        if el.name in ("svg",) or el.find_parent("svg") is not None:
            continue
        st = el.get("style")
        if st is None:
            continue
        key = st.strip().rstrip(";")
        if key in STYLE_TO_CLASS:
            el["class"] = el.get("class", []) + STYLE_TO_CLASS[key].split()
            del el["style"]
            continue
        keep = []
        for part in key.split(";"):
            part = part.strip()
            if re.match(r"^width:\s*\d+(\.\d+)?%$", part) and el.name in ("th", "td"):
                keep.append(part)
            elif part in ("text-align:left", "text-align:center"):
                keep.append(part)
        if keep:
            el["style"] = ";".join(keep)
        else:
            del el["style"]


# ---------------------------------------------------------------- SVG
_svg_counter = [0]


def uniquify_svg_ids(root, prefix):
    """В исходниках у многих SVG одинаковые id маркеров-стрелок. Если первый
    такой SVG окажется в свёрнутом блоке, стрелки в остальных пропадут —
    поэтому делаем id уникальными для каждого рисунка."""
    for svg in root.find_all("svg"):
        _svg_counter[0] += 1
        p = f"{prefix}s{_svg_counter[0]}-"
        ids = [el["id"] for el in svg.find_all(True) if el.has_attr("id")]
        if not ids:
            continue
        raw = str(svg)
        for i in sorted(set(ids), key=len, reverse=True):
            raw = re.sub(r'id="%s"' % re.escape(i), f'id="{p}{i}"', raw)
            raw = re.sub(r"url\(#%s\)" % re.escape(i), f"url(#{p}{i})", raw)
            raw = re.sub(r'href="#%s"' % re.escape(i), f'href="#{p}{i}"', raw)
        svg.replace_with(BeautifulSoup(raw, "html.parser"))


# ---------------------------------------------------------------- картинки

IMG_NAMES = ["g7-drozhzhi-pochkovanie.png", "g7-mikroskop.png", "g7-socvetiya.png"]


def extract_images(soup):
    imgs = soup.find_all("img")
    if len(imgs) != len(IMG_NAMES):
        fail(f"ожидалось {len(IMG_NAMES)} картинок в 7 классе, найдено {len(imgs)}")
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for img, name in zip(imgs, IMG_NAMES):
        m = re.match(r"data:image/(\w+);base64,(.*)", img["src"], re.S)
        (IMG_DIR / name).write_bytes(base64.b64decode(m.group(2)))
        img["src"] = "assets/img/" + name
        img["loading"] = "lazy"
        img["decoding"] = "async"
        if "style" in img.attrs:
            del img["style"]


# ---------------------------------------------------------------- общая чистка

def clean_fragment(root, prefix):
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    convert_katex(root)
    fix_styles(root)
    for svg in root.find_all("svg"):
        # height="auto" — недопустимое значение атрибута SVG; размер задают стили
        if svg.get("height") == "auto":
            del svg["height"]
    uniquify_svg_ids(root, prefix)
    # широкие таблицы прокручиваются внутри своего контейнера
    for t in root.find_all("table"):
        if t.parent and "table-wrap" in t.parent.get("class", []):
            continue
        wrap = root.new_tag("div") if hasattr(root, "new_tag") else BeautifulSoup("", "html.parser").new_tag("div")
        wrap["class"] = ["table-wrap"]
        t.wrap(wrap)


def frag(html_text, prefix):
    s = BeautifulSoup(html_text, "html.parser")
    clean_fragment(s, prefix)
    return s


def mark_option_rows(fr):
    """Строки «разбора вариантов» помечаем буквой варианта, чтобы в разборе
    подсветить ответ, который выбрала ученица."""
    for tr in fr.select("tr.ok, tr.no"):
        td = tr.find("td")
        m = re.match(r"\s*([А-ЖA-Z]|\d+)\)", td.get_text()) if td else None
        if m:
            tr["data-opt"] = m.group(1)
    for li in fr.find_all("li"):
        st = li.find(["strong", "b"])
        if st and li.contents and li.contents[0] is st:
            m = re.match(r"\s*([а-ж])\)", st.get_text())
            if m:
                li["data-opt"] = m.group(1)


# ================================================================ 7 класс

G7_T1 = "Б Б Б Б А Б А Б Г В Б Б В Г Б Б А В Б В".split()
G7_T2 = {"p1-s2-q1": "Г", "p2-s1-q1": "В", "p2-s1-q2": "В", "p2-s1-q3": "В", "p2-s1-q4": "А"}

INFLORESCENCES = [
    "кисть", "колос", "початок", "щиток", "зонтик", "серёжка", "головка", "корзинка",
    "метёлка (сложная кисть)", "сложный колос", "сложный зонтик", "сложный щиток",
    "завиток", "дихазий (развилина)", "извилина",
]

G7_TEXT = {
    "p2-s2-q1": [
        {"accept": [r"^главн(ым|ый|ой|ая|ое)$"],
         "hints": []},
        {"accept": [r"^придаточн(ым|ый|ой|ая|ое)$"],
         "hints": [{"re": r"^придат", "msg": "«Придаток» — бытовое слово. Нужен термин в той же форме, что и первое слово."},
                   {"re": r"^боков", "msg": "Боковые корни растут от других корней, а здесь корень растёт от стебля."}]},
    ],
    "p2-s2-q2": [
        {"accept": [r"^(споры|спор|спора|из споры)$"],
         "hints": [{"re": r"^зигот", "msg": "Из зиготы у мхов вырастает спорофит, а не гаметофит."},
                   {"re": r"^(протонем|предросток)", "msg": "Протонема — промежуточная стадия. А сама она из чего вырастает?"}]},
    ],
    "p2-s2-q3": [
        {"accept": [r"^камби(й|я|ем|ального кольца|альное кольцо)$"],
         "hints": [{"re": r"^кор", "msg": "Кора — это всё, что снаружи от камбия (пробка и луб). Что лежит между лубом и древесиной?"}]},
    ],
    "p2-s2-q4": [
        {"accept": [r"^(лист|листья|листок|листа)$"],
         "hints": [{"re": r"^почк", "msg": "Почка сидит в пазухе листа. А что прикреплено к самому узлу?"}]},
    ],
    "p2-s2-q5": [
        {"accept": [r"^(околоплодник|перикарпий)$"],
         "hints": [{"re": r"^(скорлуп|кожур)", "msg": "Это бытовое слово (или оболочка семени). Нужен термин для стенки плода."}]},
    ],
}

# Эталонные слова для подсказки «Показать первую букву» (сверяются с «Ответ:» в разборе).
G7_WORDS = {
    "p2-s2-q1": ["главным", "придаточным"],
    "p2-s2-q2": ["споры"],
    "p2-s2-q3": ["камбий"],
    "p2-s2-q4": ["лист"],
    "p2-s2-q5": ["околоплодник"],
}

G7_MATCH = {
    "p2-s3-q1": {"А": "3", "Б": "1", "В": "2"},
    "p2-s3-q2": {"А": "4", "Б": "5", "В": "1", "Г": "3", "Д": "2"},
}


def parse_cond_options(cond):
    """.cond → (пронумерованные утверждения, варианты с буквами)."""
    stmts, opts = [], []
    for div in cond.find_all("div"):
        cl = div.find("span", class_="cl", recursive=False)
        if not cl:
            continue
        label = cl.get_text(strip=True).rstrip(")")
        cl.extract()
        body = inner(div).strip()
        body = re.sub(r"[;.]\s*$", "", body)
        if label.isdigit():
            stmts.append({"key": label, "html": body})
        else:
            opts.append({"key": label, "html": body})
    return stmts, opts


def build_g7():
    raw = SRC7.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "lxml")
    extract_images(soup)

    data = {
        "id": "g7",
        "grade": 7,
        "year": "2014/2015",
        "stage": "Городской этап",
        "title": "Олимпиада 7 класса",
        "subtitle": "Городской этап · 2014/2015 · теоретическая часть",
        "accent": "leaf",
        "sections": [],
        "notes": [],
    }

    # --- памятки и вводные (переносим целиком)
    p1 = soup.select_one("section#p1")
    p2 = soup.select_one("section#p2")
    intro1 = p1.select_one(".intro")
    intro2 = p2.select_one(".intro")

    def section_html(h2id):
        h2 = soup.select_one(f"h2#{h2id}")
        parts = []
        for sib in h2.next_siblings:
            if isinstance(sib, Tag) and (sib.name in ("h2", "section") or "ex" in sib.get("class", [])):
                break
            if isinstance(sib, Tag) and sib.name == "p" and "totop" in sib.get("class", []):
                continue
            parts.append(str(sib))
        return text_of(h2), "".join(parts)

    t_m1, m1 = section_html("p1-s3")
    t_l1, l1 = section_html("p1-s4")
    t_m2, m2 = section_html("p2-s6")
    t_l2, l2 = section_html("p2-s7")

    data["notes"] = [
        {"id": "g7-how", "title": "Как устроен разбор",
         "html": str(frag(inner(intro1), "g7n1")) + '<h3>Вторая часть</h3>' + str(frag(inner(intro2), "g7n2"))},
        {"id": "g7-traps", "title": "Главные ловушки",
         "html": f"<h3>{t_l1}</h3>" + str(frag(l1, "g7n3")) + f"<h3>{t_l2}</h3>" + str(frag(l2, "g7n4"))},
        {"id": "g7-key", "title": "Ключ ответов", "spoiler": True,
         "html": f"<h3>{t_m1}</h3>" + str(frag(m1, "g7n5")) + f"<h3>{t_m2}</h3>" + str(frag(m2, "g7n6"))},
    ]

    # --- задания
    sections = {}
    order = []
    t1_index = 0
    for ex in soup.select("div.ex"):
        qid = ex["id"]
        h2 = ex.find_previous("h2")
        sec_title = text_of(h2)
        sec_id = h2["id"]
        if sec_id not in sections:
            sections[sec_id] = {"id": "g7-" + sec_id, "title": sec_title, "questions": []}
            order.append(sec_id)

        t = ex.select_one(".t")
        num = t.select_one(".n").get_text(strip=True).rstrip(".")
        t.select_one(".n").extract()
        stem = inner(t)

        sol = ex.select_one(".sol")
        cond_nodes, expl_nodes = [], []
        cur = cond_nodes
        for ch in list(ex.children):
            if ch is t:
                continue
            if ch is sol:
                cur = expl_nodes
                continue
            if isinstance(ch, NavigableString) and not ch.strip():
                continue
            cur.append(ch)

        ans = ex.select_one(".ans")
        # «Ответ: <span class="ok">…</span>» → только сам ответ; подпись рисует интерфейс
        answer_html = re.sub(r"^\s*Ответ:\s*", "", inner(ans.select_one(".ok") or ans)) if ans else ""
        expl_html = "".join(str(n) for n in expl_nodes if n is not ans)

        q = {"id": "g7-" + qid, "num": num, "stem": stem, "media": "", "src": "g7"}

        cond = None
        media = []
        for n in cond_nodes:
            if isinstance(n, Tag) and "cond" in n.get("class", []):
                cond = n
            else:
                media.append(n)

        if sec_id == "p1-s1":
            stmts, opts = parse_cond_options(cond)
            q.update(type="single", options=opts, answer=G7_T1[t1_index])
            t1_index += 1
        elif qid in G7_T2:
            if qid == "p2-s3-q3":
                pass
            stmts, opts = parse_cond_options(cond)
            q.update(type="single", statements=stmts, options=opts, answer=G7_T2[qid])
        elif qid in G7_TEXT:
            q.update(type="text", blanks=[{**b, "word": w} for b, w in zip(G7_TEXT[qid], G7_WORDS[qid])])
            if stem.count("……") != len(G7_TEXT[qid]):
                fail(f"{qid}: число пропусков в условии не совпадает с ключом")
        elif qid in G7_MATCH:
            table = next(n for n in media if isinstance(n, Tag) and n.name == "table")
            media.remove(table)
            left, right = [], []
            for tr in table.find_all("tr")[1:]:
                a, b = tr.find_all("td")
                ma = re.match(r"\s*([А-Ж])\)\s*(.*)", a.get_text(" ", strip=True))
                mb = re.match(r"\s*(\d+)\.\s*(.*)", b.get_text(" ", strip=True))
                left.append({"key": ma.group(1), "html": html.escape(ma.group(2).rstrip(".;"))})
                right.append({"key": mb.group(1), "html": html.escape(mb.group(2))})
            heads = [text_of(th) for th in table.find_all("th")]
            q.update(type="match", left=left, right=right, leftTitle=heads[0], rightTitle=heads[1],
                     answer=G7_MATCH[qid])
        elif qid == "p2-s3-q3":
            # Микроскоп: названия А–Ж, на рисунке цифры 1–5.
            _, names = parse_cond_options(cond)
            img = cond.find("img")
            media.insert(0, BeautifulSoup(
                f'<figure class="cond-figure">{str(img)}<figcaption>Рисунок из условия. '
                'Цифра 3 на скане видна слабо: она стоит справа вверху, у самого конца трубки.</figcaption></figure>',
                "html.parser"))
            q.update(type="match",
                     left=[{"key": str(i), "html": f"Цифра {i}"} for i in range(1, 6)], hideLeftKey=True,
                     right=[{"key": o["key"], "html": o["html"]} for o in names],
                     leftTitle="Обозначение", rightTitle="Название (двум названиям номера не достанется)",
                     answer={"1": "Г", "2": "Е", "3": "Д", "4": "Б", "5": "В"})
        elif qid == "p2-s4-q1":
            q.update(
                type="table",
                corner="№ на схеме",
                instructions="Для каждой схемы выбери название (5.1) и группу (5.2).",
                columns=[{"key": "name", "title": "Название (5.1)", "options": sorted(INFLORESCENCES, key=lambda s: s.replace("ё", "е"))},
                         {"key": "kind", "title": "Группа (5.2)", "options": ["ботрическое", "цимозное"]}],
                rows=[{"key": str(i + 1), "label": str(i + 1)} for i in range(15)],
                answer={str(i + 1): {"name": INFLORESCENCES[i],
                                     "kind": "ботрическое" if i < 12 else "цимозное"} for i in range(15)},
            )
        elif qid == "p2-s5-q1":
            crafts = ["берёзовый сок", "ивовые прутья", "липовое лыко", "береста", "смола сосны (живица)"]
            groups = [{"key": "1", "html": "1 — почти не вредят"},
                      {"key": "2", "html": "2 — ослабляют, но не губят"},
                      {"key": "3", "html": "3 — губят дерево"}]
            q.update(type="match", style="segmented",
                     left=[{"key": c, "html": c} for c in crafts], right=groups,
                     leftTitle="Промысел", rightTitle="Группа по ущербу",
                     answer={"берёзовый сок": "2", "ивовые прутья": "1", "липовое лыко": "3",
                             "береста": "1", "смола сосны (живица)": "2"},
                     instructions="Раздели промыслы на три группы по вреду для дерева.")
        else:
            fail("не знаю, как устроено задание " + qid)

        media_html = "".join(str(n) for n in media)
        mf = frag(media_html, q["id"] + "m")
        for p in mf.find_all("p"):
            p["class"] = [c for c in p.get("class", []) if c != "indent"] + ["cond-note"]
        q["media"] = str(mf).strip()
        q["stem"] = str(frag(q["stem"], q["id"] + "t")).strip()
        ef = frag(expl_html, q["id"] + "e")
        mark_option_rows(ef)
        q["explanation"] = str(ef).strip()
        q["answerHtml"] = str(frag(answer_html, q["id"] + "a")).strip()
        sections[sec_id]["questions"].append(q)

    data["sections"] = [sections[s] for s in order]
    # Короткие названия разделов для навигации
    short = {"p1-s1": "Задание 1 · один ответ", "p1-s2": "Задание 2 · с множественным выбором",
             "p2-s1": "Задание 2 · продолжение", "p2-s2": "Задание 3 · пропущенное слово",
             "p2-s3": "Задание 4 · соответствие", "p2-s4": "Задание 5 · соцветия",
             "p2-s5": "Задание 6 · промыслы"}
    for s in data["sections"]:
        s["short"] = short[s["id"][3:]]
    return data, soup


# ================================================================ 8 класс

G8_TESTS = "г б а а а в б г в б а в б а г г б а е д".split()

G8_TERMS = [
    {"accept": [r"^(метаморфоз|метаморфоза|превращение)( (метаморфоз|метаморфоза|превращение))?$"],
     "hints": [{"re": r"^линьк", "msg": "Линька — только смена покрова для роста, без перестройки органов."},
               {"re": r"^онтогенез", "msg": "Онтогенез — всё развитие целиком, а здесь речь о перестройке строения."}]},
    {"accept": [r"^конъюгаци[яи]$"],
     "near": [{"re": r"^кон[ь]?югаци[яи]$", "msg": "Верно! Только пишется с твёрдым знаком: конъюгация."}],
     "hints": [{"re": r"^копуляц", "msg": "Копуляция — полное слияние двух клеток. Здесь клетки только обмениваются ядрами."}]},
    {"accept": [r"^гемолимф[аы]$"],
     "hints": [{"re": r"^(кровь|лимфа)$", "msg": "Почти. У членистоногих кровь смешивается с полостной жидкостью, и у этой смеси есть своё название."}]},
    {"accept": [r"^регенераци[яи]$"], "hints": []},
    {"accept": [r"^мантия$"],
     "hints": [{"re": r"^раковин", "msg": "Раковина — продукт этой складки. Как называется сама складка?"}]},
    {"accept": [r"^(целом|целома|вторичная полость( тела)?|целом вторичная полость тела)$"],
     "hints": [{"re": r"^первичн", "msg": "Первичная полость не имеет собственной выстилки, а в условии — вторичная."}]},
    {"accept": [r"^(гетеротрофы|гетеротроф|гетеротрофные( организмы)?)$"],
     "hints": [{"re": r"^(сапротроф|паразит)", "msg": "Это лишь часть таких организмов. Определение шире."},
               {"re": r"^автотроф", "msg": "Автотрофы сами создают органику, а здесь — питаются готовой."}]},
    {"accept": [r"^промежуточн(ый|ого)( хозяин| хозяина)?$"],
     "hints": [{"re": r"^(окончательн|основн|дефинитивн)", "msg": "В окончательном хозяине паразит размножается половым путём. А здесь — бесполым."}]},
    {"accept": [r"^семенники$", r"^мужские половые железы$"],
     "near": [{"re": r"^семенник$", "msg": "Верно по смыслу. В бланке пиши во множественном числе: в условии «органы», значит «семенники»."}],
     "hints": [{"re": r"^(антериди|тычинк)", "msg": "Это мужские органы растений, а задание из зоологического блока."}]},
    {"accept": [r"^хорд[аы]$"],
     "hints": [{"re": r"^позвоночн", "msg": "Позвоночник состоит из позвонков, а здесь — сплошной упругий стержень."}]},
]

G8_TERM_WORDS = ["метаморфоз", "конъюгация", "гемолимфа", "регенерация", "мантия", "целом",
                 "гетеротрофы", "промежуточный хозяин", "семенники", "хорда"]

G8_TABLE_ROWS = [
    # (признак, варианты в клетке, индексы верных вариантов: рак, паук, насекомое)
    # Формулировки сокращены, чтобы помещались в клетку; полная эталонная таблица — в разборе.
    ("Покровы тела", ["известковый хитиновый панцирь", "тонкий эластичный хитин", "хитин с восковым слоем"], [0, 1, 2]),
    ("Отделы тела", ["головогрудь + брюшко", "голова + грудь + брюшко", "голова + туловище + хвост"], [0, 0, 1]),
    ("Количество ходильных ног", ["3 пары", "4 пары", "5 пар", "6 пар"], [2, 1, 0]),
    ("Органы дыхания", ["жабры", "лёгочные мешки и трахеи", "трахеи"], [0, 1, 2]),
    ("Тип кровеносной системы", ["незамкнутая", "замкнутая"], [0, 0, 0]),
    ("Сердце", ["мешковидное, на спине головогруди", "трубчатое, на спине брюшка", "трубчатое, на брюшной стороне"], [0, 1, 1]),
    ("Тип нервной системы", ["брюшная нервная цепочка", "узлы слиты в одну массу", "нервная трубка на спине"], [0, 1, 0]),
    ("Органы зрения", ["сложные глаза на стебельках", "простые глаза (обычно 8)", "сложные глаза + простые глазки"], [0, 1, 2]),
    ("Органы осязания", ["2 пары усиков", "усиков нет, осязают волоски", "1 пара усиков"], [0, 1, 2]),
]

G8_BLOCK_ORDER = ["b-algo", "b-expl", "b-traps", "b-mem", "b-viz", "b-hor"]


def split_options(p_html):
    """«а) …; б) …; в) ….» → список вариантов."""
    txt = p_html.strip()
    parts = re.split(r"(?:^|;\s*)([а-и])\)\s*", txt)
    # parts: ['', 'а', 'текст', 'б', 'текст', ...]
    if parts[0].strip():
        fail("неожиданное начало вариантов: " + txt[:60])
    opts = []
    for i in range(1, len(parts), 2):
        opts.append({"key": parts[i], "html": parts[i + 1].strip().rstrip(".").strip()})
    letters = "".join(o["key"] for o in opts)
    if letters != RU_LO[:len(letters)]:
        fail("варианты идут не по порядку: " + letters)
    return opts


def build_g8():
    raw = SRC8.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "lxml")
    data = {
        "id": "g8",
        "grade": 8,
        "year": "2016/2017",
        "stage": "Школьный этап",
        "title": "Олимпиада 8 класса",
        "subtitle": "Школьный этап · 2016/2017 · 25 заданий, 43 вопроса",
        "accent": "stain",
        "sections": [],
        "notes": [],
    }

    cover = soup.select_one("section.cover")
    idea = cover.select_one(".idea")
    keygrid = cover.select_one(".keygrid")
    legend = cover.select_one(".legend")
    legend_note = legend.find_next_sibling("p")

    sections = [
        {"id": "g8-a1", "title": "Часть А · Задание 1 — Правильные суждения", "short": "А1 · верные суждения", "questions": []},
        {"id": "g8-a2", "title": "Часть А · Задание 2 — Термины по определениям", "short": "А2 · термины", "questions": []},
        {"id": "g8-a3", "title": "Часть А · Задание 3 — Тесты", "short": "А3 · тесты 1–20", "questions": []},
        {"id": "g8-b", "title": "Часть Б — Соответствия и таблица", "short": "Часть Б", "questions": []},
        {"id": "g8-train", "title": "Бонус · Тренажёр на перенос знаний", "short": "Бонус · тренажёр", "questions": []},
    ]
    sec = {s["id"]: s for s in sections}

    for qs in soup.select("section.q"):
        qn = int(qs["id"][1:])
        head = text_of(qs.select_one(".qnum"))
        topic = text_of(qs.select_one(".qh h2"))
        cond = qs.select_one(".b-cond .bb")
        ans = qs.select_one(".b-ans .bb")
        blocks = []
        for cls in G8_BLOCK_ORDER:
            b = qs.select_one(".blk." + cls)
            if b is not None:
                blocks.append(str(b))
        qid = f"g8-q{qn}"
        ef = frag("".join(blocks), qid + "e")
        mark_option_rows(ef)
        q = {"id": qid, "src": "g8", "topic": topic, "head": head, "media": "",
             "explanation": str(ef).strip(), "answerHtml": str(frag(inner(ans), qid + "a")).strip()}

        if qn == 1:
            ps = cond.find_all("p")
            stem = inner(ps[0])
            items = [inner(li) for li in cond.select("ol > li")]
            q.update(num="1", type="multi", stem=stem,
                     options=[{"key": str(i + 1), "html": h} for i, h in enumerate(items)],
                     answer=["1", "4", "5", "7"],
                     instructions="Отметь все верные суждения.")
            sec["g8-a1"]["questions"].append(q)
        elif qn == 2:
            ps = cond.find_all("p")
            items = [inner(li) for li in cond.select("ol > li")]
            if len(items) != len(G8_TERMS):
                fail("число определений не совпадает с ключом")
            q.update(num="2", type="terms", stem=inner(ps[0]), note=inner(ps[1]),
                     items=[{"key": str(i + 1), "html": h, "word": G8_TERM_WORDS[i], **G8_TERMS[i]}
                            for i, h in enumerate(items)])
            sec["g8-a2"]["questions"].append(q)
        elif 3 <= qn <= 22:
            ps = cond.find_all("p")
            stem_p = ps[0]
            n = stem_p.find("strong").get_text(strip=True).rstrip(".")
            stem_p.find("strong").extract()
            opts = split_options(inner(ps[1]))
            extra = "".join(str(p) for p in ps[2:])
            q.update(num=n, type="single", stem=inner(stem_p).strip(), options=opts,
                     answer=G8_TESTS[int(n) - 1])
            if extra:
                q["media"] = str(frag(extra.replace("<p>", '<p class="cond-note">'), qid + "m"))
            if n == "8":
                q["optionNotes"] = {"в": "По ключу этой олимпиады верный ответ «г». "
                                         "Но у тебя есть основания: открой разбор, там есть олимпиадная оговорка."}
            sec["g8-a3"]["questions"].append(q)
        elif qn in (23, 24):
            table = cond.find("table")
            heads = [text_of(th) for th in table.find_all("th")]
            left, right = [], []
            for tr in table.select("tbody tr"):
                a, b = tr.find_all("td")
                ma = re.match(r"\s*([а-ж])\)\s*(.*)", a.get_text(" ", strip=True))
                mb = re.match(r"\s*(\d+)\.\s*(.*)", b.get_text(" ", strip=True))
                left.append({"key": ma.group(1), "html": html.escape(ma.group(2).rstrip(";").strip())})
                right.append({"key": mb.group(1), "html": html.escape(mb.group(2).strip())})
            stem = inner(cond.find("p"))
            answer = {"а": "4", "б": "3", "в": "2", "г": "6", "д": "1", "е": "5"} if qn == 23 else \
                     {"а": "4", "б": "5", "в": "1", "г": "3", "д": "2"}
            q.update(num="Б" + str(qn - 22), type="match", stem=stem, left=left, right=right,
                     leftTitle=heads[0], rightTitle=heads[1], answer=answer)
            sec["g8-b"]["questions"].append(q)
        elif qn == 25:
            stem = inner(cond.find("p"))
            cols = [{"key": "rak", "title": "Ракообразные"}, {"key": "pauk", "title": "Паукообразные"},
                    {"key": "nas", "title": "Насекомые"}]
            rows, answer = [], {}
            for i, (label, options, idx) in enumerate(G8_TABLE_ROWS):
                rk = f"r{i + 1}"
                rows.append({"key": rk, "label": label, "options": options})
                answer[rk] = {c["key"]: options[j] for c, j in zip(cols, idx)}
            q.update(num="Б3", type="table", stem=stem, corner="Признак", columns=cols, rows=rows,
                     answer=answer,
                     instructions="В каждой клетке выбери подходящий вариант. Полная эталонная таблица — в разборе.")
            sec["g8-b"]["questions"].append(q)
        else:
            fail("лишнее задание q%d" % qn)

    for q in sec["g8-a3"]["questions"]:
        q["head"] = "Тест " + q["num"]
    # «<strong>Задание 1.</strong> Выберите…» — номер уже есть в заголовке карточки
    for s_ in sections:
        for q in s_["questions"]:
            q["stem"] = re.sub(r"^\s*<strong>Задание \d+\.</strong>\s*", "", q["stem"])

    # --- итоговые разделы (fin1–fin4)
    fins = {f["id"]: f for f in soup.select("section.fin")}
    if set(fins) != {"fin1", "fin2", "fin3", "fin4"}:
        fail("не найдены итоговые разделы 8 класса")

    # Итог 4 — тренажёр: превращаем в интерактивные вопросы
    f4 = fins["fin4"]
    trains = f4.select(".train")
    keys = f4.select_one(".keys")
    key_items = keys.select("li") if keys else []
    if len(trains) != 4 or len(key_items) != 4:
        fail("тренажёр: ожидалось 4 вопроса и 4 ключа")
    train_answers = ["б", "в", "в", "в"]
    for i, (tr, key) in enumerate(zip(trains, key_items)):
        ps = tr.find_all("p")
        stem_html = inner(ps[0])
        m = re.match(r"\s*<strong>(.*?)</strong>\s*(.*)", stem_html, re.S)
        kind = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        mk = re.search(r"\((.*)\)", kind)  # «Вопрос 1 (перенос знаний).» → «Перенос знаний»
        kind = mk.group(1)[:1].upper() + mk.group(1)[1:] if mk else kind
        opts = split_options(inner(ps[1]))
        kf = frag(inner(key), f"g8-t{i + 1}e")
        key_letter = re.match(r"\s*([а-ж])\)", kf.get_text())
        if not key_letter or key_letter.group(1) != train_answers[i]:
            fail(f"тренажёр {i + 1}: ключ в исходнике не совпадает")
        q = {"id": f"g8-t{i + 1}", "src": "g8", "num": str(i + 1), "head": kind, "type": "single",
             "stem": m.group(2).strip(), "options": opts, "answer": train_answers[i], "media": "",
             "explanation": "", "answerHtml": str(kf)}
        sec["g8-train"]["questions"].append(q)

    def fin_html(fid, prefix):
        f = fins[fid]
        h2 = f.find("h2")
        title = text_of(h2)
        h2.extract()
        return title, str(frag(inner(f), prefix))

    t1, h1 = fin_html("fin1", "g8f1")
    t2, h2 = fin_html("fin2", "g8f2")
    t3, h3 = fin_html("fin3", "g8f3")

    cards = []
    for card in fins["fin3"].select(".card"):
        cards.append({"front": inner(card.select_one(".f")), "back": inner(card.select_one(".r"))})

    data["notes"] = [
        {"id": "g8-idea", "title": "Как устроен разбор",
         "html": f'<div class="idea">{inner(idea)}</div><h3>Восемь шагов разбора</h3>'
                 + str(frag(str(legend), "g8n1")) + str(frag(str(legend_note), "g8n2"))},
        {"id": "g8-cheat", "title": "Экспресс-шпаргалка", "html": h1},
        {"id": "g8-dict", "title": "Словарь корней", "html": h2},
        {"id": "g8-cards", "title": "Карточки (лист для печати)", "html": h3},
        {"id": "g8-key", "title": "Ключ ответов", "spoiler": True,
         "html": str(frag(str(keygrid), "g8n3"))},
    ]
    data["cards"] = cards

    # словарь корней → карточки «термин ↔ корни»
    dict_cards = []
    for tr in fins["fin2"].select("table tr"):
        tds = tr.find_all("td")
        if len(tds) != 3:
            continue
        dict_cards.append({"front": inner(tds[0]), "back": inner(tds[1]) + (
            "" if tds[2].get_text(strip=True) in ("—", "") else " — " + inner(tds[2]))})
    data["dictCards"] = dict_cards
    data["sections"] = sections
    return data, soup



# ================================================================ 8 класс, 2018/2019

SRC8B = ROOT / "source" / "olimpiada-8-klass-2018-2019.html"

G8B_TESTS = {1: "в", 2: "а", 3: "а", 4: "в", 5: "г", 6: "в", 7: "г", 8: "е", 9: "г", 10: "б",
             11: "в", 12: "б", 13: "в", 14: "г", 15: "в", 16: "в", 17: "б", 18: "а", 19: "а", 20: "г",
             21: "а", 23: "в", 24: "а", 25: "а", 26: "д", 27: "д", 28: "б", 29: "г", 30: "а"}

# Ответы, которые сам разбор признаёт допустимыми наравне с основным.
G8B_ALSO = {
    10: {"г": "Засчитано. Широкая стрелка на скане задевает и перицикл (корнеродный слой), поэтому такой "
              "ответ допустим. Но остриё попадает в островок мелких клеток флоэмы, и основной ответ — «б»."},
}
G8B_P1 = {"1": "ж", "2": "и", "3": "а", "4": "г", "5": "в", "6": "д"}
G8B_P2 = {"1": "а", "2": "в", "3": "а", "4": "б", "5": "е", "6": "з", "7": "ж", "8": "г"}
G8B_P2_ALT = {
    "3": {"б": "Засчитано: в некоторых ключах у муравья указывают грызуще-лижущий аппарат. "
                "Основной ответ — грызущий: мощные жвалы муравья грызут и режут."},
    "5": {"д": "Засчитано, как допускает разбор: псевдотрахеи на хоботке мухи отфильтровывают твёрдые частицы. "
                "Но основной и школьный ответ — лижущий."},
}
G8B_P3_SETS = [["2", "3", "6", "9", "12", "15"], ["2", "3", "6", "8", "12", "15"],
               ["2", "3", "5", "9", "12", "15"], ["2", "3", "5", "8", "12", "15"]]
G8B_P3_NOTE = ("Засчитано. Основной ответ: 2, 3, 6, 9, 12, 15. Разбор допускает и «тройчато-раздельный» (5) "
               "вместо «тройчато-лопастного» (6) и «округлое основание» (8) вместо «сердцевидного» (9).")
G8B_T4_ITEMS = ["фундук", "миндаль", "пшено", "перловая крупа", "гречневая крупа (ядрица)",
                "кедровый «орешек»", "манная крупа", "настоящий каштан"]
G8B_T4_GROUPS = [{"key": "I", "html": "I — настоящий орех"},
                 {"key": "II", "html": "II — семя или косточка костянки"},
                 {"key": "III", "html": "III — из зерновки злака или орешка"}]
G8B_T4 = {"фундук": "I", "миндаль": "II", "пшено": "III", "перловая крупа": "III",
          "гречневая крупа (ядрица)": "III", "кедровый «орешек»": "II", "манная крупа": "III",
          "настоящий каштан": "I"}

# Картинки в порядке появления в исходнике → имена файлов на сайте.
G8B_IMG_NAMES = [
    "g8b-oblozhka.jpg", "g8b-t08-kletka.jpg", "g8b-t09-spirogira.jpg", "g8b-t10-koren-irisa.png",
    "g8b-t17-veliger.jpg", "g8b-t18-lichinki.jpg", "g8b-t27-pauk.png", "g8b-p1-kollazh.jpg",
    "g8b-p1-2.jpg", "g8b-p1-3.jpg", "g8b-p1-4.jpg", "g8b-p1-5.jpg", "g8b-p1-6.png",
    "g8b-p2-1.jpg", "g8b-p2-2.jpg", "g8b-p2-3.jpg", "g8b-p2-4.jpg", "g8b-p2-5.jpg", "g8b-p2-6.jpg",
    "g8b-p2-7.jpg", "g8b-p2-8.jpg", "g8b-p3-list.jpg",
]
G8B_HEADS = {"3": "b-algo", "4": "b-expl", "5": "b-traps", "6": "b-mem", "7": "b-viz", "8": "b-hor"}


def extract_images_g8b(soup):
    """Сохраняет картинки новой олимпиады. Обложку уменьшаем, чёрно-белые схемы
    переводим в оттенки серого (содержимое не меняется, файл легче)."""
    imgs = soup.find_all("img")
    if len(imgs) != len(G8B_IMG_NAMES):
        fail(f"ожидалось {len(G8B_IMG_NAMES)} картинок в олимпиаде 2018/2019, найдено {len(imgs)}")
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        Image = None
    import io
    for img, name in zip(imgs, G8B_IMG_NAMES):
        m = re.match(r"data:image/(\w+);base64,(.*)", img["src"], re.S)
        raw = base64.b64decode(m.group(2))
        out = IMG_DIR / name
        if Image is not None:
            im = Image.open(io.BytesIO(raw))
            if name == "g8b-oblozhka.jpg":
                im = im.convert("RGB")
                im.thumbnail((1100, 1100))
                im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
            elif name in ("g8b-t10-koren-irisa.png", "g8b-t27-pauk.png"):
                im.convert("L").save(out, "PNG", optimize=True)
            elif name.endswith(".jpg") and m.group(1) in ("jpeg", "jpg"):
                out.write_bytes(raw)
            elif name.endswith(".png") and m.group(1) == "png":
                out.write_bytes(raw)
            else:
                im.convert("RGB").save(out, "JPEG", quality=88)
            if name == "g8b-p1-kollazh.jpg":
                # Иллюстрация 1 бланка — левый верхний кадр коллажа (мульчирование)
                crop = Image.open(io.BytesIO(raw)).convert("RGB").crop((0, 0, 132, 76))
                crop.resize((264, 152), Image.LANCZOS).save(IMG_DIR / "g8b-p1-1.jpg", "JPEG", quality=90)
        else:
            out.write_bytes(raw)
        img["src"] = "assets/img/" + name
        img["loading"] = "lazy"
        img["decoding"] = "async"
        if "style" in img.attrs:
            del img["style"]


def entry_parts(entry):
    """Раздел задания → {номер шага: (заголовок, html)}; шаги 1–8 из разбора."""
    parts, cur, buf, title = {}, None, [], None
    for ch in entry.children:
        if isinstance(ch, Tag) and ch.name in ("h3", "h4"):
            if cur:
                parts[cur] = (title, "".join(str(x) for x in buf))
            t = text_of(ch)
            mm = re.match(r"(\d)\.\s*(.*)", t)
            cur, title = (mm.group(1), mm.group(2)) if mm else (None, None)
            buf = []
            continue
        if isinstance(ch, Tag) and ch.name == "h2":
            continue
        if cur:
            buf.append(ch)
    if cur:
        parts[cur] = (title, "".join(str(x) for x in buf))
    return parts


def blocks_html(parts):
    out = []
    for num in ("3", "4", "5", "6", "7", "8"):
        if num not in parts:
            continue
        title, html_ = parts[num]
        out.append(f'<div class="blk {G8B_HEADS[num]}"><div class="bl"><span class="bn">{num}</span>{html.escape(title)}</div>'
                   f'<div class="bb">{html_}</div></div>')
    return "".join(out)


def strip_answer_label(h):
    return re.sub(r"Эталонный ответ(?:\s*\([^)]*\))?:\s*", "", h, count=1).strip()


def build_g8b():
    raw = SRC8B.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "lxml")
    for sc in soup.find_all("script"):
        sc.decompose()
    extract_images_g8b(soup)
    data = {
        "id": "g8b", "grade": 8, "year": "2018/2019", "stage": "Олимпиада",
        "title": "Олимпиада 8 класса, 2018/2019",
        "subtitle": "Олимпиада · 2018/2019 · 29 тестов и 3 практических задания",
        "sections": [], "notes": [],
    }
    sections = [
        {"id": "g8b-test", "title": "Тестовая часть (№ 1–30, номера 22 в бланке нет)", "short": "Тесты 1–30", "questions": []},
        {"id": "g8b-pract", "title": "Практическая часть", "short": "Практика", "questions": []},
        {"id": "g8b-train", "title": "Бонус · Тренажёр на перенос знаний", "short": "Бонус · тренажёр", "questions": []},
    ]
    sec = {x["id"]: x for x in sections}

    for entry in soup.select("section.entry"):
        tid = entry["id"]
        qid = "g8b-" + tid
        parts = entry_parts(entry)
        cond = entry.select_one(".condition-block")
        topic = re.sub(r"^(?:Практическое )?[Зз]адание \d+:\s*", "", text_of(entry.find("h2")))
        ans_html = strip_answer_label(parts["2"][1])
        ef = frag(blocks_html(parts), qid + "e")
        mark_option_rows(ef)
        if tid == "task-1":
            for tx in ef.find_all("text", attrs={"y": "206"}):
                name, _, rest = tx.get_text().partition(" (")
                x = tx["x"]
                tx.clear()
                l1 = ef.new_tag("tspan", attrs={"x": x, "y": "200"}); l1.string = name
                l2 = ef.new_tag("tspan", attrs={"x": x, "y": "214"}); l2.string = "(" + rest
                tx.append(l1); tx.append(l2)
        q = {"id": qid, "src": "g8b", "topic": topic, "media": "",
             "explanation": str(ef).strip(), "answerHtml": str(frag(ans_html, qid + "a")).strip()}
        first = cond.find("p")
        title_txt = text_of(cond)
        if title_txt.startswith("Практическая часть") or "Практическая часть" in text_of(first):
            ps = cond.find_all("p", recursive=False)
            pnum = re.search(r"Задание (\d)", text_of(ps[0])).group(1)
            stem_html = re.sub(r"^\s*<strong>\d\.\s*", "<strong>", inner(ps[1]))
            stem_html = re.sub(r"^<strong>(.*)</strong>$", r"\1", stem_html.strip(), flags=re.S)
            q.update(num="П" + pnum, head=f"Практическая часть · задание {pnum}", stem=stem_html)
            if pnum == "1":
                opts = split_options(inner(ps[2]))
                note = ps[-1]
                q.update(type="match", left=[{"key": str(i), "html": f'<img src="assets/img/g8b-p1-{i}.{"png" if i == 6 else "jpg"}" alt="Иллюстрация {i}" loading="lazy"><span>Иллюстрация {i}</span>'} for i in range(1, 7)],
                         right=opts, leftTitle="Иллюстрация", rightTitle="Агротехнический приём (три лишних)",
                         hideLeftKey=True, answer=G8B_P1, imgRows=True,
                         instructions="Для каждой иллюстрации выбери приём. Нажми на картинку, чтобы увеличить.")
                q["media"] = str(frag(str(note).replace("<p>", '<p class="cond-note">', 1), qid + "m"))
                # исходный коллаж бланка остаётся в разборе
                coll = '<figure><img src="assets/img/g8b-p1-kollazh.jpg" alt="Коллаж из бланка" loading="lazy"><figcaption>Исходный коллаж из бланка (рисунки 1–5). Под рисунком 2 на нём видна пикировка, поверх был наложен рисунок пасынкования; рисунок 6 в PDF сместился наверх.</figcaption></figure>'
                q["explanation"] = coll + q["explanation"]
            elif pnum == "2":
                opts = split_options(re.sub(r"\s*\(8 баллов\)\s*$", "", inner(ps[2])))
                names = [text_of(th) for t in cond.find_all("table") for th in t.find_all("th")]
                imgs = [im for t in cond.find_all("table") for im in t.find_all("img")]
                left = []
                for i, (nm, im) in enumerate(zip(names, imgs)):
                    mm = re.match(r"(\d)\s*\((.*)\)", nm)
                    left.append({"key": mm.group(1), "html": f'{str(im)}<span>{mm.group(1)}. {html.escape(mm.group(2))}</span>'})
                q.update(type="match", left=left, right=opts, leftTitle="Насекомое", rightTitle="Тип ротового аппарата",
                         hideLeftKey=True, answer=G8B_P2, altAnswers=G8B_P2_ALT, imgRows=True,
                         instructions="Для каждого насекомого выбери тип ротового аппарата.")
            else:
                items = [inner(li) for li in cond.select("ol > li")]
                fig = cond.find("figure")
                q.update(type="multi", options=[{"key": str(i + 1), "html": h} for i, h in enumerate(items)],
                         answer=G8B_P3_SETS[0], acceptSets=G8B_P3_SETS, setNote=G8B_P3_NOTE,
                         instructions="Отметь все признаки, которые подходят листу на фотографии.")
                q["media"] = str(frag(str(fig), qid + "m"))
            sec["g8b-pract"]["questions"].append(q)
            continue

        # тестовая часть
        ps = cond.find_all("p", recursive=False)
        stem_p = next(p_ for p_ in ps if p_.find("strong") and re.match(r"\s*\d+\.", p_.get_text()))
        n = int(re.match(r"\s*(\d+)\.", stem_p.get_text()).group(1))
        stem = re.sub(r"^\s*<strong>\s*\d+\.\s*", "<strong>", inner(stem_p))
        stem = re.sub(r"^<strong>(.*)</strong>$", r"\1", stem.strip(), flags=re.S)
        opts = []
        for li in cond.select("ul > li"):
            mm = re.match(r"\s*([а-ж])\)\s*(.*)", li.get_text(" ", strip=True), re.S)
            body = re.sub(r"^\s*[а-ж]\)\s*", "", inner(li))
            opts.append({"key": mm.group(1), "html": re.sub(r"[;.]\s*$", "", body).strip()})
        letters = "".join(o["key"] for o in opts)
        if letters != RU_LO[:len(letters)]:
            fail(f"тест {n}: варианты не по порядку ({letters})")
        stmts = []
        notes = []
        for p_ in ps:
            if p_ is stem_p:
                continue
            t = p_.get_text(" ", strip=True)
            if re.match(r"\s*1\s*[)–-]", t):
                for mm in re.finditer(r"(\d+)\s*[)–-]\s*([^;]+?)(?:;|\.?$)", t):
                    stmts.append({"key": mm.group(1), "html": html.escape(mm.group(2).strip())})
            else:
                notes.append(str(p_).replace("<p>", '<p class="cond-note">', 1))
        media = notes + [str(f) for f in cond.find_all("figure")]
        q.update(num=str(n), head=f"Тест {n}", type="single", stem=stem, options=opts, answer=G8B_TESTS[n])
        if stmts:
            q["statements"] = stmts
        if n in G8B_ALSO:
            q["alsoAccept"] = G8B_ALSO[n]
        if media:
            q["media"] = str(frag("".join(media), qid + "m"))
        sec["g8b-test"]["questions"].append(q)

    # --- итоговый блок
    sb = soup.select_one("#summary-block")
    h3s = sb.find_all("h3")

    def after(h):
        buf = []
        for sib in h.next_siblings:
            if isinstance(sib, Tag) and sib.name == "h3":
                break
            buf.append(sib)
        return buf

    cheat = "".join(str(x) for x in after(h3s[0]))
    dict_nodes = after(h3s[1])
    card_nodes = after(h3s[2])
    train_nodes = after(h3s[3])
    dict_html = "".join(str(x) for x in dict_nodes)
    cards_html = "".join(str(x) for x in card_nodes)

    cards = []
    for tr in BeautifulSoup(cards_html, "html.parser").select("tbody tr"):
        tds = tr.find_all("td")
        cards.append({"front": inner(tds[1]), "back": inner(tds[2])})
    dict_cards = []
    for tr in BeautifulSoup(dict_html, "html.parser").select("tbody tr"):
        tds = tr.find_all("td")
        dict_cards.append({"front": inner(tds[0]), "back": inner(tds[1]) + " — " + inner(tds[2])})

    # тренажёр: задачи 1–3 — открытые (сверка с ключом), задача 4 — распределение по группам
    tasks = [x for x in train_nodes if isinstance(x, Tag) and x.name == "p" and re.match(r"\s*Задача \d", x.get_text())]
    keys_ul = next(x for x in train_nodes if isinstance(x, Tag) and x.name == "ul")
    keys = keys_ul.find_all("li", recursive=False)
    if len(tasks) != 4 or len(keys) != 4:
        fail("тренажёр 2018/2019: ожидалось 4 задачи и 4 ключа")
    for i, (tp, key) in enumerate(zip(tasks, keys)):
        strong = tp.find("strong")
        head = re.sub(r"^Задача \d+\s*\((.*)\):?$", r"\1", text_of(strong)).split(" — ")[0]
        strong.extract()
        br = tp.find("br")
        if br:
            br.extract()
        body = inner(tp).strip()
        key_html = re.sub(r"^\s*<strong>Ключ к Задаче \d:</strong>\s*", "", inner(key))
        key_html = re.sub(r"\s+(<strong>(?:[бвг]\)|Группа II|Группа III))", r"<br>\1", key_html)
        q = {"id": f"g8b-t{i + 1}", "src": "g8b", "num": str(i + 1), "head": head, "media": "",
             "stem": body, "explanation": "", "answerHtml": str(frag(key_html, f"g8b-t{i + 1}a")).strip()}
        if i < 3:
            q.update(type="open")
        else:
            q.update(type="match", style="segmented", left=[{"key": x, "html": html.escape(x)} for x in G8B_T4_ITEMS],
                     right=G8B_T4_GROUPS, answer=G8B_T4, leftTitle="Продукт", rightTitle="Группа",
                     stem="Распредели продукты по трём группам: чем каждый из них является с точки зрения ботаники.",
                     note=body)
        sec["g8b-train"]["questions"].append(q)

    # --- памятки
    hero = soup.select_one(".hero-banner")
    cover = hero.find("img")
    data["notes"] = [
        {"id": "g8b-about", "title": "Об этой олимпиаде",
         "html": str(frag(f'<figure>{str(cover)}</figure><h3>{html.escape(text_of(hero.find("h1")))}</h3>'
                          f'<p>{inner(hero.find("p"))}</p>'
                          '<p>Каждое задание разобрано по шагам: алгоритм олимпиадного мышления, послойное объяснение '
                          'с разбором всех вариантов, типичные ошибки и ловушки, приёмы запоминания, схема и олимпиадный горизонт.</p>', "g8bn0"))},
        {"id": "g8b-cheat", "title": "Экспресс-шпаргалка и ответы", "spoiler": True, "html": str(frag(cheat, "g8bn1"))},
        {"id": "g8b-dict", "title": "Словарь корней", "html": str(frag(dict_html, "g8bn2"))},
        {"id": "g8b-cards", "title": "Карточки (таблица)", "html": str(frag(cards_html, "g8bn3"))},
    ]
    data["cards"] = cards
    data["dictCards"] = dict_cards
    data["sections"] = sections
    return data, soup


def verify_g8b(o, soup):
    problems = []
    tests = o["sections"][0]["questions"]
    if [int(q["num"]) for q in tests] != sorted(G8B_TESTS):
        problems.append("2018/2019: номера тестов не совпадают с ключом")
    for q in tests:
        at = BeautifulSoup(q["answerHtml"], "html.parser").get_text(" ", strip=True)
        if not at.startswith(q["answer"] + ")"):
            problems.append(f"{q['id']} (тест {q['num']}): эталон «{at[:40]}» ≠ ключ {q['answer']}")
        if q["answer"] not in [x["key"] for x in q["options"]]:
            problems.append(f"{q['id']}: ответа нет среди вариантов")
        for k in q.get("alsoAccept", {}):
            if not re.search(r"или\s+" + k + r"\)", at):
                problems.append(f"{q['id']}: дополнительный ответ {k} не упомянут в эталоне")
        if q.get("statements"):
            opt = next(x for x in q["options"] if x["key"] == q["answer"])
            nums = re.findall(r"\d+", BeautifulSoup(opt["html"], "html.parser").get_text())
            if not all(n in [s_["key"] for s_ in q["statements"]] for n in nums):
                problems.append(f"{q['id']}: вариант ссылается на несуществующий пункт")
    # сверка с экспресс-шпаргалкой (отдельная таблица ответов в том же файле)
    sb = soup.select_one("#summary-block table")
    sheet = {}
    for tr in sb.select("tbody tr"):
        tds = tr.find_all("td")
        mm = re.match(r"Тест №(\d+)", tds[0].get_text(strip=True))
        if mm:
            sheet[int(mm.group(1))] = tds[2].get_text(" ", strip=True)
    for q in tests:
        n = int(q["num"])
        if n not in sheet or not sheet[n].startswith(q["answer"] + ")"):
            problems.append(f"тест {n}: в шпаргалке «{sheet.get(n, '—')[:30]}», в ключе {q['answer']}")
    pr = o["sections"][1]["questions"]
    a1 = BeautifulSoup(pr[0]["answerHtml"], "html.parser").get_text(" ", strip=True)
    if dict(re.findall(r"(\d) — ([а-и])\)", a1)) != G8B_P1:
        problems.append("практика 1: ключ не совпадает с эталоном")
    a2 = BeautifulSoup(pr[1]["answerHtml"], "html.parser").get_text(" ", strip=True)
    if dict(re.findall(r"(\d) \([^)]*\) — ([а-з])\)", a2)) != G8B_P2:
        problems.append("практика 2: ключ не совпадает с эталоном " + str(re.findall(r"(\d) \([^)]*\) — ([а-з])\)", a2)))
    for row, alts in G8B_P2_ALT.items():
        for k in alts:
            if not re.search(r"или[^)]*?" + k + r"\)", a2):
                problems.append(f"практика 2: альтернатива {row}–{k} не упомянута в эталоне")
    a3 = BeautifulSoup(pr[2]["answerHtml"], "html.parser").get_text(" ", strip=True)
    if not a3.startswith("2, 3, 6, 9 (или 8), 12, 15") or "5 — тройчато-раздельный" not in a3:
        problems.append("практика 3: эталон изменился: " + a3[:60])
    tr = o["sections"][2]["questions"][3]
    at = BeautifulSoup(tr["answerHtml"], "html.parser").get_text(" ", strip=True)
    groups = {"I": re.search(r"Группа I \(.*?\):(.*?)Группа II", at).group(1),
              "II": re.search(r"Группа II \(.*?\):(.*?)Группа III", at).group(1),
              "III": re.search(r"Группа III \(.*?\):(.*)$", at).group(1)}
    for i, item in enumerate(G8B_T4_ITEMS):
        g = G8B_T4[item]
        if f"{i + 1})" not in groups[g]:
            problems.append(f"тренажёр 4: «{item}» в эталоне не в группе {g}")
    return problems


# ================================================================ проверка

def verify(g7, s7, g8, s8):
    problems = []

    # 7 класс: ключ к заданию 1 — по итоговой матрице ответов исходника
    mat = s7.select_one("h2#p1-s3").find_next("table")
    letters = [td.get_text(strip=True) for tr in mat.find_all("tr") for td in tr.find_all("td")[1:]]
    if letters != G7_T1:
        problems.append(f"7 кл., задание 1: матрица {letters} ≠ ключ {G7_T1}")

    for sec in g7["sections"]:
        for q in sec["questions"]:
            ans_txt = BeautifulSoup(q["answerHtml"], "html.parser").get_text(" ", strip=True)
            if q["type"] == "single":
                if not ans_txt.startswith(q["answer"] + ")"):
                    problems.append(f"{q['id']}: «Ответ» в разборе ({ans_txt[:30]}) ≠ ключ {q['answer']}")
                ok_rows = re.findall(r'<tr class="ok" data-opt="([^"]+)"', q["explanation"])
                if ok_rows and ok_rows != [q["answer"]] and not all(r.isdigit() for r in ok_rows):
                    problems.append(f"{q['id']}: строка ✔ в разборе {ok_rows} ≠ ключ {q['answer']}")
                keys = [o["key"] for o in q["options"]]
                if q["answer"] not in keys:
                    problems.append(f"{q['id']}: ответа нет среди вариантов")
                if q.get("statements"):
                    opt = next(o for o in q["options"] if o["key"] == q["answer"])
                    stmt_ok = re.findall(r'<tr class="ok" data-opt="(\d+)"', q["explanation"])
                    nums = re.findall(r"\d+", opt["html"])
                    if stmt_ok and stmt_ok != nums:
                        problems.append(f"{q['id']}: верные пункты в разборе {stmt_ok} ≠ вариант {nums}")
            if q["type"] == "match":
                for k, v in q["answer"].items():
                    if k not in [x["key"] for x in q["left"]] or v not in [x["key"] for x in q["right"]]:
                        problems.append(f"{q['id']}: битая пара {k}-{v}")
                if q["id"] in ("g7-p2-s3-q1", "g7-p2-s3-q2"):
                    pairs = re.findall(r"([А-Ж])–(\d)", ans_txt)
                    if dict(pairs) != q["answer"]:
                        problems.append(f"{q['id']}: ответ в разборе {pairs} ≠ ключ")
                if q["id"] == "g7-p2-s3-q3":
                    pairs = re.findall(r"(\d) — ([А-Ж])", ans_txt)
                    if dict(pairs) != q["answer"]:
                        problems.append(f"{q['id']}: ответ в разборе {pairs} ≠ ключ")
            if q["type"] == "text":
                for b in q["blanks"]:
                    pass
            if q["type"] == "table" and q["id"] == "g7-p2-s4-q1":
                # сверяем с заполненной матрицей задания 5 в разборе
                ex = BeautifulSoup(q["explanation"], "html.parser")
                mtab = [t for t in ex.find_all("table") if "Название (5.1)" in t.get_text()][0]
                for tr in mtab.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    n, name, b, c = tds
                    exp = q["answer"][n]
                    if name != exp["name"]:
                        problems.append(f"соцветие {n}: в разборе «{name}», в ключе «{exp['name']}»")
                    kind = "ботрическое" if b == "Х" else "цимозное" if c == "Х" else "?"
                    if kind != exp["kind"]:
                        problems.append(f"соцветие {n}: группа в разборе {kind}, в ключе {exp['kind']}")

    # текстовые ответы 7 класса — сверяем с «Ответ: …»
    for sec in g7["sections"]:
        for q in sec["questions"]:
            if q["type"] != "text":
                continue
            ans_txt = BeautifulSoup(q["answerHtml"], "html.parser").get_text(" ", strip=True)
            words = [w.strip(" .") for w in re.sub(r"^Ответ:\s*", "", ans_txt).split(";")]
            for b, w in zip(q["blanks"], words):
                if not any(re.match(r, normalize(w)) for r in b["accept"]):
                    problems.append(f"{q['id']}: эталон «{w}» не принимается проверкой")
                if b["word"] != w:
                    problems.append(f"{q['id']}: слово подсказки «{b['word']}» ≠ ответ «{w}»")

    # 8 класс: тесты — по ключу из обложки и по «Эталонному ответу»
    kg = s8.select_one(".keygrid")
    t3 = kg.find_all("table")[1]
    key = {}
    for tr in t3.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) == 4:
            key[tds[0].get_text(strip=True)] = tds[1].get_text(strip=True).rstrip("*")
            key[tds[2].get_text(strip=True)] = tds[3].get_text(strip=True).rstrip("*")
    for i, a in enumerate(G8_TESTS):
        if key.get(str(i + 1)) != a:
            problems.append(f"8 кл., тест {i + 1}: ключ обложки {key.get(str(i + 1))} ≠ {a}")
    for sec in g8["sections"]:
        for q in sec["questions"]:
            at = BeautifulSoup(q["answerHtml"], "html.parser").get_text(" ", strip=True)
            if q["type"] == "single" and not q["id"].startswith("g8-t"):
                if not at.startswith(q["answer"] + ")"):
                    problems.append(f"{q['id']}: эталон «{at[:40]}» ≠ ключ {q['answer']}")
            if q["type"] == "multi":
                nums = re.findall(r"\d+", at.split(".")[0])
                if nums != q["answer"]:
                    problems.append(f"{q['id']}: эталон {nums} ≠ ключ {q['answer']}")
            if q["type"] == "match":
                pairs = dict(re.findall(r"([а-ж]) – (\d)", at))
                if pairs != q["answer"]:
                    problems.append(f"{q['id']}: эталон {pairs} ≠ ключ {q['answer']}")
            if q["type"] == "terms":
                found = re.findall(r"(\d+) — (.*?)(?:;|\.$)", at)
                for (n, word), item in zip(found, q["items"]):
                    w = re.sub(r"\s*\(.*?\)", "", word).strip()
                    if not any(re.match(r, normalize(w)) for r in item["accept"]):
                        problems.append(f"{q['id']} п.{n}: эталон «{w}» не принимается проверкой")
                    if item["word"] != w:
                        problems.append(f"{q['id']} п.{n}: слово подсказки «{item['word']}» ≠ ответ «{w}»")
                if len(found) != len(q["items"]):
                    problems.append(f"{q['id']}: в эталоне {len(found)} терминов")
            if q["type"] == "table":
                for r in q["rows"]:
                    for c in q["columns"]:
                        if q["answer"][r["key"]][c["key"]] not in r["options"]:
                            problems.append(f"{q['id']}: нет ответа среди вариантов ({r['label']})")
    return problems


def normalize(s):
    s = s.lower().replace("ё", "е")
    s = re.sub(r"[«»\"'().,;:!?…]", " ", s)
    s = s.replace("—", " ").replace("–", " ")
    return re.sub(r"\s+", " ", s).strip()


def main():
    g7, s7 = build_g7()
    g8, s8 = build_g8()
    g8b, s8b = build_g8b()
    problems = verify(g7, s7, g8, s8) + verify_g8b(g8b, s8b)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        fail(f"проверка ключей не пройдена ({len(problems)})")
    payload = {"olympiads": [g7, g8, g8b]}
    js = ("/* Сгенерировано tools/build_data.py из файлов в source/. Не редактировать вручную. */\n"
          "window.OLYMPIAD_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text(js, encoding="utf-8")
    nq = sum(len(s["questions"]) for o in (g7, g8, g8b) for s in o["sections"])
    print(f"Готово: {OUT_JS.relative_to(ROOT)}; вопросов: {nq}, {len(js) // 1024} КБ; ключи сверены.")


if __name__ == "__main__":
    main()
