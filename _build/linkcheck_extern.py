#!/usr/bin/env python3
"""Prueft die Verweise auf fremde Server. Wird von Hand gestartet.

Nicht Teil des Baus: das Ergebnis haengt davon ab, wer gerade erreichbar
ist, und ein Release soll nicht daran scheitern, dass ein fremder Server
eine Minute lang hustet.

Lohnt sich trotzdem regelmaessig. Beim Umzug hat dieses Skript gefunden,
dass der Umzug von datamate.org drei Verweise von hier aus zerschossen
hat: zwei Bilder, die als Heissverweis dort lagen und beim Aussortieren
verwaister Dateien weggefallen sind (der Suchlauf dort sah nur Verweise
innerhalb von datamate.org), und die SeaMate-Kachel, deren Ziel jetzt mit
410 antwortet.

    hugo --gc && python3 -E -s _build/linkcheck_extern.py
"""
import collections
import html
import re
import sys
import time
import urllib.error
import urllib.request

import wpdata as w

PUBLIC = w.REPO / 'public'
KOPF = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) de-seafile-linkcheck/1'}


class OhneFolgen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def main():
    ziele = collections.defaultdict(set)
    for p in sorted(PUBLIC.rglob('*.html')):
        s = html.unescape(re.sub(r'<!--.*?-->', '', p.read_text(encoding='utf-8', errors='replace'),
                                 flags=re.S))
        for m in re.finditer(r'(?:href|src)="(https?://[^"]+)"', s):
            ziele[m.group(1).split('#')[0]].add(str(p.relative_to(PUBLIC)))

    op = urllib.request.build_opener(OhneFolgen())
    schlecht = []
    for u in sorted(ziele):
        for versuch in ('HEAD', 'GET'):
            try:
                with op.open(urllib.request.Request(u, method=versuch, headers=KOPF),
                             timeout=25) as r:
                    code, ort = r.status, r.headers.get('Location')
            except urllib.error.HTTPError as e:
                code, ort = e.code, e.headers.get('Location')
            except Exception as e:
                code, ort = None, str(e)[:70]
            # Manche Server mögen kein HEAD - dann einmal mit GET nachfassen.
            if code not in (403, 405, None) or versuch == 'GET':
                break
        if code in (200, 301, 302, 303, 307, 308):
            print(f'   {code} {u}')
        else:
            schlecht.append((u, code, ort, sorted(ziele[u])))
            print(f'!! {code} {u}')
            print(f'      {ort or ""}')
            print(f'      steht in: {", ".join(sorted(ziele[u]))[:140]}')
        time.sleep(0.1)

    print(f'\n{len(ziele)} fremde Adressen, {len(schlecht)} nicht erreichbar')
    return 1 if schlecht else 0


if __name__ == '__main__':
    sys.exit(main())
