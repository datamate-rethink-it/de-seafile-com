#!/usr/bin/env python3
"""Referenz-Schnappschuss der laufenden WordPress-Seite de.seafile.com."""
import json, os, pathlib, sys, time, urllib.request, urllib.error

BASE = 'https://de.seafile.com'
B = pathlib.Path('/home/christoph/Dokumente/de-seafile-hugo/_build')
OUT = B / 'reference'
routes = [l.strip() for l in (B / 'wp' / 'all-routes.txt').read_text().splitlines() if l.strip()]

OUT.mkdir(parents=True, exist_ok=True)
index = {}
for i, r in enumerate(routes, 1):
    req = urllib.request.Request(BASE + r, headers={'User-Agent': 'de-seafile-snapshot/1'})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body, code, loc = resp.read(), resp.status, resp.headers.get('Location')
            ctype = resp.headers.get('Content-Type', '')
    except urllib.error.HTTPError as e:
        body, code, loc, ctype = e.read(), e.code, e.headers.get('Location'), e.headers.get('Content-Type', '')
    except Exception as e:
        print(f'{i:4d} ERR  {r}: {e}', flush=True)
        index[r] = {'error': str(e)}
        continue
    name = (r.strip('/') or 'index').replace('/', '_') or 'index'
    if not name.endswith(('.xml', '.txt', '.ico', '.jpg')):
        name += '.html'
    (OUT / name).write_bytes(body)
    index[r] = {'status': code, 'bytes': len(body), 'file': name,
                'content_type': ctype, 'location': loc}
    print(f'{i:4d} {code} {len(body):8d} {r}', flush=True)
    time.sleep(0.15)

(B / 'reference-index.json').write_text(json.dumps(index, indent=1, ensure_ascii=False))
print('fertig:', len(index))
