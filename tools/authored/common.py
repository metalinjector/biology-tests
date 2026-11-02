"""Общие средства для авторских разборов (олимпиады, к которым не было готового разбора).

Тексты пишутся в простой разметке, похожей на Markdown:
  абзацы через пустую строку; «- » — маркированный список; «1. » — нумерованный;
  строки «| … |» — таблица (первая строка — заголовок); блок с «! » — правило-предупреждение;
  **жирный**, *курсив*, [ОУ] — метка «Олимпиадный уровень»; блок, начинающийся с «<», — готовый HTML.
"""
import html
import re

OU = '<span class="ou">Олимпиадный уровень (старшие классы)</span>'


def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", t)
    t = t.replace("[ОУ]", OU)
    t = re.sub(r"\^(\d+n?|[+\-]?\d*)\^", r"<sup>\1</sup>", t)
    t = re.sub(r"~(\d+)~", r"<sub>\1</sub>", t)
    return t


def md(text):
    """Мини-Markdown → HTML."""
    if text is None:
        return ""
    out = []
    blocks = re.split(r"\n\s*\n", text.strip("\n"))
    for b in blocks:
        b = b.strip("\n")
        if not b.strip():
            continue
        lines = [ln.rstrip() for ln in b.split("\n")]
        first = lines[0].lstrip()
        if first.startswith("<"):
            out.append(b.strip())
        elif all(ln.lstrip().startswith("- ") or ln.startswith("  ") for ln in lines) and first.startswith("- "):
            items, cur = [], None
            for ln in lines:
                if ln.lstrip().startswith("- ") and not ln.startswith("    "):
                    if cur is not None:
                        items.append(cur)
                    cur = ln.lstrip()[2:]
                else:
                    cur += " " + ln.strip()
            items.append(cur)
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
        elif re.match(r"\d+\.\s", first):
            items, cur = [], None
            for ln in lines:
                m = re.match(r"\s*\d+\.\s+(.*)", ln)
                if m:
                    if cur is not None:
                        items.append(cur)
                    cur = m.group(1)
                else:
                    cur += " " + ln.strip()
            items.append(cur)
            out.append("<ol>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ol>")
        elif first.startswith("|"):
            rows = [ln.strip().strip("|").split("|") for ln in lines if not re.match(r"^\s*\|[\s:|-]+\|\s*$", ln)]
            head, body = rows[0], rows[1:]
            h = "<thead><tr>" + "".join(f"<th>{_inline(c.strip())}</th>" for c in head) + "</tr></thead>"
            bd = "<tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c.strip())}</td>" for c in r) + "</tr>" for r in body) + "</tbody>"
            out.append(f"<table>{h}{bd}</table>")
        elif first.startswith("! "):
            body = " ".join(ln.strip() for ln in lines)[2:]
            out.append(f'<div class="rule"><span class="rule-ic">!</span><div><p>{_inline(body)}</p></div></div>')
        else:
            out.append("<p>" + _inline(" ".join(ln.strip() for ln in lines)) + "</p>")
    return "\n".join(out)


BLOCKS = [
    ("algo", "b-algo", "3", "Алгоритм олимпиадного мышления"),
    ("expl", "b-expl", "4", "Послойное объяснение и разбор вариантов"),
    ("traps", "b-traps", "5", "Типичные ошибки и ловушки"),
    ("mem", "b-mem", "6", "Как запомнить"),
    ("viz", "b-viz", "7", "Визуализация"),
    ("hor", "b-hor", "8", "Олимпиадный горизонт"),
]


def explanation(q):
    """Шаги 3–8 разбора в разметке, общей с прежними разборами (.blk)."""
    parts = []
    for key, cls, num, title in BLOCKS:
        v = q.get(key)
        if not v:
            continue
        if key == "viz":
            svg, cap = v if isinstance(v, tuple) else (v, "")
            body = f'<div class="svgwrap">{svg}</div>' + (f'<div class="cap">{html.escape(cap)}</div>' if cap else "")
        else:
            body = md(v)
        parts.append(f'<div class="blk {cls}"><div class="bl"><span class="bn">{num}</span>{title}</div>'
                     f'<div class="bb">{body}</div></div>')
    return "".join(parts)


# ---------------------------------------------------------------- SVG-помощники
# Рисунки выводятся на светлой «пластинке» в обеих темах, поэтому цвета заданы явно.

INK = "#1f2d2a"
MUTED = "#5b6b66"
PAL = {
    "green": ("#e3f1e6", "#2f7a3b"), "blue": ("#e4edf9", "#2463a6"), "orange": ("#fdeee2", "#c2410c"),
    "violet": ("#efe9fb", "#6d4bc4"), "teal": ("#e0f2f5", "#0e7490"), "gold": ("#faf1dc", "#8a6512"),
    "red": ("#fbe5e7", "#b4232c"), "grey": ("#eef1f0", "#5b6b66"),
}


def esc(t):
    return html.escape(str(t), quote=True)


def svg(w, h, body, label=""):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(label)}">'
            f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>{body}</svg>')


def text(x, y, t, size=13, weight=400, anchor="middle", fill=INK, italic=False):
    lines = t.split("\n")
    st = ' font-style="italic"' if italic else ""
    if len(lines) == 1:
        return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{st}>{esc(t)}</text>'
    out = f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{st}>'
    for i, ln in enumerate(lines):
        out += f'<tspan x="{x}" dy="{0 if i == 0 else size * 1.25:.1f}">{esc(ln)}</tspan>'
    return out + "</text>"


def text_w(t, size, weight=400):
    """Примерная ширина строки (Noto Sans; кириллица чуть шире латиницы)."""
    return len(t) * size * (0.62 if weight >= 600 else 0.56)


def fit(t, width, size, weight=600, min_size=10.0, wrap=True):
    """Вписывает подпись в ширину: сначала перенос по пробелу ближе к середине, затем уменьшение шрифта."""
    lines = t.split("\n")
    if max(text_w(ln, size, weight) for ln in lines) <= width:
        return t, size
    if wrap and len(lines) == 1 and " " in t:
        words = t.split(" ")
        best = min(((" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))),
                   key=lambda ab: max(len(ab[0]), len(ab[1])))
        lines = list(best)
    s = size
    while max(text_w(ln, s, weight) for ln in lines) > width and s > min_size:
        s -= 0.5
    return "\n".join(lines), s


def box(x, y, w, h, t, color="grey", size=13, weight=600, sub=None, r=10):
    fill, stroke = PAL[color]
    t, size = fit(t, w - 12, size, weight)
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    n = t.count("\n") + 1
    ty = y + h / 2 - (n - 1) * size * 0.62 + size * 0.36 - (7 if sub else 0)
    out += text(x + w / 2, ty, t, size, weight, fill=stroke if weight >= 600 else INK)
    if sub:
        sub, ss = fit(sub, w - 10, 11, 400, min_size=9, wrap=False)
        out += text(x + w / 2, y + h - 10, sub, ss, 400, fill=MUTED)
    return out


def arrow(x1, y1, x2, y2, color=INK, dash=False, width=1.6):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" marker-end="url(#ar)"{d}/>'


def chain(items, colors=None, title=None, w=760, box_h=56, gap=26, size=13, label="", subs=None):
    """Цепочка блоков слева направо со стрелками (переносится на вторую строку при необходимости)."""
    n = len(items)
    per_row = n if n <= 5 else (n + 1) // 2
    bw = (w - 40 - gap * (per_row - 1)) / per_row
    rows = (n + per_row - 1) // per_row
    if any("\n" in fit(it, bw - 12, size)[0] for it in items):
        box_h += 16 if subs else 12
    top = 40 if title else 14
    h = top + rows * (box_h + 40) - 20
    body = text(w / 2, 24, title, 15, 700) if title else ""
    for i, it in enumerate(items):
        r, c = divmod(i, per_row)
        x = 20 + c * (bw + gap)
        y = top + r * (box_h + 40)
        col = (colors[i] if colors else "blue")
        body += box(x, y, bw, box_h, it, col, size, sub=(subs[i] if subs else None))
        if i < n - 1:
            if c < per_row - 1:
                body += arrow(x + bw + 2, y + box_h / 2, x + bw + gap - 2, y + box_h / 2)
            else:
                body += arrow(x + bw / 2, y + box_h + 2, 20 + bw / 2, y + box_h + 38)
    return svg(w, h, body, label or (title or ""))


def compare(cols, title=None, w=760, size=13, label=""):
    """Карточки-столбцы для сравнения: cols = [(заголовок, цвет, [строки])]."""
    n = len(cols)
    gap = 16
    cw = (w - 40 - gap * (n - 1)) / n
    rows = max(len(c[2]) for c in cols)
    top = 40 if title else 14
    line_h = size * 1.55
    ch = 44 + rows * line_h * 1.6 + 14
    h = top + ch + 14
    body = text(w / 2, 24, title, 15, 700) if title else ""
    for i, (head, color, lines) in enumerate(cols):
        x = 20 + i * (cw + gap)
        fill, stroke = PAL[color]
        body += f'<rect x="{x}" y="{top}" width="{cw}" height="{ch}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        body += text(x + cw / 2, top + 26, head, size + 1, 700, fill=stroke)
        for j, ln in enumerate(lines):
            ln, ls = fit(ln, cw - 24, size, 400, min_size=9.5, wrap=False)
            body += text(x + 14, top + 52 + j * line_h * 1.6, ln, ls, 400, anchor="start")
    return svg(w, h, body, label or (title or ""))


def rings(labels, title=None, w=760, label="", note=None):
    """Концентрические кольца (срез осевого органа): labels снаружи внутрь [(название, цвет)]."""
    cx, cy = 210, 200
    n = len(labels)
    rmax = 165
    step = rmax / n
    h = 400
    body = text(w / 2, 24, title, 15, 700) if title else ""
    for i, (name, color) in enumerate(labels):
        r = rmax - i * step
        fill, stroke = PAL[color]
        body += f'<circle cx="{cx}" cy="{cy + 10}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    for i, (name, color) in enumerate(labels):
        r = rmax - i * step - step / 2
        ly = 70 + i * (300 / max(n - 1, 1)) if n > 1 else cy
        px, py = cx + r * 0.72, cy + 10 - r * 0.69
        fill, stroke = PAL[color]
        body += f'<line x1="{px:.1f}" y1="{py:.1f}" x2="440" y2="{ly:.1f}" stroke="{MUTED}" stroke-width="1"/>'
        body += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{stroke}"/>'
        body += text(448, ly + 5, name, 14, 600, anchor="start", fill=stroke)
    if note:
        body += text(448, h - 18, note, 12, 400, anchor="start", fill=MUTED, italic=True)
    return svg(w, h, body, label or (title or ""))
