#!/usr/bin/env python3
"""Holt die vier Menues aus dem Schnappschuss nach data/.

Die Menues steckten in der Datenbank, nicht im Dateibestand: Hauptmenue
und Fusszeile als wp_nav_menu, das Seitenmenue der Anleitungen als
eigenes Menue "Seafileanleitung". Als YAML sind sie aenderbar, ohne dass
jemand 47 Inhaltsdateien anfassen muss.

Laeuft einmal bei der Migration. Danach werden die Dateien von Hand
gepflegt - ein zweiter Lauf wuerde Aenderungen ueberschreiben.

    python3 -E -s _build/gen_menues.py
"""
import html
import re
import sys

import wpdata as w

DATA = w.REPO / 'data'
EIGEN = re.compile(r'https?://de\.seafile\.com')


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def adresse(u):
    return EIGEN.sub('', html.unescape(u)) or '/'


def eintraege(ul):
    """Eine <ul> in eine Liste von {titel, ziel, unterpunkte} verwandeln.

    Die Verschachtelung geht nur eine Ebene tief; mehr hat das Menue nie
    gehabt, und wp_nav_menu haette es auch nicht anders ausgegeben.
    """
    aus = []
    tiefe = 0
    for m in re.finditer(r'<(/?)(ul|li|a)\b([^>]*)>', ul):
        schluss, tag, rest = m.group(1), m.group(2), m.group(3)
        if tag == 'ul':
            tiefe += -1 if schluss else 1
        elif tag == 'a' and not schluss:
            ziel = re.search(r'href="([^"]*)"', rest)
            ende = ul.index('</a>', m.end())
            eintrag = {'titel': text(ul[m.end():ende]),
                       'ziel': adresse(ziel.group(1) if ziel else '#')}
            if tiefe <= 1 or not aus:
                aus.append(eintrag)
            else:
                aus[-1].setdefault('unterpunkte', []).append(eintrag)
    return aus


def ul_nach(s, kennung):
    """Die <ul> mit dieser id, mitsamt ihren verschachtelten <ul>.

    Nicht mit einem nicht-gierigen (.*?)</ul> zu machen: das Seitenmenue
    der Anleitungen hat Untermenues, und der Abgleich endet dann am
    ersten inneren </ul>. Also die Ebenen zaehlen.
    """
    anfang = re.search(r'<ul id="' + re.escape(kennung) + r'"[^>]*>', s)
    if not anfang:
        raise SystemExit(f'Menue {kennung} nicht im Schnappschuss gefunden')
    tiefe, pos = 1, anfang.end()
    for m in re.finditer(r'<(/?)ul\b[^>]*>', s[anfang.end():]):
        tiefe += -1 if m.group(1) else 1
        if tiefe == 0:
            pos = anfang.end() + m.end()
            break
    else:
        raise SystemExit(f'Menue {kennung}: schliessendes </ul> fehlt')
    return s[anfang.start():pos]


# Verweise in den Menues, die so nur ueber eine WordPress-Weiterleitung
# funktionierten. Der Fusszeilen-Punkt "Kontakt" stand auf jeder der 111
# Seiten und schickte jeden Besucher ueber eine 301.
KORREKTUREN = {
    '/individueller-support/#kontakt': '/support/individueller-support/#kontakt',
}


def ohne_gestrichene(punkte):
    """Punkte auf gestrichene Seiten fallen raus - auch ganze Untermenues.

    Der Zweig "Seafile Drive Client 1.0" haengt mit sechs Unterpunkten im
    Seitenmenue; ohne diesen Schritt bliebe er dort stehen und zeigte auf
    Weiterleitungen.
    """
    aus = []
    for p in punkte:
        if p['ziel'] in w.GESTRICHEN:
            continue
        if p['ziel'] in KORREKTUREN:
            p = dict(p, ziel=KORREKTUREN[p['ziel']])
        if p.get('unterpunkte'):
            p = dict(p, unterpunkte=ohne_gestrichene(p['unterpunkte']))
        aus.append(p)
    return aus


def yaml(eintraege_, einzug='  '):
    zeilen = []
    for e in eintraege_:
        zeilen.append(f'{einzug}- titel: "{e["titel"]}"')
        zeilen.append(f'{einzug}  ziel: "{e["ziel"]}"')
        if e.get('unterpunkte'):
            zeilen.append(f'{einzug}  unterpunkte:')
            zeilen += yaml(e['unterpunkte'], einzug + '    ')
    return zeilen


def main():
    DATA.mkdir(exist_ok=True)
    start = (w.REFERENCE / 'index.html').read_text(encoding='utf-8')
    anleitung = (w.REFERENCE / 'support_benutzer_anleitung_seahub.html').read_text(encoding='utf-8')

    # Hauptmenue
    (DATA / 'navigation.yaml').write_text(
        '# Hauptmenue. Uebernommen aus dem WordPress-Menue "Hauptmenue".\n'
        'punkte:\n' + '\n'.join(yaml(ohne_gestrichene(eintraege(ul_nach(start, 'primary-menu'))))) + '\n',
        encoding='utf-8')

    # Seitenmenue der Anleitungen
    (DATA / 'anleitung.yaml').write_text(
        '# Seitenmenue der Anleitungsseiten (WordPress-Menue\n'
        '# "Seafileanleitung"). Steht auf allen Seiten mit handbuch: true.\n'
        'punkte:\n' + '\n'.join(yaml(ohne_gestrichene(
            eintraege(ul_nach(anleitung, 'menu-seafileanleitung'))))) + '\n',
        encoding='utf-8')

    # Fusszeile: vier Widget-Spalten, jede mit <h4> und einem Menue
    fuss = re.search(r'<footer.*?</footer>', start, re.S).group(0)
    spalten = []
    for sp in re.findall(r'<div class="col-md-3[^"]*"[^>]*>(.*?)</div>\s*(?=<div class="col-md-3|</div>)',
                         fuss, re.S):
        ueber = re.search(r'<h4>(.*?)</h4>', sp)
        kennung = re.search(r'<ul id="([^"]+)"', sp)
        if not (ueber and kennung):
            continue
        spalten.append((text(ueber.group(1)), eintraege(ul_nach(sp, kennung.group(1)))))
    if len(spalten) != 4:
        raise SystemExit(f'Fusszeile: {len(spalten)} Spalten statt 4 gefunden')
    zeilen = ['# Fusszeile, vier Spalten. Uebernommen aus den vier',
              '# Widget-Bereichen footer_1 bis footer_4.',
              '#',
              '# Punkte auf gestrichene Seiten sind entfernt - hier der',
              '# Eintrag "Seafile Drive Client 1.0" (siehe BESTANDSAUFNAHME.md).',
              'spalten:']
    for ueber, punkte in spalten:
        zeilen.append(f'  - ueberschrift: "{ueber}"')
        zeilen.append('    punkte:')
        zeilen += yaml(ohne_gestrichene(punkte), '      ')
    (DATA / 'fusszeile.yaml').write_text('\n'.join(zeilen) + '\n', encoding='utf-8')

    print(f'navigation.yaml, anleitung.yaml, fusszeile.yaml ({len(spalten)} Spalten) geschrieben')


if __name__ == '__main__':
    sys.exit(main())
