#!/usr/bin/env python3
"""Prueft die seiteninternen Verweise der gebauten Seite.

Gemeldet wird nur, was ins Leere zeigt. Verweise, fuer die es eine Regel
in deploy/redirects.caddy gibt, gelten als in Ordnung - sie funktionieren
nach dem Umzug genauso wie vorher, naemlich ueber eine 301. Sie werden
aber gezaehlt und aufgelistet, damit sichtbar bleibt, wie viele es sind.

Externe Adressen prueft dieses Skript nicht: das Ergebnis haengt davon
ab, wer gerade erreichbar ist, und ein Bau soll nicht daran scheitern,
dass ein fremder Server eine Minute lang hustet. Dafuer gibt es
_build/linkcheck_extern.py, das von Hand gestartet wird.

    hugo --gc && python3 -E -s _build/linkcheck.py
"""
import collections
import html
import re
import sys
from urllib.parse import unquote

import wpdata as w

PUBLIC = w.REPO / 'public'
BERICHT = w.B / 'linkcheck-report.txt'

# Vom Webserver bedient, nicht von einer Datei im Baum:
#   /api/trial         Weiterreichung an den Trial-Server
#   /pagefind/         erst nach dem Lauf von pagefind da
#   /feed, /category/<slug>/feed/   rewrite in der Caddy-Konfiguration
AUSNAHMEN = re.compile(r'^(/api/|/pagefind/|/feed/?$|/category/[^/]+/feed/?$)')


def main():
    vorhanden = {'/' + str(p.relative_to(PUBLIC)) for p in PUBLIC.rglob('*') if p.is_file()}
    umleitung = set(w.alle_weiterleitungen())
    entfallen = set(w.ENTFALLEN)

    tot = collections.Counter()
    ueber_umleitung = collections.Counter()
    auf_entfallene = collections.Counter()
    woher = {}

    for p in sorted(PUBLIC.rglob('*.html')):
        roh = p.read_text(encoding='utf-8', errors='replace')
        s = html.unescape(re.sub(r'<!--.*?-->', '', roh, flags=re.S))
        ziele = [m.group(1) for m in re.finditer(r'(?:src|href)="(/[^"]*)"', s)]
        for m in re.finditer(r'srcset="([^"]*)"', s):
            ziele += [t.strip().split(' ')[0] for t in m.group(1).split(',')
                      if t.strip().startswith('/')]
        for u in ziele:
            u = unquote(u.split('#')[0].split('?')[0])
            if AUSNAHMEN.match(u):
                continue
            if u in vorhanden or f'{u}index.html' in vorhanden or f'{u}/index.html' in vorhanden:
                continue
            woher.setdefault(u, str(p.relative_to(PUBLIC)))
            if u in entfallen:
                auf_entfallene[u] += 1
            elif u in umleitung:
                ueber_umleitung[u] += 1
            else:
                tot[u] += 1

    zeilen = []
    if auf_entfallene:
        zeilen.append('Verweise auf gestrichene Seiten (410) - gehoeren im Text repariert:')
        for u, n in auf_entfallene.most_common():
            zeilen.append(f'  {n:4d}x {u}   (z.B. {woher[u]})')
    if tot:
        zeilen.append('Tote Verweise:')
        for u, n in tot.most_common():
            zeilen.append(f'  {n:4d}x {u}   (z.B. {woher[u]})')
    if ueber_umleitung:
        zeilen.append('Ueber eine Weiterleitung erreichbar (wie bisher im WordPress):')
        for u, n in ueber_umleitung.most_common():
            zeilen.append(f'  {n:4d}x {u}   -> {w.alle_weiterleitungen()[u]}')

    BERICHT.write_text('\n'.join(zeilen) + '\n', encoding='utf-8')
    print(f'{len(tot)} tote Verweise, {len(auf_entfallene)} auf gestrichene Seiten, '
          f'{len(ueber_umleitung)} ueber eine Weiterleitung')
    if zeilen:
        print('\n'.join(zeilen))
    return 1 if (tot or auf_entfallene) else 0


if __name__ == '__main__':
    sys.exit(main())
