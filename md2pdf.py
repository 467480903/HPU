#!/usr/bin/env python3
"""Minimal Markdown -> HTML converter + PDF (via headless Chrome) for this project doc."""
import re
import html as html_lib
import subprocess
import sys
import os
import tempfile
import shutil
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', r'<img src="\2" alt="\1">', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_sep(line):
    s = line.strip()
    if not s.startswith("|"):
        return False
    cells = [c.strip() for c in s.strip("|").split("|")]
    return all(re.fullmatch(r':?-+:?', c) for c in cells if c != "")


def render_gantt(source):
    """Render this document's Mermaid gantt block as a printable inline SVG."""
    title = "项目计划"
    sections = []
    section = None
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("title "):
            title = stripped[6:]
        elif stripped.startswith("section "):
            section = [stripped[8:], []]
            sections.append(section)
        else:
            match = re.match(r"(.+?)\s*:\s*\w+\s*,\s*(\d{4}-\d{2}-\d{2})\s*,\s*(\d+)M", stripped)
            if match and section:
                name, start, months = match.groups()
                section[1].append((name.strip(), date.fromisoformat(start), int(months)))

    tasks = [(group, *task) for group, entries in sections for task in entries]
    if not tasks:
        return "<pre>甘特图数据无法解析</pre>"

    width, label_width, month_width = 1100, 300, 60
    top, row_h, group_h = 58, 30, 25
    chart_start = date(2026, 11, 1)
    months = 13
    height = top + sum(group_h + len(entries) * row_h for _, entries in sections) + 16
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">',
             '<style>text{font-family:"Noto Sans CJK SC","Noto Sans",sans-serif;fill:#263238}.title{font-size:20px;font-weight:bold}.month{font-size:12px}.group{font-size:13px;font-weight:bold}.task{font-size:11px}.bar{fill:#c62828}.grid{stroke:#d8d8d8;stroke-width:1}</style>',
             f'<text x="8" y="27" class="title">{title}</text>']
    for m in range(months):
        x = label_width + m * month_width
        month_num = (chart_start.month - 1 + m) % 12 + 1
        year = chart_start.year + (chart_start.month - 1 + m) // 12
        parts.append(f'<text x="{x + 4}" y="49" class="month">{year}/{month_num:02}</text>')
        parts.append(f'<line x1="{x}" y1="55" x2="{x}" y2="{height - 8}" class="grid"/>')
    y = top
    month_index = lambda d: (d.year - chart_start.year) * 12 + d.month - chart_start.month
    for group, entries in sections:
        parts.append(f'<text x="8" y="{y + 17}" class="group">{group}</text>')
        y += group_h
        for name, start, duration in entries:
            parts.append(f'<text x="8" y="{y + 18}" class="task">{name}</text>')
            x = label_width + month_index(start) * month_width + 3
            bar_w = max(8, duration * month_width - 6)
            parts.append(f'<rect x="{x}" y="{y + 5}" width="{bar_w}" height="19" rx="4" class="bar"/>')
            y += row_h
    parts.append('</svg>')
    return '<div class="gantt">' + ''.join(parts) + '</div>'


def convert(md):
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "":
            i += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            i += 1
            code_lines = []
            while i < n and lines[i].strip() != "```":
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            code = "\n".join(code_lines)
            if language == "mermaid" and code_lines and code_lines[0].strip() == "gantt":
                out.append(render_gantt(code))
            else:
                out.append(f"<pre><code>{html_lib.escape(code)}</code></pre>")
            continue

        # Table
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            header = split_row(rows[0])
            ncols = len(header)
            h = ["<table><thead><tr>"]
            h += [f"<th>{inline(c)}</th>" for c in header]
            h.append("</tr></thead><tbody>")
            for r in rows[1:]:
                if is_sep(r):
                    continue
                cells = split_row(r)
                cells = (cells + [""] * ncols)[:ncols]
                h.append("<tr>")
                h += [f"<td>{inline(c)}</td>" for c in cells]
                h.append("</tr>")
            h.append("</tbody></table>")
            out.append("".join(h))
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Ordered list
        m = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if m:
            items = []
            while i < n:
                mm = re.match(r"^(\d+)\.\s+(.*)", lines[i].strip())
                if not mm:
                    break
                item_html = inline(mm.group(2))
                i += 1
                # Absorb any immediately following images (across blank lines) into this item
                imgs = []
                j = i
                while j < n:
                    ls = lines[j].strip()
                    if ls == "":
                        j += 1
                        continue
                    if re.match(r"^!\[", ls):
                        imgs.append(inline(ls))
                        j += 1
                        continue
                    break
                if imgs:
                    item_html += "".join(f'<p class="img">{im}</p>' for im in imgs)
                    i = j
                items.append(item_html)
                # Continue only if the next non-blank line is another numbered item
                j = i
                while j < n and lines[j].strip() == "":
                    j += 1
                if j < n and re.match(r"^(\d+)\.\s+", lines[j].strip()):
                    i = j
                else:
                    break
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # Image-only line
        if re.match(r"^!\[", stripped):
            out.append(f'<p class="img">{inline(stripped)}</p>')
            i += 1
            continue

        # Paragraph
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    return "\n".join(out)


CSS = """
@page { size: A4; margin: 20mm; }
body { font-family: 'Noto Sans CJK SC', 'Noto Sans', Arial, sans-serif;
       color: #1a1a1a; line-height: 1.55; font-size: 11pt; }
h1 { font-size: 20pt; border-bottom: 2px solid #c00; padding-bottom: 6px; margin-top: 1.2em; }
h2 { font-size: 15pt; color: #b00; margin-top: 1.2em; border-bottom: 1px solid #ddd; padding-bottom: 3px; }
p { margin: 0.6em 0; }
img { max-width: 100%; height: auto; display: block; margin: 0.5em auto; }
p.img { text-align: center; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9.5pt; }
th, td { border: 1px solid #999; padding: 5px 8px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; }
ol { margin: 0.5em 0 0.5em 1.4em; padding: 0; }
li { margin: 0.4em 0; }
code { background: #f4f4f4; padding: 1px 4px; border-radius: 3px; }
pre { margin: 0.8em 0; padding: 10px 12px; border: 1px solid #ddd;
      border-radius: 4px; background: #f6f7f8; white-space: pre-wrap;
      overflow-wrap: anywhere; line-height: 1.45; font-size: 9pt; }
pre code { display: block; padding: 0; background: none; border-radius: 0;
           font-family: 'Noto Sans Mono CJK SC', 'DejaVu Sans Mono', monospace; }
.gantt { width: 100%; margin: 1em 0; page-break-inside: avoid; }
.gantt svg { display: block; width: 100%; height: auto; }
"""


def main():
    src = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(BASE_DIR, "project_description_en.md")
    stem, _ = os.path.splitext(src)
    html_out = stem + ".html"
    pdf_out = stem + ".pdf"
    with open(src, encoding="utf-8") as f:
        md = f.read()
    body = convert(md)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<style>{CSS}</style></head>
<body>
{body}
</body></html>"""
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html)

    chrome_profile = tempfile.mkdtemp(prefix="md2pdf-chrome-")
    cmd = [
        "google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={chrome_profile}",
        "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=20000",
        f"--print-to-pdf={pdf_out}",
        f"file://{html_out}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    shutil.rmtree(chrome_profile, ignore_errors=True)
    if r.returncode != 0:
        print("Chrome stderr:", r.stderr, file=sys.stderr)
        sys.exit(r.returncode)
    if os.path.exists(pdf_out):
        print("OK:", pdf_out, os.path.getsize(pdf_out), "bytes")
    else:
        print("PDF not created", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
