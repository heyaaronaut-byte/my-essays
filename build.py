"""
build.py — turns Markdown essays into a Paul-Graham-style static site.

Usage:
    python build.py

Each file in essays/*.md should start with two metadata lines:
    title: My Essay Title
    date: July 2026

...followed by a blank line, then the essay body in plain paragraphs
(one blank line between paragraphs). No need for fancy Markdown syntax
unless you want to add it later.
"""

import os
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
ESSAYS_DIR = ROOT / "essays"
OUTPUT_DIR = ROOT / "docs"  # GitHub Pages can serve straight from /docs
ESSAYS_OUTPUT = OUTPUT_DIR / "essays"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<link rel="stylesheet" href="{css_path}style.css">
</head>
<body>
<div class="nav"><a href="{home_path}index.html">index</a></div>
<h1>{title}</h1>
<div class="date">{date}</div>
{body}
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Essays</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>Essays</h1>
<div class="byline">by you</div>
<p class="intro">A place to write down what I'm learning as I go — mostly about building things, personal finance, and figuring stuff out along the way.</p>
<ul class="essay-list">
{items}
</ul>
</body>
</html>
"""


def parse_essay(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = "Untitled"
    date = ""
    body_start = 0

    for i, line in enumerate(lines):
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("date:"):
            date = line.split(":", 1)[1].strip()
        elif line.strip() == "" and title != "Untitled":
            body_start = i + 1
            break

    body_lines = lines[body_start:]
    paragraphs = "\n".join(body_lines).split("\n\n")
    html_body = "\n".join(
        f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()
    )

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return {"title": title, "date": date, "body": html_body, "slug": slug}


def build():
    OUTPUT_DIR.mkdir(exist_ok=True)
    ESSAYS_OUTPUT.mkdir(parents=True, exist_ok=True)

    # copy stylesheet
    (OUTPUT_DIR / "style.css").write_text(
        (ROOT / "style.css").read_text(encoding="utf-8"), encoding="utf-8"
    )

    essays = []
    for md_file in sorted(ESSAYS_DIR.glob("*.md")):
        essay = parse_essay(md_file)
        essays.append(essay)

        page_html = PAGE_TEMPLATE.format(
            title=essay["title"],
            date=essay["date"],
            body=essay["body"],
            css_path="../",
            home_path="../",
        )
        (ESSAYS_OUTPUT / f"{essay['slug']}.html").write_text(
            page_html, encoding="utf-8"
        )
        print(f"built essays/{essay['slug']}.html")

    items = "\n".join(
        f'<li><a href="essays/{e["slug"]}.html">{e["title"]}</a>'
        f'<span class="essay-date">{e["date"]}</span></li>'
        for e in reversed(essays)
    )
    (OUTPUT_DIR / "index.html").write_text(
        INDEX_TEMPLATE.format(items=items), encoding="utf-8"
    )
    print("built index.html")
    print(f"\nDone. Site is in {OUTPUT_DIR}/ — open index.html to preview.")


if __name__ == "__main__":
    build()
