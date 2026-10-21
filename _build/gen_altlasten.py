#!/usr/bin/env python3
"""Sammelt die Adressen ein, die nur die alte WordPress-Installation kennt.

In den eigenen Texten stehen Verweise, die keiner Seite dieses Repos
entsprechen und die trotzdem funktionieren, weil WordPress sie aufloest:

  /online-collaboration                      -> /online-file-editing/
  /zentrale-benutzerverwaltung-ad-ldap-...   -> /ad-ldap/
  /wiki                                      -> /wikis/

Die ersten beiden sind frueher vergebene Slugs, die WordPress unter
_wp_old_slug in postmeta mitfuehrt - die REST-API nennt sie nicht, und
aus dem Dateibestand sind sie nicht zu gewinnen. Der dritte ist
redirect_guess_404_permalink, das aus Wortteilen raet.

Nachbauen laesst sich das nicht. Darum einmal fragen: jede Adresse aus
den eigenen Texten, die ins Leere zeigt, wird der laufenden Seite
vorgelegt und ihre Antwort nach wp/altlasten.json geschrieben. Danach
braucht es die alte Seite nicht mehr; die Datei gehoert ins Repo.

Voraussetzung: die Seite muss gebaut sein (hugo), damit feststeht,
welche Adressen es gibt.

    hugo --gc && python3 -E -s _build/gen_altlasten.py
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import unquote

import wpdata as w

PUBLIC = w.REPO / 'public'


class OhneFolgen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def gebaut():
    if not PUBLIC.exists():
        raise SystemExit('public/ fehlt - erst "hugo --gc" laufen lassen')
    aus = set()
    for p in PUBLIC.rglob('*'):
        if p.is_file():
            rel = '/' + str(p.relative_to(PUBLIC))
            aus.add(rel)
            if rel.endswith('/index.html'):
                aus.add(rel[:-len('index.html')])
    return aus


def verweise():
    """Alle internen Verweise aus den gebauten Seiten."""
    aus = {}
    for p in PUBLIC.rglob('*.html'):
        s = re.sub(r'<!--.*?-->', '', p.read_text(encoding='utf-8', errors='replace'), flags=re.S)
        for m in re.finditer(r'(?:src|href)="(/[^"]*)"', html.unescape(s)):
            u = unquote(m.group(1).split('#')[0].split('?')[0])
            aus.setdefault(u, str(p.relative_to(PUBLIC)))
    return aus


def main():
    da = gebaut()
    bekannt = w.alle_weiterleitungen()
    offen = {}
    for u, quelle in verweise().items():
        if u in da or u + 'index.html' in da or u + '/index.html' in da:
            continue
        if u in bekannt or u.startswith('/pagefind/') or u.startswith('/api/'):
            continue
        offen[u] = quelle

    op = urllib.request.build_opener(OhneFolgen())
    ergebnis = {}
    for u, quelle in sorted(offen.items()):
        try:
            with op.open(urllib.request.Request(
                    w.BASE + u, headers={'User-Agent': 'de-seafile-altlasten/1'}),
                    timeout=30) as r:
                code, ort = r.status, r.headers.get('Location')
        except urllib.error.HTTPError as e:
            code, ort = e.code, e.headers.get('Location')
        except Exception as e:
            print(f'  FEHLER {u}: {e}')
            continue
        ziel = (ort or '').replace(w.BASE, '') if code in (301, 302) else None
        ergebnis[u] = ziel
        zustand = f'301 -> {ziel}' if ziel else f'{code}, kein Ziel'
        print(f'  {u:62s} {zustand}   (aus {quelle})')
        time.sleep(0.1)

    (w.WP / 'altlasten.json').write_text(
        json.dumps(ergebnis, indent=1, ensure_ascii=False, sort_keys=True) + '\n',
        encoding='utf-8')
    mit = sum(1 for v in ergebnis.values() if v)
    print(f'\n{len(ergebnis)} Adressen geprueft, {mit} mit Ziel -> wp/altlasten.json')
    print('Die ohne Ziel sind auch in der alten Seite tot und gehoeren im Text repariert.')


if __name__ == '__main__':
    sys.exit(main())
