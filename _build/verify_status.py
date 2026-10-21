#!/usr/bin/env python3
"""Vergleicht die Statuscodes des Containers mit denen der laufenden Seite.

Fuer jede Adresse aus wp/all-routes.txt: was antwortet die alte Seite,
was antwortet der Container, und stimmt das Ziel einer Weiterleitung
ueberein. Bei datamate.org hat genau diese Pruefung zehn Beitraege
gefunden, die ein zu weit gefasstes 410-Muster eingefangen hatte - der
Linkcheck konnte das nicht sehen.

Braucht einen laufenden Container und wird von Hand gestartet, nicht im
Bau:

    docker build -t de-seafile-com:dev .
    docker run -d --name de-seafile-test -p 127.0.0.1:8083:80 de-seafile-com:dev
    python3 -E -s _build/verify_status.py
    docker rm -f de-seafile-test

Mit einer Adresse als Argument wird nur diese geprueft.
"""
import json
import sys
import urllib.error
import urllib.request

import wpdata as w

CONTAINER = 'http://127.0.0.1:8083'

# Adressen, bei denen eine Abweichung gewollt ist.
GEWOLLT = {
    '/wp-login.php': 'WordPress ist abgeschaltet',
    '/wp-admin/': 'WordPress ist abgeschaltet',
    '/xmlrpc.php': 'WordPress ist abgeschaltet',
    '/wp-json/': 'WordPress ist abgeschaltet',
    '/wp-json/wp/v2/posts': 'WordPress ist abgeschaltet',
    '/comments/feed/': 'keine Kommentare mehr, kein Kommentar-Feed',
    '/favicon.ico': 'Verweise im Kopf statt einer Weiterleitung auf ein PNG',
}


class OhneFolgen(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def hole(op, basis, pfad):
    try:
        with op.open(urllib.request.Request(
                basis + pfad, headers={'User-Agent': 'de-seafile-statusvergleich/1'}),
                timeout=30) as r:
            return r.status, r.headers.get('Location')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Location')
    except Exception as e:
        return None, str(e)[:70]


def main():
    op = urllib.request.build_opener(OhneFolgen())
    live = json.loads((w.B / 'status-live.json').read_text(encoding='utf-8'))
    routen = ([sys.argv[1]] if len(sys.argv) > 1
              else [l.strip() for l in (w.WP / 'all-routes.txt').read_text().splitlines() if l.strip()])
    weiter = w.alle_weiterleitungen()

    abweichungen, gewollt = [], 0
    for pfad in routen:
        alt = live.get(pfad, {})
        alt_code, alt_ort = alt.get('status'), (alt.get('location') or '').replace(w.BASE, '')
        neu_code, neu_ort = hole(op, CONTAINER, pfad)
        neu_ort = (neu_ort or '').replace(CONTAINER, '')

        if pfad in GEWOLLT:
            gewollt += 1
            continue
        # Gestrichene Seiten sollen 410 antworten, wo frueher 200 stand.
        if pfad in w.ENTFALLEN:
            if neu_code != 410:
                abweichungen.append(f'{pfad}: {neu_code} statt 410 (gestrichen)')
            continue
        if pfad in weiter:
            ziel = weiter[pfad]
            if neu_code != 301:
                abweichungen.append(f'{pfad}: {neu_code} statt 301')
            elif neu_ort != ziel:
                abweichungen.append(f'{pfad}: leitet auf {neu_ort}, erwartet {ziel}')
            continue
        if alt_code != neu_code:
            abweichungen.append(f'{pfad}: alt {alt_code}, neu {neu_code}')
        elif alt_code == 301 and alt_ort != neu_ort:
            abweichungen.append(f'{pfad}: alt -> {alt_ort}, neu -> {neu_ort}')

    print(f'{len(routen)} Adressen verglichen, {gewollt} mit gewollter Abweichung '
          f'uebersprungen, {len(abweichungen)} Abweichung(en)')
    for a in abweichungen:
        print(f'  {a}')
    if gewollt:
        print('\nGewollte Abweichungen:')
        for p, grund in GEWOLLT.items():
            if p in routen:
                print(f'  {p:30s} {grund}')
    return 1 if abweichungen else 0


if __name__ == '__main__':
    sys.exit(main())
