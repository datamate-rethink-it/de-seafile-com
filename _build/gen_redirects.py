#!/usr/bin/env python3
"""Erzeugt deploy/redirects.caddy aus _build/wpdata.py.

Die Datei ist erzeugt und gehoert trotzdem ins Repo: so sieht man im Diff,
was sich an den Adressen aendert, und der Bau braucht kein Python. Die
Pruefung in .github/workflows/build.yml laesst das Skript laufen und
vergleicht - wer eine Seite streicht und das Erzeugen vergisst, faellt auf.

    python3 -E -s _build/gen_redirects.py
"""
import json
import sys

import wpdata as w

ZIEL = w.REPO / 'deploy' / 'redirects.caddy'

KOPF = """\
# Weiterleitungen und entfallene Adressen von de.seafile.com.
#
# ERZEUGT von _build/gen_redirects.py - nicht von Hand aendern.
# Was hier steht, wird in _build/wpdata.py entschieden.
#
# Die Regeln stecken mit Absicht im Image und nicht im vhost des Servers:
# so sind sie mit dem Inhalt zusammen versioniert, und ein Rueckschritt auf
# eine aeltere Fassung nimmt die Regeln mit.
#
# Die Weiterleitungen kommen aus sechs Quellen:
#
#   {plugin:4d}  Regeln des Plugins Redirection
#   {ersetzt:4d}  gestrichene Seiten mit Nachfolger
#   {suffixe:4d}  Endstuecke von Pfaden (/seahub/ -> der volle Pfad) -
#         das hat WordPress von sich aus getan, es steht nirgends
#   {news:4d}  /news/<beitrag>/ -> /<beitrag>/ (Praefix der Beitragsseite)
#   {anhang:4d}  Anhangseiten von Bildern -> die Bilddatei (Yoast)
#   {altlast:4d}  alte Slugs und Rateversuche, eingesammelt mit
#         _build/gen_altlasten.py, weil sie in keiner API stehen
#   {jahre:4d}  Datumsarchive -> /news/
#
# Pruefen:
#   docker run --rm \\
#     -v ./deploy/Caddyfile.container:/etc/caddy/Caddyfile:ro \\
#     -v ./deploy/redirects.caddy:/etc/caddy/redirects.caddy:ro \\
#     caddy:2.11.7-alpine caddy validate --adapter caddyfile \\
#     --config /etc/caddy/Caddyfile
"""


def main():
    weiter = w.alle_weiterleitungen()
    zeilen = [KOPF.format(
        plugin=len(w.PLUGIN_WEITERLEITUNGEN), ersetzt=len(w.ERSETZT),
        suffixe=len(w.pfadsuffixe()), news=len(w.news_praefix()),
        anhang=len(w.anhangseiten()), altlast=len(w.altlasten()),
        jahre=len(w.datumsarchive()))]

    zeilen.append('\n# --- 410 Gone: gestrichen, kein Nachfolger -----------------------')
    zeilen.append('# Als handle-Block, nicht als blankes "error @entfallen 410":')
    zeilen.append('# Caddy sortiert die Direktiven, und error landet dabei hinter den')
    zeilen.append('# handle-Bloecken der Caddyfile. Die statische Auslieferung greift')
    zeilen.append('# dann zuerst, findet nichts und antwortet 404 statt 410. Als')
    zeilen.append('# handle steht die Regel in der Reihenfolge, in der sie dasteht -')
    zeilen.append('# und redirects.caddy wird vor allen anderen handle importiert.')
    zeilen.append('@entfallen path ' + ' '.join(sorted(w.ENTFALLEN)))
    zeilen.append('handle @entfallen {')
    zeilen.append('\terror 410')
    zeilen.append('}')

    gruppen = [
        ('Plugin Redirection', w.PLUGIN_WEITERLEITUNGEN),
        ('gestrichene Seiten mit Nachfolger', w.ERSETZT),
        ('Datumsarchive', w.datumsarchive()),
        ('alte Slugs und Rateversuche (gen_altlasten.py)', w.altlasten()),
        ('Endstuecke von Pfaden', w.pfadsuffixe()),
        ('/news/<beitrag>/ -> /<beitrag>/', w.news_praefix()),
        ('Anhangseiten -> Bilddatei', w.anhangseiten()),
    ]
    gesehen = set()
    for titel, regeln in gruppen:
        teil = [(q, z) for q, z in sorted(regeln.items())
                if q not in gesehen and weiter.get(q) == z]
        gesehen |= {q for q, _ in teil}
        if not teil:
            continue
        zeilen.append(f'\n# --- {titel} ({len(teil)}) '
                      + '-' * max(0, 56 - len(titel) - len(str(len(teil)))))
        for quelle, ziel in teil:
            zeilen.append(f'redir {quelle} {ziel} permanent')

    zeilen.append('\n# --- Sitemap --------------------------------------------------')
    zeilen.append('redir /sitemap.xml /sitemap_index.xml permanent')

    fehlt = set(weiter) - gesehen - {'/sitemap.xml'}
    if fehlt:
        raise SystemExit(f'Nicht ausgegebene Regeln: {sorted(fehlt)[:5]}')

    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text('\n'.join(zeilen) + '\n', encoding='utf-8')

    uebersicht = {'entfallen': sorted(w.ENTFALLEN), 'weiterleitungen': weiter}
    (w.B / 'weiterleitungen.json').write_text(
        json.dumps(uebersicht, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'{len(weiter)} Weiterleitungen und {len(w.ENTFALLEN)} entfallene '
          f'Adressen nach {ZIEL.relative_to(w.REPO)}')


if __name__ == '__main__':
    sys.exit(main())
