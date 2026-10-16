#!/usr/bin/env python3
"""Собирает тренажёр в один HTML-файл: стили, скрипты, задания и картинки внутри.

Такой файл открывается двойным щелчком без интернета (шрифты подтянутся,
если интернет есть) и его удобно переслать ученице одним вложением.

Запуск:  python3 tools/bundle.py            → dist/olimpiada-pod-mikroskopom.html
         python3 tools/bundle.py --fragment  → тот же файл без <html>/<head>/<body>
                                               (для публикации как Artifact)
"""
import base64
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "olimpiada-pod-mikroskopom.html"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def inline_images(text):
    def repl(m):
        path = ROOT / m.group(0)
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        mime = "image/png" if path.suffix == ".png" else "image/jpeg"
        return f"data:{mime};base64," + b64
    return re.sub(r"assets/img/[\w.-]+\.(?:png|jpe?g)", repl, text)


def script(js):
    if re.search(r"</script", js, re.I):
        js = re.sub(r"</(script)", r"<\\/\1", js, flags=re.I)
    return "<script>\n" + js + "\n</script>"


def build(fragment=False, out=OUT):
    page = read("index.html")
    page = page.replace('<link rel="stylesheet" href="assets/css/app.css">',
                        "<style>\n" + read("assets/css/app.css") + "\n</style>")
    page = page.replace('<script src="assets/js/data.js"></script>', script(inline_images(read("assets/js/data.js"))))
    page = page.replace('<script src="assets/js/app.js"></script>', script(read("assets/js/app.js")))
    if "assets/" in re.sub(r"<script>.*?</script>|<style>.*?</style>", "", page, flags=re.S):
        sys.exit("ОШИБКА: в странице остались ссылки на assets/")
    if fragment:
        head = re.search(r"<head>(.*?)</head>", page, re.S).group(1)
        body = re.search(r"<body>(.*?)</body>", page, re.S).group(1)
        # обёртку <html>/<head>/<body> добавит площадка публикации
        head = re.sub(r'\s*<meta charset="utf-8">', "", head)
        head = re.sub(r'\s*<meta name="viewport"[^>]*>', "", head)
        page = head.strip() + "\n" + body.strip() + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Готово: {out} — {out.stat().st_size // 1024} КБ")


if __name__ == "__main__":
    if "--fragment" in sys.argv:
        i = sys.argv.index("--fragment")
        target = Path(sys.argv[i + 1]) if len(sys.argv) > i + 1 else ROOT / "dist" / "artifact.html"
        build(fragment=True, out=target)
    else:
        build()
