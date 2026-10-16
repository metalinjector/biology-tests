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
RU_LO = "абвгдеж"


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
    parts = re.split(r"(?:^|;\s*)([а-ж])\)\s*", txt)
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
    problems = verify(g7, s7, g8, s8)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        fail(f"проверка ключей не пройдена ({len(problems)})")
    payload = {"olympiads": [g7, g8]}
    js = ("/* Сгенерировано tools/build_data.py из файлов в source/. Не редактировать вручную. */\n"
          "window.OLYMPIAD_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n")
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)
    OUT_JS.write_text(js, encoding="utf-8")
    nq = sum(len(s["questions"]) for o in (g7, g8) for s in o["sections"])
    print(f"Готово: {OUT_JS.relative_to(ROOT)}; вопросов: {nq}, {len(js) // 1024} КБ; ключи сверены.")


if __name__ == "__main__":
    main()
