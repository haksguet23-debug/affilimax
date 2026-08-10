#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md_to_pdf.py — Convertit un rapport Markdown en PDF imprimable.

Méthode :
  1. Lit le .md
  2. Convertit (léger) en HTML stylé pour impression (A4)
  3. Rend le PDF via Chrome headless (--print-to-pdf)

Usage :
  python md_to_pdf.py [fichier.md] [fichier.pdf]
  (défauts : RAPPORT_REEL_2026-08-10.md -> RAPPORT_REEL_2026-08-10.pdf)

Dépendances : uniquement Python stdlib + Chrome installé.
"""

import html
import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    return None


# ==================== INLINE FORMATTING ====================

def inline(text):
    """Transforme **gras**, *italique* et `code` en HTML (échappé avant).

    Les spans `code` sont remplacés par des placeholders avant le gras/italique
    pour que les regex ne puissent pas matcher à travers une balise <code>.
    """
    text = html.escape(text)
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00C%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    # **gras** (ne traverse pas les placeholders)
    text = re.sub(r"\*\*([^*\x00]+)\*\*", r"<strong>\1</strong>", text)
    # *italique*
    text = re.sub(r"\*([^*\x00]+)\*", r"<em>\1</em>", text)
    # Restauration des spans code
    for idx, c in enumerate(codes):
        text = text.replace("\x00C%d\x00" % idx, "<code>%s</code>" % c)
    return text


# ==================== BLOCKS ====================

def parse_table(lines, i):
    """Parse un tableau markdown à partir de la ligne i. Renvoie (html, next_i)."""
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1
    if not rows:
        return "", i
    # Ligne séparateur (|---|) — garde-fou : ne doit pas être identique à l'en-tête
    if (
        len(rows) >= 2
        and rows[1] != rows[0]
        and all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1])
    ):
        header, rows = rows[0], rows[2:]
    else:
        header, rows = rows[0], rows[1:]
    html_rows = []
    for row in rows:
        cells = "".join(f"<td>{inline(c)}</td>" for c in row)
        html_rows.append(f"<tr>{cells}</tr>")
    head = "".join(f"<th>{inline(c)}</th>" for c in header)
    return (
        f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(html_rows)}</tbody></table></div>",
        i,
    )


def convert_markdown(md_text):
    """Convertit le markdown du rapport en HTML (blocs simples)."""
    lines = md_text.splitlines()
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- Ligne vide : sauter
        if not stripped:
            i += 1
            continue

        # --- Règle horizontale ---
        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # --- Titres ---
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # --- Tableau ---
        if stripped.startswith("|"):
            tbl, i = parse_table(lines, i)
            if tbl:
                out.append(tbl)
            continue

        # --- Blockquote (lignes > consécutives) ---
        if stripped.startswith(">"):
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{inline(' '.join(x.strip() for x in quote))}</blockquote>")
            continue

        # --- Bloc de code fencé ---
        if stripped.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # fermeture
            out.append(f"<pre>{html.escape(chr(10).join(code))}</pre>")
            continue

        # --- Liste à puces ---
        if re.match(r"^[-*+]\s+", stripped):
            items = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^[-*+]\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue

        # --- Liste numérotée ---
        if re.match(r"^\d+[.)]\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+[.)]\s+", "", lines[i].strip())))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # --- Paragraphe : groupe les lignes consécutives ---
        para = [stripped]
        i += 1
        while i < n and lines[i].strip() and not (
            lines[i].strip().startswith(("#", "|", ">", "-", "*", "+"))
            or re.match(r"^\d+[.)]\s+", lines[i].strip())
            or re.fullmatch(r"-{3,}|\*{3,}|_{3,}", lines[i].strip())
            or lines[i].strip().startswith("```")
        ):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    return "\n".join(out)


# ==================== PAGE HTML ====================

PAGE_CSS = """
:root{--gold:#b8860b;--blue:#1d4ed8;--green:#15803d;--red:#b91c1c;--muted:#6b7280;--dark:#0f172a}
*{box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;color:#1e293b;line-height:1.55;max-width:820px;margin:0 auto;padding:36px 44px;font-size:13px}
h1{font-size:24px;color:var(--dark);margin:0 0 4px;letter-spacing:-.5px}
h2{font-size:17px;color:var(--dark);border-bottom:2px solid var(--gold);padding-bottom:6px;margin:28px 0 12px;text-transform:uppercase;letter-spacing:.5px}
h3{font-size:14px;color:var(--blue);margin:18px 0 8px}
h4{font-size:13px;margin:14px 0 6px;color:var(--dark)}
p{margin:8px 0}
hr{border:none;border-top:1px solid #e2e8f0;margin:20px 0}
blockquote{background:#f8fafc;border-left:4px solid var(--gold);padding:10px 16px;margin:12px 0;border-radius:0 8px 8px 0;color:#334155;font-size:12.5px}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:12px}
th{background:var(--dark);color:#fff;text-align:left;padding:8px 10px;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.4px}
td{padding:7px 10px;border-bottom:1px solid #e2e8f0;vertical-align:top}
tr:nth-child(even) td{background:#f8fafc}
.table-wrap{overflow-x:auto}
code{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:4px;padding:1px 5px;font-family:'Cascadia Code','Consolas',monospace;font-size:11px;color:#0f172a}
pre{background:#0f172a;color:#e2e8f0;border-radius:8px;padding:14px 16px;overflow-x:auto;font-family:'Cascadia Code','Consolas',monospace;font-size:11.5px;line-height:1.5;margin:12px 0}
ul,ol{margin:8px 0;padding-left:22px}
li{margin:3px 0}
strong{color:var(--dark)}
em{color:#475569}
h2 code{text-transform:none}
@page{size:A4;margin:18mm 16mm}
@media print{body{padding:0;max-width:none}tr{page-break-inside:avoid}h2{page-break-after:avoid}pre{page-break-inside:avoid}}
"""


def build_html(title, body_html):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>{PAGE_CSS}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


def main():
    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_DIR / "RAPPORT_REEL_2026-08-10.md"
    md_path = md_path if md_path.is_absolute() else BASE_DIR / md_path
    if not md_path.exists():
        print(f"[ERREUR] Fichier introuvable : {md_path}")
        sys.exit(1)

    pdf_path = Path(sys.argv[2]) if len(sys.argv) > 2 else md_path.with_suffix(".pdf")
    html_path = md_path.with_suffix(".html")  # aperçu navigable

    md_text = md_path.read_text(encoding="utf-8")
    body = convert_markdown(md_text)
    title = md_path.stem.replace("_", " ")

    html_content = build_html(title, body)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"[OK] HTML écrit : {html_path}")

    chrome = find_chrome()
    if not chrome:
        print("[ERREUR] Chrome/Edge introuvable pour le rendu PDF.")
        print("        Le HTML imprimable est prêt : ouvrez-le puis 'Imprimer > PDF'.")
        sys.exit(1)

    # Chemin file:// (Windows)
    file_url = html_path.resolve().as_uri()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        f"--print-to-pdf={str(pdf_path.resolve())}",
        file_url,
    ]
    print(f"[OK] Rendu PDF via : {chrome}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print("[WARN] Chrome a retourné un code non nul — tentative avec --headless legacy")
        # Les vieilles versions de Chrome ne connaissent ni --headless=new ni
        # --no-pdf-header-footer (c'était --print-to-pdf-no-header).
        cmd2 = [
            c.replace("--headless=new", "--headless")
            .replace("--no-pdf-header-footer", "--print-to-pdf-no-header")
            for c in cmd
        ]
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)

    if pdf_path.exists() and pdf_path.stat().st_size > 500:
        size_kb = pdf_path.stat().st_size / 1024
        print(f"[OK] PDF généré : {pdf_path} ({size_kb:.1f} Ko)")
    else:
        print("[ERREUR] Le PDF n'a pas été généré.")
        if result.stderr:
            print("stderr:", result.stderr[:800])
        sys.exit(1)


if __name__ == "__main__":
    main()
