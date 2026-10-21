#!/usr/bin/env python3
"""Erzeugt webroot/ aus dem entpackten WordPress-Dateibestand.

webroot/ wird bei jedem Lauf vollstaendig neu geschrieben - nichts dort
hineinlegen, was man behalten will. Selbstgeschriebenes gehoert nach
webroot-eigen/, Hugo mischt beide Verzeichnisse.

Braucht _build/wporig/ (siehe README, "Neu aufsetzen") und fuer die
Schriften einmal Netz.

    python3 -E -s _build/gen_static.py
"""
import json
import pathlib
import posixpath
import re
import shutil
import sys
import urllib.request
from urllib.parse import unquote

import wpdata as w

WP = w.B / 'wporig' / 'wordpress'
WEBROOT = w.REPO / 'webroot'
THEME = 'wp-content/themes/seafileger'

# Was die gerenderten Seiten tatsaechlich laden. Ermittelt aus den
# Schnappschuessen, nach dem Entfernen von HTML-Kommentaren: header.php
# und footer.php binden animations.css, animations-ie-fix.css und
# css3-animate-it.js nur auskommentiert ein.
THEME_DATEIEN = [
    'style.css',
    'manifest.json',
    'css/bootstrap.min.css',
    'css/template.min.css',
    'css/lightbox.min.css',
    'css/print.min.css',
    'js/jquery.min.js',
    'js/bootstrap.min.js',
    'js/jquery.sticky.js',
    'js/lightbox.min.js',
    'js/navigation.js',
    'js/parallax.min.js',
    'js/skip-link-focus-fix.js',
    'js/waypoints/jquery.waypoints.min.js',
]

# Nicht uebernommen, mit Absicht:
#   wp-content/plugins/cookie-notice   - kein Tracking mehr, kein Banner
#   wp-content/plugins/simple-lightbox - das Theme bringt eine eigene mit;
#                                        es waren zwei Lightboxen parallel
#   wp-includes/js/jquery              - das Theme laedt eigenes jQuery,
#                                        WordPress lud ein zweites dazu
#   wp-includes/css/.../block-library  - kein einziger wp-block-* im Text;
#                                        aligncenter & Co. stehen in
#                                        template.min.css

SCHRIFTEN = 'https://fonts.googleapis.com/css?family=Raleway:400,600,800|Roboto+Slab:300'
# Zwei url() im Theme-CSS zeigen absolut auf de.seafile.com. Relativ
# gemacht laedt die oertliche Vorschau sie nicht aus der Produktion.
EIGEN = re.compile(rb'(?:https?:)?//de\.seafile\.com(?=/)')
IMPORT = re.compile(rb"@import url\('https://fonts\.googleapis\.com/[^']*'\);")
URL = re.compile(r"""url\(\s*['"]?([^)'"]+?)['"]?\s*\)""")


def kopieren(quelle, zielpfad):
    ziel = WEBROOT / zielpfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(quelle, ziel)


# ---------------------------------------------------------------- Medien

def uploads():
    """Alles aus uploads/20NN/ ausser den nicht benutzten Zuschnitten.

    WordPress legt zu jedem Bild Zuschnitte an (-300x200 usw.). Die
    unbenutzten sind 68 MB und jederzeit neu erzeugbar; Originale bleiben
    alle, auch die unverlinkten - ein Original ist nicht wiederherstellbar,
    wenn das Archiv erst weg ist.

    Verweise werden aus dem *erzeugten* Inhalt gelesen, nicht aus dem
    Schnappschuss: srcset und sizes stehen dort mit drin, und
    prozentkodierte Namen muessen vor dem Vergleich dekodiert werden -
    sonst wirft man jedes Bild mit Umlaut im Namen weg.
    """
    text = []
    for p in (w.REPO / 'content').rglob('*.html'):
        text.append(p.read_text(encoding='utf-8'))
    for p in (w.REPO / 'layouts').rglob('*.html'):
        text.append(p.read_text(encoding='utf-8'))
    blob = '\n'.join(text)
    verwendet = {unquote(m.group(1))
                 for m in re.finditer(r'/wp-content/uploads/([^\s"\'\)\?<>\\,]+)', blob)}
    # Favicons stehen in der Vorlage, nicht im Inhalt - und die Bilder der
    # gestrichenen Seiten werden von Anhangseiten-Weiterleitungen noch
    # angesprochen.
    for ziel in w.anhangseiten().values():
        verwendet.add(unquote(ziel).replace('/wp-content/uploads/', ''))

    wurzel = WP / 'wp-content/uploads'
    n = weg = 0
    for datei in wurzel.rglob('*'):
        if not datei.is_file():
            continue
        rel = str(datei.relative_to(wurzel))
        if not re.match(r'^20\d\d/', rel):
            continue                       # Plugin-Kram, Logs, GeoLite
        if w.THUMBNAIL.search(rel) and rel not in verwendet:
            weg += 1
            continue
        kopieren(datei, f'wp-content/uploads/{rel}')
        n += 1
    return n, weg


# ----------------------------------------------------------------- Theme

def theme():
    """Die geladenen Dateien, alles was ihr CSS per url() nachzieht, und
    alles, worauf Inhalt oder Vorlagen zeigen.

    Der dritte Teil ist leicht zu vergessen und faellt erst im Browser
    auf: das Logo in der Kopfleiste, die Kopfbilder von /news/ und den
    Kategoriearchiven und die traurige Wolke der Fehlerseite stehen in
    layouts/ und in keinem Stylesheet.
    """
    offen = list(THEME_DATEIEN)
    for ordner in ('content', 'layouts'):
        for datei in (w.REPO / ordner).rglob('*.html'):
            for m in re.finditer(r'/wp-content/themes/seafileger/([^\s"\'\)\?<>\\]+)',
                                 datei.read_text(encoding='utf-8')):
                offen.append(unquote(m.group(1)))
    fertig = set()
    while offen:
        rel = offen.pop()
        if rel in fertig:
            continue
        fertig.add(rel)
        quelle = WP / THEME / rel
        if not quelle.exists():
            raise SystemExit(f'Theme-Datei fehlt: {quelle}')
        if rel.endswith('.css'):
            # Bytes, nicht Text: bootstrap.min.css hat CRLF-Zeilenenden,
            # und read_text() macht daraus stillschweigend LF. Das aendert
            # die Datei, ohne dass es jemand wollte.
            ziel = WEBROOT / THEME / rel
            ziel.parent.mkdir(parents=True, exist_ok=True)
            ziel.write_bytes(EIGEN.sub(b'', quelle.read_bytes()))
        else:
            kopieren(quelle, f'{THEME}/{rel}')
            continue
        # url() in CSS ist die Falle: ohne diesen Durchlauf fehlen
        # Schriften, Aufzaehlungszeichen und Lightbox-Pfeile.
        basis = posixpath.dirname(rel)
        for m in URL.finditer(quelle.read_text(encoding='utf-8', errors='replace')):
            ziel = m.group(1).strip()
            if ziel.startswith(('data:', 'http://', 'https://', '//', '#')):
                continue
            offen.append(posixpath.normpath(posixpath.join(basis, ziel)))
    return len(fertig)


def schriften():
    """Raleway und Roboto Slab selbst ausliefern statt von Google.

    template.min.css und print.min.css holen sie bis heute per @import
    von fonts.googleapis.com - also bei jedem Seitenaufruf eine Anfrage an
    Google, auf einer Seite, die mit Kontrolle ueber die eigenen Daten
    wirbt. Die Dateien liegen jetzt daneben, der @import zeigt auf
    fonts.css.
    """
    kopf = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/140.0 Safari/537.36'}
    css = urllib.request.urlopen(
        urllib.request.Request(SCHRIFTEN, headers=kopf), timeout=60).read().decode()
    verzeichnis = WEBROOT / THEME / 'font'
    verzeichnis.mkdir(parents=True, exist_ok=True)
    neu = []
    for block in re.findall(r'@font-face\s*\{.*?\}', css, re.S):
        m = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not m:
            continue
        url = m.group(1)
        name = (re.search(r"font-family:\s*'([^']+)'", block).group(1).replace(' ', '')
                + '-' + re.search(r'font-weight:\s*(\d+)', block).group(1)
                + '-' + url.rsplit('/', 1)[-1].split('.')[0] + '.woff2')
        (verzeichnis / name).write_bytes(
            urllib.request.urlopen(urllib.request.Request(url, headers=kopf), timeout=60).read())
        neu.append(block.replace(url, f'../font/{name}'))
    if not neu:
        raise SystemExit('Keine woff2-Dateien in der Google-Fonts-Antwort')
    (WEBROOT / THEME / 'css' / 'fonts.css').write_text(
        '/* Selbst ausgeliefert statt von fonts.googleapis.com.\n'
        '   Erzeugt von _build/gen_static.py. */\n' + '\n'.join(neu) + '\n',
        encoding='utf-8')
    for datei in ('css/template.min.css', 'css/print.min.css'):
        p = WEBROOT / THEME / datei
        roh = p.read_bytes()
        if not IMPORT.search(roh):
            raise SystemExit(f'@import auf Google Fonts nicht gefunden in {datei}')
        p.write_bytes(IMPORT.sub(b"@import url('fonts.css');", roh))
    return len(neu)


def manifest():
    """manifest.json geradeziehen.

    Im Original: absolute Adressen, `"type": "image/png"` fuer eine
    SVG-Datei und `"scope": "/maps/"` - letzteres aus dem Beispiel von
    Google uebernommen und nie angefasst. Mit diesem scope gilt das
    Manifest nur fuer /maps/, also nirgends.
    """
    p = WEBROOT / THEME / 'manifest.json'
    m = json.loads(p.read_text(encoding='utf-8'))
    m['icons'] = [{'src': f'/{THEME}/img/svg/seafile_logo_proposed.svg',
                   'type': 'image/svg+xml', 'sizes': 'any'}]
    m['scope'] = '/'
    m['theme_color'] = '#FFA10F'          # wie <meta name="theme-color">
    p.write_text(json.dumps(m, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def robots():
    (WEBROOT / 'robots.txt').write_text(
        'User-agent: *\nDisallow:\n\n'
        'Sitemap: https://de.seafile.com/sitemap_index.xml\n', encoding='utf-8')


def main():
    if WEBROOT.exists():
        shutil.rmtree(WEBROOT)
    WEBROOT.mkdir()
    t = theme()
    s = schriften()
    manifest()
    robots()
    n, weg = uploads()
    groesse = sum(f.stat().st_size for f in WEBROOT.rglob('*') if f.is_file())
    print(f'{t} Theme-Dateien, {s} Schriftschnitte, {n} Medien '
          f'({weg} unbenutzte Zuschnitte ausgelassen), {groesse/1048576:.0f} MB')


if __name__ == '__main__':
    sys.exit(main())
