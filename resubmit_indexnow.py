#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IndexNow rotatif hebdomadaire — soumet 200 URLs differentes chaque semaine.
Lance par la tache planifiee Windows "Affilimax IndexNow".
SOURCES : blog github.io (sitemap_fr.xml) + site Render (sitemap.xml).
Rotation : semaine ISO % 8 -> tranche de 200 URLs. Jamais les memes 2 semaines de suite.
"""
import json, re, time, urllib.request, datetime

KEY_FILE = "affilimax2026indexnowkey001.txt"
SOURCES = [
    ("https://haksguet23-debug.github.io/affilmax-blog/", "sitemap_fr.xml",
     "https://haksguet23-debug.github.io/affilmax-blog/sitemap_fr.xml"),
    ("https://afflimax.onrender.com/", "sitemap.xml",
     "https://afflimax.onrender.com/sitemap.xml"),
]
BATCH = 200

def get(url):
    return urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")

def urls_for(base, local_map, remote_map):
    try:
        sm = open(local_map, encoding="utf-8", errors="replace").read()
    except OSError:
        sm = get(remote_map)
    out = [u if u.startswith("http") else base + u.lstrip("/")
           for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", sm)]
    if base not in out:
        out.insert(0, base)
    return out

week = datetime.date.today().isocalendar()[1]
key = open(KEY_FILE, encoding="utf-8").read().strip()
submitted = 0
for base, local_map, remote_map in SOURCES:
    urls = urls_for(base, local_map, remote_map)
    host = urllib.parse.urlparse(base).netloc
    start = (week % max(1, (len(urls) + BATCH - 1) // BATCH)) * BATCH
    chunk = urls[start:start + BATCH] or urls[:BATCH]
    body = json.dumps({"host": host, "key": key,
                       "keyLocation": base + KEY_FILE, "urlList": chunk}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    for attempt in (1, 2, 3):
        try:
            r = urllib.request.urlopen(req, timeout=30)
            submitted += len(chunk)
            print(f"[OK] {host} : {len(chunk)} URLs (tranche {start}) -> HTTP {r.status}")
            break
        except Exception as e:
            print(f"[ECHEC {attempt}/3] {host} : {e}")
            time.sleep(20 * attempt)
print(f"TOTAL semaine {week} : {submitted} URLs soumises")
