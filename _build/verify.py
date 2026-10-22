#!/usr/bin/env python3
"""Vergleicht die gebauten Seiten mit dem Stand, den WordPress ausgeliefert hat.

Verglichen wird nicht Markup gegen Markup - das Geruest ist neu
geschrieben -, sondern dreierlei je Adresse:

  * der sichtbare Text jedes Blockelements (Absatz, Ueberschrift,
    Listenpunkt, Tabellenzelle). Was im alten Stand stand und im neuen
    fehlt, wird gemeldet. Was hinzukommt, nicht: das Suchfeld und die
    Themenuebersicht an neuer Stelle sind gewollt.
  * die eingebundenen Mediendateien.
  * die Verweisziele.

Ein Byte-Vergleich waere nach dem Umzug ein Fehlalarmgenerator, sobald
jemand einen Text aendert. Diese Pruefung bleibt auch danach brauchbar,
weil sie nur meldet, was verschwindet.

Was mit Absicht verschwunden ist, steht in GEWOLLT - mit Begruendung.

    hugo --gc && python3 -E -s _build/verify.py
"""
import html
import re
import sys
from urllib.parse import unquote

import wpdata as w

PUBLIC = w.REPO / 'public'
BERICHT = w.B / 'verify-diff.txt'

ALT = re.compile(r'</nav>(.*)</div><!-- #content -->', re.S)
NEU = re.compile(r'</nav>(.*)<footer', re.S)
BLOCK = re.compile(
    r'<(p|h[1-6]|li|td|th|dt|dd|figcaption|blockquote)\b[^>]*>(.*?)</\1>', re.S | re.I)

# Texte und Dateien, die mit Absicht weg sind. Begruendung in
# BESTANDSAUFNAHME.md; ohne diese Liste meldet jede Anleitungsseite den
# fehlenden Menuepunkt des SeaDrive-1.0-Zweigs.
GEWOLLT = {
    # gestrichener Zweig im Seitenmenue der Anleitungen (47 Seiten)
    'Seafile Drive Client 1.0',
    'SeaDrive mit Server verbinden',
    'Client-Einstellungen verwalten',
    # Kacheln auf /support/administratoren/
    'Featurelog',
    'Erweiterung SeaMate',
    'Seafile für UCS',
    'Welche Funktion kam wann?',
    'SeaMate',
    'Die Seafile App für UCS im Detail.',
    'Die Entwicklung von Seafile aus Funktionssicht.',
    # Knopf auf /downloads/
    'Zum Featurelog',
    # umformuliert, weil /plugin-integration/ wegfaellt: das Add-in liegt
    # auch unter /downloads/
    'Das Add-in kann von dieser Webseite kostenfrei heruntergeladen',
    # Fusszeilenpunkt
    'Seafile Drive Client 1.0 ',
    # Drei Abschnitte der Datenschutzerklaerung, die eine Einbindung
    # beschrieben, die es nicht mehr gibt: Schriften werden selbst
    # ausgeliefert, reCAPTCHA ist durch Altcha ersetzt, und Google Maps
    # war nie eingebunden. Eine Erklaerung, die eine Uebermittlung an
    # Google behauptet, die nicht stattfindet, ist schlechter als keine.
    'Wir binden die Schriftarten',
    'Wir binden die Funktion zur Erkennung von Bots',
    'Wir binden die Landkarten des Dienstes',
    # index.php schrieb auf /news/ ein zweites <p> statt eines </p>. Der
    # Absatz blieb dadurch offen und zog die Kategorieleiste und das
    # Suchfeld in denselben Block. Hier ist er geschlossen - der Text
    # steht vollstaendig da, nur nicht mehr in einem Stueck.
    'Neuigkeiten zu Seafile, Release Notes zu neuen Programmversionen',
}
GEWOLLTE_MEDIEN = {
    '/wp-content/uploads/2018/10/featurelog.svg',
    '/wp-content/uploads/2018/10/seamate.svg',
    # Heissverweise auf datamate.org, dort beim Umzug weggefallen; liegen
    # jetzt unter /eigen/bilder/ (siehe webroot-eigen/eigen/bilder/
    # HERKUNFT.md)
    'https://www.datamate.org/wp-content/uploads/2018/06/Seahub_Action_Buttons-1024x434.jpg',
    'https://www.datamate.org/wp-content/uploads/2018/06/markdowneditor_tableediting-1024x503.jpg',
}


def saeubern(s):
    s = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', s, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', ' ', s, flags=re.S)


def gesamttext(s):
    t = html.unescape(re.sub(r'<[^>]+>', ' ', saeubern(s)))
    return re.sub(r'\s+', ' ', t.replace('\u00a0', ' ')).strip()


def bloecke(s):
    """Sichtbarer Text je Blockelement, Leeres und Einzelwoerter raus.

    Gesucht wird spaeter nicht Block gegen Block, sondern jeder alte Block
    im Gesamttext der neuen Seite. Grund: template-parts/content.php legte
    um den Beitragstext ein <p>, das nie geschlossen wurde - ein alter
    "Absatz" reicht dadurch bis weit in den naechsten hinein. Ein
    Vergleich Block gegen Block meldete das als Verlust, obwohl nur die
    Schachtelung repariert ist.
    """
    aus = set()
    for m in BLOCK.finditer(saeubern(s)):
        t = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))
        t = re.sub(r'\s+', ' ', t.replace(' ', ' ')).strip()
        if len(t) >= 25:
            aus.add(t)
    return aus


def medien(s):
    aus = set()
    for m in re.finditer(r'(?:src|href)="([^"]+)"', html.unescape(saeubern(s))):
        # Das alte Kartenmarkup hatte einen Zeilenumbruch im src-Attribut
        # (<img src="\n\t\t\t<?php the_post_thumbnail_url() ?>">).
        u = unquote(m.group(1).split('#')[0]).strip().replace(w.BASE, '')
        if '/wp-content/uploads/' in u:
            aus.add(u)
    return aus


def ziele(s):
    aus = set()
    for m in re.finditer(r'href="([^"]+)"', html.unescape(saeubern(s))):
        u = unquote(m.group(1).split('#')[0]).replace(w.BASE, '')
        if u.startswith(('http://', 'https://')) or (u.startswith('/') and 'uploads' not in u):
            aus.add(u.rstrip('/') or '/')
    return aus


def rumpf(muster, datei):
    m = muster.search(datei.read_text(encoding='utf-8', errors='replace'))
    return m.group(1) if m else None


def main():
    pfade = {w.pfad(p['link']) for p in w.seiten()} | {w.pfad(b['link']) for b in w.beitraege()}
    pfade |= {'/news/'} | {f"/category/{c['slug']}/" for c in w.kategorien()}
    # Ziele, die es nach dem Umzug nicht mehr gibt - Verweise darauf
    # sollen fehlen.
    entfallen = {p.rstrip('/') for p in w.GESTRICHEN} | {
        g.rstrip('/') for g in ('https://www.datamate.org/seafile/seamate/',
                                '/authentifizierungsmethoden-von-seafile-im-ueberblick',
                                '/support/benuter/anleitung/seafile-sync-client',
                                '/featurelog')}

    zeilen, schlecht = [], 0
    for pfad in sorted(pfade):
        name = (pfad.strip('/') or 'index').replace('/', '_') + '.html'
        alt_datei = w.REFERENCE / name
        neu_datei = (PUBLIC / 'index.html' if pfad == '/'
                     else PUBLIC / pfad.strip('/') / 'index.html')
        if not alt_datei.exists() or not neu_datei.exists():
            zeilen.append(f'{pfad}: {"kein Schnappschuss" if not alt_datei.exists() else "nicht gebaut"}')
            schlecht += 1
            continue
        a_roh, n_roh = rumpf(ALT, alt_datei), rumpf(NEU, neu_datei)
        if a_roh is None or n_roh is None:
            zeilen.append(f'{pfad}: Rumpf nicht abgrenzbar')
            schlecht += 1
            continue

        neu_text = gesamttext(n_roh)
        fehlt_text = {t for t in bloecke(a_roh)
                      if t not in neu_text and not any(g in t for g in GEWOLLT)}
        fehlt_medien = {m for m in medien(a_roh) - medien(n_roh) if m not in GEWOLLTE_MEDIEN}
        fehlt_ziele = {z for z in ziele(a_roh) - ziele(n_roh) if z not in entfallen}

        for art, menge in (('Text', fehlt_text), ('Medien', fehlt_medien),
                           ('Verweise', fehlt_ziele)):
            if menge:
                schlecht += 1
                zeilen.append(f'{pfad}: {len(menge)} {art} fehlen')
                for f in sorted(menge)[:5]:
                    zeilen.append(f'    - {f[:160]}')

    BERICHT.write_text('\n'.join(zeilen) + '\n', encoding='utf-8')
    print(f'{len(pfade)} Adressen verglichen, {schlecht} Abweichung(en)')
    if zeilen:
        print('\n'.join(zeilen[:80]))
        print(f'\nvollstaendig in {BERICHT.relative_to(w.REPO)}')
    return 1 if schlecht else 0


if __name__ == '__main__':
    sys.exit(main())
