#!/usr/bin/env python3
"""Build the ERGent User Manual.

Joins the chapters 00-*.md to 05-*.md in this folder into ONE styled HTML file
(ERGent-Manual.html) with a cover page and a table of contents, then makes
ERGent-Manual.pdf with headless Google Chrome.

Run it from anywhere:

    .venv/bin/python docs/manual/build_manual.py

It uses the `markdown` package if it is installed (pip install markdown). If not, it
falls back to a small built-in converter that handles headings, lists, tables, code,
quotes, bold, italic, links and inline code. Nothing else is needed.
"""

from __future__ import annotations

import datetime
import html
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / "ERGent-Manual.html"
PDF_FILE = HERE / "ERGent-Manual.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TITLE = "ERGent User Manual"
SUBTITLE = "Team ERG · Version 2+"
TAGLINE = "A control-chart dashboard for 911 EMS dispatch in Ithaca, NY"


# ---- a tiny markdown converter (used only if the `markdown` package is missing) -----------

def _inline(text: str) -> str:
    """Bold, italic, inline code and links inside one line of text."""
    codes = []

    def stash(m):
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def mini_markdown(src: str) -> str:
    lines = src.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):                                   # fenced code
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(block)) + "</code></pre>")
        elif re.match(r"#{1,6} ", line):                                # heading
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n}>{_inline(line[n:].strip())}</h{n}>")
            i += 1
        elif re.match(r"-{3,}\s*$", line):
            out.append("<hr>")
            i += 1
        elif line.lstrip().startswith(">"):                             # quote
            block = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                block.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append("<blockquote>" + mini_markdown("\n".join(block)) + "</blockquote>")
        elif line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"\s*\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1]):
            head = _cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            t = ["<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>")
            out.append("".join(t) + "</tbody></table>")
        elif re.match(r"\s*([-*]|\d+\.)\s+", line):                     # list (one nesting level)
            ordered = bool(re.match(r"\s*\d+\.", line))
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while i < len(lines) and (re.match(r"\s*([-*]|\d+\.)\s+", lines[i]) or
                                      (lines[i].startswith("  ") and lines[i].strip() and items)):
                m = re.match(r"(\s*)([-*]|\d+\.)\s+(.*)", lines[i])
                if m and len(m.group(1)) >= 2 and items:                # nested item
                    items[-1] += "\x01" + m.group(3)
                elif m:
                    items.append(m.group(3))
                else:                                                   # continuation line
                    items[-1] += " " + lines[i].strip()
                i += 1
            li = []
            for it in items:
                head, *sub = it.split("\x01")
                inner = _inline(head)
                if sub:
                    inner += "<ul>" + "".join(f"<li>{_inline(s)}</li>" for s in sub) + "</ul>"
                li.append(f"<li>{inner}</li>")
            out.append(f"<{tag}>" + "".join(li) + f"</{tag}>")
        else:                                                           # paragraph
            block = []
            while i < len(lines) and lines[i].strip() and not re.match(r"(#{1,6} |```|\s*>|\s*\||\s*([-*]|\d+\.)\s+)", lines[i]):
                block.append(lines[i].strip())
                i += 1
            if not block:                                               # safety: never loop forever
                block = [lines[i].strip()]
                i += 1
            out.append("<p>" + _inline(" ".join(block)) + "</p>")
    return "\n".join(out)


def to_html(src: str) -> str:
    try:
        import markdown
    except ImportError:
        return mini_markdown(src)
    return markdown.markdown(src, extensions=["tables", "fenced_code", "sane_lists"])


# ---- the manual ----------------------------------------------------------------------------------

def slug(text: str, used: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-") or "section"
    name, n = base, 2
    while name in used:
        name, n = f"{base}-{n}", n + 1
    used.add(name)
    return name


def build_html() -> str:
    files = sorted(p for p in HERE.glob("[0-9][0-9]-*.md"))
    if not files:
        sys.exit("No chapter files (00-*.md ...) found in " + str(HERE))
    used: set[str] = set()
    toc: list[tuple[str, str, list[tuple[str, str]]]] = []      # (id, title, [(id, h2 title)])
    chapters: list[str] = []
    for path in files:
        number = int(path.name[:2])
        body = to_html(path.read_text(encoding="utf-8"))
        subs: list[tuple[str, str]] = []
        state = {"title": "", "id": ""}

        def h1(m):
            title = re.sub(r"<[^>]+>", "", m.group(1))
            state["title"], state["id"] = title, slug(f"chapter-{number}-{title}", used)
            label = f'<span class="chnum">Chapter {number}</span>' if number else '<span class="chnum">Welcome</span>'
            return f'<h1 id="{state["id"]}">{label}{m.group(1)}</h1>'

        def h2(m):
            hid = slug(m.group(1), used)
            subs.append((hid, re.sub(r"<[^>]+>", "", m.group(1))))
            return f'<h2 id="{hid}">{m.group(1)}</h2>'

        body = re.sub(r"<h1[^>]*>(.*?)</h1>", h1, body, count=1, flags=re.S)
        body = re.sub(r"<h2[^>]*>(.*?)</h2>", h2, body, flags=re.S)
        toc.append((state["id"], (f"{number}. " if number else "") + state["title"], subs))
        chapters.append(f'<section class="chapter">\n{body}\n</section>')

    toc_html = ["<nav class=\"toc\"><h1 class=\"toc-title\">Contents</h1><ul class=\"toc-list\">"]
    for cid, title, subs in toc:
        toc_html.append(f'<li class="toc-ch"><a href="#{cid}">{html.escape(title)}</a>')
        if subs:
            toc_html.append("<ul>" + "".join(f'<li><a href="#{h}">{html.escape(t)}</a></li>' for h, t in subs) + "</ul>")
        toc_html.append("</li>")
    toc_html.append("</ul></nav>")

    built = datetime.date.today().strftime("%B %d, %Y")
    cover = f"""<section class="cover">
  <div class="cover-mark">ERGent</div>
  <h1 class="cover-title">{TITLE}</h1>
  <p class="cover-sub">{SUBTITLE}</p>
  <p class="cover-tag">{TAGLINE}</p>
  <p class="cover-date">Cornell Six Sigma Hackathon &middot; Built {built}</p>
</section>"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE} · {SUBTITLE}</title>
<style>{CSS}</style></head>
<body>
{cover}
{"".join(toc_html)}
{chr(10).join(chapters)}
</body></html>
"""


CSS = """
@page { size: Letter; margin: 18mm 16mm 20mm 16mm;
  @bottom-center { content: counter(page); font: 9pt -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #6b7280; } }
@page :first { @bottom-center { content: ""; } }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5pt/1.55 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; color: #1f2933;
  max-width: 190mm; margin: 0 auto; padding: 0 4mm; }
h1, h2, h3, h4 { color: #0f2540; line-height: 1.25; }
h1 { font-size: 24pt; margin: 0 0 6mm; padding-bottom: 3mm; border-bottom: 2px solid #e8604c; }
h1 .chnum { display: block; font-size: 10pt; letter-spacing: .12em; text-transform: uppercase;
  color: #e8604c; margin-bottom: 2mm; }
h2 { font-size: 15pt; margin: 8mm 0 3mm; break-after: avoid; }
h3 { font-size: 12pt; margin: 6mm 0 2mm; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 4mm 0 1mm; break-after: avoid; }
p, ul, ol, table, pre, blockquote { margin: 0 0 3.5mm; }
ul, ol { padding-left: 6mm; }
li { margin-bottom: 1mm; }
a { color: #1d4ed8; text-decoration: none; }
code { font: 9pt "SF Mono", Menlo, Consolas, monospace; background: #f1f3f5; padding: 0 1.2mm; border-radius: 1mm; }
pre { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 2mm; padding: 3mm; overflow-x: auto;
  white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; line-height: 1.45; }
blockquote { border-left: 3px solid #e8604c; background: #fff6f4; padding: 2.5mm 4mm; color: #3a4552;
  break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.3pt; }
th, td { border: 1px solid #d5dbe1; padding: 1.6mm 2.4mm; text-align: left; vertical-align: top; }
th { background: #eef2f7; color: #0f2540; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
hr { border: 0; border-top: 1px solid #d5dbe1; margin: 6mm 0; }
.chapter { break-before: page; }
.cover { min-height: 235mm; display: flex; flex-direction: column; justify-content: center; align-items: flex-start;
  padding: 0 8mm; border-left: 6px solid #e8604c; }
.cover-mark { font-size: 16pt; letter-spacing: .25em; color: #e8604c; font-weight: 700; }
.cover-title { font-size: 40pt; border: 0; margin: 6mm 0 2mm; padding: 0; }
.cover-sub { font-size: 16pt; color: #3a4552; margin: 0 0 8mm; }
.cover-tag { font-size: 12pt; color: #52606d; max-width: 120mm; }
.cover-date { margin-top: 30mm; font-size: 10pt; color: #6b7280; }
.toc { break-before: page; }
.toc-title { border-bottom: 2px solid #e8604c; }
.toc-list, .toc-list ul { list-style: none; padding-left: 0; }
.toc-ch { margin: 4mm 0 1mm; font-weight: 700; font-size: 11.5pt; }
.toc-ch ul { margin: 1mm 0 0 5mm; font-weight: 400; font-size: 9.8pt; }
.toc-ch ul li { margin: 0; break-inside: avoid; }
@media screen { body { padding: 10mm 6mm; } .chapter, .toc { border-top: 1px dashed #cbd2d9; padding-top: 8mm; margin-top: 8mm; } }
"""


# ---- output --------------------------------------------------------------------------------------

def count_pages(pdf: Path) -> int:
    data = pdf.read_bytes()
    n = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    if n:
        return n
    try:                                                    # Spotlight (macOS) knows the page count
        out = subprocess.run(["mdls", "-name", "kMDItemNumberOfPages", "-raw", str(pdf)],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return int(out) if out.isdigit() else 0
    except Exception:
        return 0


def main() -> int:
    HTML_FILE.write_text(build_html(), encoding="utf-8")
    print(f"wrote {HTML_FILE} ({HTML_FILE.stat().st_size // 1024} KB)")
    if not Path(CHROME).exists():
        print("Google Chrome was not found, so the PDF was not made. Open the HTML file and use "
              "Print > Save as PDF.")
        return 0
    if PDF_FILE.exists():
        PDF_FILE.unlink()
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           f"--print-to-pdf={PDF_FILE}", f"file://{HTML_FILE}"]
    subprocess.run(cmd, capture_output=True, timeout=180)
    if not PDF_FILE.exists():
        print("Chrome did not make a PDF. Open the HTML file and use Print > Save as PDF.")
        return 1
    print(f"wrote {PDF_FILE} ({PDF_FILE.stat().st_size // 1024} KB, about {count_pages(PDF_FILE)} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
