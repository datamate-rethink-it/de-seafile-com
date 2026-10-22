#!/usr/bin/env python3
"""Erzeugt content/ aus den Daten der alten WordPress-Installation.

Der Text kommt aus den gerenderten Seiten in reference/, nicht aus der
REST-API: die API verschluckt die <!--more-->-Marke, an der WordPress den
Teaser fuer /news/ abschneidet, und sie liefert die Bilder ohne die
loading/decoding/srcset-Attribute, die der Server tatsaechlich ausliefert.
Die Metadaten (Titel, Beschreibung, Daten, Kategorie) kommen aus der API.

Das Geruest jeder Seite - Kopfleiste, Fusszeile, Seitenleiste der
Anleitungen, Beitragskopf - steckt in layouts/ und *nicht* im Inhalt.
Sonst muesste man 47 Dateien anfassen, um einen Menuepunkt zu aendern.

    python3 -E -s _build/gen_content.py
"""
import html
import pathlib
import re
import shutil
import sys

import wpdata as w

CONTENT = w.REPO / 'content'

# Verzeichnisse unter content/, die von Hand gepflegt werden und beim
# Neuerzeugen stehen bleiben. /suche/ ersetzt die WordPress-Suche und hat
# in den alten Daten keine Entsprechung.
EIGENE = {'suche'}

# Grenzen des Theme-Rumpfes: header.php endet mit </nav>, footer.php
# beginnt mit </div><!-- #content -->. Gilt fuer alle 159 Schnappschuesse.
RUMPF = re.compile(r'</nav>(.*)</div><!-- #content -->', re.S)

# Innerhalb einer Anleitungsseite (manual.php): rechte Spalte, zwischen der
# Ueberschrift und dem "Zuletzt geaendert"-Fuss.
HANDBUCH = re.compile(
    r'<div class="col-md-8">\s*<h2>.*?</h2>(.*?)\s*<hr/>\s*<p><i><b>Zuletzt', re.S)

# Innerhalb eines Beitrags (single.php + template-parts/content.php):
# zwischen der Ueberschrift und dem schliessenden Absatz, den content.php
# um den gesamten Text legt.
BEITRAG = re.compile(
    r'<h1 class="entry-title">.*?</h1>\s*<p>(.*?)</p>\s*<div>\s*</div><!-- #primary -->', re.S)

MEHR = re.compile(r'<span id="more-\d+"></span>')

# Im Text stehen die Adressen absolut. Relativ gemacht bleibt der Inhalt
# vom Hostnamen unabhaengig und die oertliche Vorschau zeigt ehrlich an,
# welche Datei im Dateibestand fehlt, statt sie aus der Produktion zu
# holen. Nur der eigene Host - fremde Adressen bleiben, wie sie sind.
EIGEN = re.compile(r'(?:https?:)?//de\.seafile\.com(?=/)')


def relativ(s):
    return EIGEN.sub('', s)


# ------------------------------------------------- Korrekturen am Text
#
# Verweise im uebernommenen Text, die ins Leere zeigen oder auf eine
# gestrichene Seite. Sie hier zu fuehren statt die erzeugten Dateien von
# Hand nachzubessern ist der Punkt: gen_content.py schreibt content/ bei
# jedem Lauf neu.
#
# Jede Regel muss genau einmal greifen, sonst bricht der Lauf ab - eine
# Korrektur, die stillschweigend ins Leere laeuft, waere schlimmer als
# keine.

KORREKTUREN = {
    # Zeigte auf einen Beitrag, den es nie gab (404 auch in der alten
    # Seite). Gemeint sind die Authentifizierungsmethoden, und darueber
    # schreibt /ad-ldap/.
    '/admin-delegation/': [
        ('href="/authentifizierungsmethoden-von-seafile-im-ueberblick"', 'href="/ad-ldap/"'),
    ],
    # Tippfehler im Pfad: "benuter".
    '/seafile-sync-client-als-windows-dienst/': [
        ('href="/support/benuter/anleitung/seafile-sync-client"',
         'href="/support/benutzer/anleitung/seafile-sync-client/"'),
    ],
    # Zwei Bilder lagen als Heissverweis auf datamate.org und sind beim
    # dortigen Umzug weggefallen (siehe webroot-eigen/eigen/bilder/
    # HERKUNFT.md). Jetzt liefert de.seafile.com sie selbst aus.
    '/seafile-professional-server-version-6-3-ab-heute-production-ready/': [
        ('https://www.datamate.org/wp-content/uploads/2018/06/Seahub_Action_Buttons-1024x434.jpg',
         '/eigen/bilder/Seahub_Action_Buttons-1024x434.jpg'),
        ('https://www.datamate.org/wp-content/uploads/2018/06/markdowneditor_tableediting-1024x503.jpg',
         '/eigen/bilder/markdowneditor_tableediting-1024x503.jpg'),
    ],
    # /plugin-integration/ faellt weg. Das Outlook-Add-in liegt aber auch
    # unter /downloads/, der Download geht also nicht verloren.
    '/support/benutzer/anleitung/seafile-outlook-addin/': [
        ('<a href="/plugin-integration/">dieser Webseite</a>',
         '<a href="/downloads/">der Downloadseite</a>'),
    ],
    # Der Knopf "Zum Featurelog" verschwindet; direkt daneben steht schon
    # einer auf das Changelog im Seafile Manual.
    '/downloads/': [
        ('\n\t\t\t\t\t<a class="button blue small" href="/featurelog"'
         ' target="_blank" rel="noopener noreferrer"> Zum Featurelog</a>', ''),
    ],
}

# Ganze Kacheln, die wegfallen: <div class="col-sm-12 col-md-3"> mit
# genau diesem Ziel.
KACHELN_WEG = {
    '/support/administratoren/': [
        # gestrichen
        '/featurelog/',
        '/support/administratoren/dokumentation-seafile-app-ucs/',
        # SeaMate ist bei datamate.org eingestellt, die Adresse
        # antwortet seit dem 21.10.2026 mit 410
        'https://www.datamate.org/seafile/seamate/',
    ],
}

KACHEL = r'<div class="col-sm-12 col-md-3">\s*<a href="{}".*?</a>\s*</div>'


def korrigieren(pfad, koerper):
    for alt, neu in KORREKTUREN.get(pfad, []):
        if koerper.count(alt) != 1:
            raise SystemExit(
                f'Korrektur fuer {pfad} greift {koerper.count(alt)}x statt einmal:\n  {alt[:90]}')
        koerper = koerper.replace(alt, neu)
    for ziel in KACHELN_WEG.get(pfad, []):
        muster = re.compile(KACHEL.format(re.escape(ziel)), re.S)
        koerper, n = muster.subn('', koerper)
        if n != 1:
            raise SystemExit(f'Kachel {ziel} auf {pfad}: {n} Treffer statt einem')
    return koerper


BLOCKANFANG = re.compile(
    r'<(p|h[1-6]|ul|ol|div|section|table|figure|blockquote|pre|img)\b', re.I)


def absatz_ergaenzen(koerper):
    """Fuehrenden Fliesstext in einen eigenen Absatz fassen.

    template-parts/content.php legte um den gesamten Beitragstext ein
    <p>...</p>. Bei Beitraegen, deren Text mit einem Blockelement beginnt
    (die meisten), war das ein ungueltig verschachteltes Absatzelement,
    das der Browser sofort wieder schloss - ohne Wirkung. Bei dreien
    (/ad-ldap/, /api/, /cluster/) beginnt der Text aber mit blankem
    Fliesstext, und dort war dieses <p> der einzige Absatz, den er hatte.

    Statt den Fehler nachzubauen, bekommt dieser Text hier seinen eigenen
    Absatz.
    """
    koerper = koerper.strip()
    m = BLOCKANFANG.search(koerper)
    if not m or m.start() == 0:
        return koerper
    return f'<p>{koerper[:m.start()].strip()}</p>\n{koerper[m.start():]}'


def trial_formular(inhalt):
    """Das Trial-Formular auf den neuen Endpunkt und auf Altcha umstellen.

    Bisher ein gewoehnlicher POST auf /trial/ selbst, den
    content-trail-page.php beantwortet hat, mit reCAPTCHA von Google. Jetzt
    postet webroot-eigen/eigen/seite.js nach /api/trial; Caddy im Image
    reicht das an trial.seafile-demo.de weiter, wo der Code laeuft und wo
    Seafile-API und Brevo-Schluessel oertlich liegen.

    reCAPTCHA ist raus. Es lud Google unbedingt beim Oeffnen der Seite -
    auf der einzigen Seite der Website, die ueberhaupt etwas von einem
    Fremden holte, und ausgerechnet unter der Zeile "Uebernehmen Sie die
    Kontrolle ueber Ihre Daten". An seine Stelle tritt Altcha: das Widget
    liegt unter /eigen/, die Aufgabe kommt von /api/trial/challenge, und
    gerechnet wird im Browser.
    """
    neu = inhalt.replace(
        '<form class="well form-horizontal" method="POST">',
        '<form class="well form-horizontal" id="trial-formular" method="post" action="/api/trial">')
    if neu == inhalt:
        raise SystemExit('Trial: das <form>-Element sieht anders aus als erwartet')

    # auto="onfocus": gerechnet wird, sobald jemand das Formular anfasst -
    # nicht beim Oeffnen der Seite und nicht erst beim Absenden.
    widget = ('<altcha-widget style="margin-bottom: 12px;" '
              'challengeurl="/api/trial/challenge" auto="onfocus" hidelogo hidefooter '
              'strings=\'{"label":"Ich bin ein Mensch","verifying":"Pr\u00fcfe \u2026",'
              '"verified":"Gepr\u00fcft","error":"Pr\u00fcfung fehlgeschlagen",'
              '"expired":"Abgelaufen, bitte erneut versuchen"}\'></altcha-widget>')
    neu, n = re.subn(
        r'<div style="margin-bottom: 12px;" class="g-recaptcha" data-sitekey="[^"]*"></div>',
        widget.replace('\\', '\\\\'), neu)
    if n != 1:
        raise SystemExit(f'Trial: {n} reCAPTCHA-Kaestchen gefunden statt einem')

    # Zeilenenden sind hier \r\n - der Text kommt aus einem Editor unter
    # Windows durch die WordPress-Datenbank.
    alt_skript = ('<!-- eingebaut am 27.08.2025 um 01:30 Uhr -->\r\n'
                  '<script src="https://www.google.com/recaptcha/api.js" async defer></script>')
    if alt_skript not in neu:
        raise SystemExit('Trial: das reCAPTCHA-Skript sieht anders aus als erwartet')
    return neu.replace(alt_skript, '<script src="/eigen/altcha.min.js" type="module" defer></script>')


def schnappschuss(pfad):
    name = (pfad.strip('/') or 'index').replace('/', '_') + '.html'
    datei = w.REFERENCE / name
    if not datei.exists():
        raise SystemExit(f'Schnappschuss fehlt: {datei}')
    return datei.read_text(encoding='utf-8')


def rumpf(pfad):
    m = RUMPF.search(schnappschuss(pfad))
    if not m:
        raise SystemExit(f'Kein Theme-Rumpf in {pfad} - Grenzen pruefen')
    return m.group(1)


def entity(s):
    """&raquo; und Co. aus den Titeln holen, fuer die Frontmatter."""
    return html.unescape(s or '').strip()


def yoast(it, feld):
    return (it.get('yoast_head_json') or {}).get(feld)


def lesezeit(it):
    for k, v in ((it.get('yoast_head_json') or {}).get('twitter_misc') or {}).items():
        if 'Lesezeit' in k:
            return v
    return None


def beitragsbild(it):
    """Das Beitragsbild (featured image) in Originalgroesse.

    Die alten Beitragskarten und der Kopfbereich eines Beitrags benutzten
    the_post_thumbnail_url(), also diese Datei - nicht das og:image von
    Yoast, das eine andere sein kann. Ohne diese Unterscheidung zeigen die
    Karten auf /news/ andere Bilder als bisher.
    """
    kennung = it.get('featured_media')
    if not kennung:
        return None
    for m in _medien():
        if m['id'] == kennung:
            return relativ(m['source_url'])
    return None


_medien_zwischenspeicher = []


def _medien():
    if not _medien_zwischenspeicher:
        _medien_zwischenspeicher.extend(w.laden('media.json'))
    return _medien_zwischenspeicher


def ogbild(it):
    # Relativ wie der uebrige Inhalt; die Vorlage macht daraus mit absURL
    # wieder eine vollstaendige Adresse, weil og:image absolut sein muss.
    bilder = yoast(it, 'og_image') or []
    return relativ(bilder[0]['url']) if bilder else None


def yamlwert(v):
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, int):
        return str(v)
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'


def schreiben(ziel, frontmatter, koerper):
    ziel.parent.mkdir(parents=True, exist_ok=True)
    zeilen = ['---']
    for k, v in frontmatter.items():
        if v is None:
            continue
        if isinstance(v, list):
            zeilen.append(f'{k}:')
            zeilen += [f'  - {yamlwert(x)}' for x in v]
        else:
            zeilen.append(f'{k}: {yamlwert(v)}')
    zeilen.append('---')
    ziel.write_text('\n'.join(zeilen) + '\n' + koerper.strip() + '\n', encoding='utf-8')


# ------------------------------------------------------------------ Seiten

def seitenziel(pfad, hat_kinder):
    """Branch Bundle fuer Seiten mit Unterseiten, sonst Leaf Bundle."""
    teile = [t for t in pfad.strip('/').split('/') if t]
    if not teile:
        return CONTENT / '_index.html'
    name = '_index.html' if hat_kinder else 'index.html'
    return CONTENT.joinpath(*teile) / name


def seiten_schreiben():
    bleibt = w.seiten()
    pfade = {w.pfad(p['link']) for p in bleibt}
    n = 0
    for p in bleibt:
        pfad = w.pfad(p['link'])
        hat_kinder = any(q != pfad and q.startswith(pfad) for q in pfade)
        if p['template'] == 'manual.php':
            m = HANDBUCH.search(rumpf(pfad))
            if not m:
                raise SystemExit(f'Anleitungsseite {pfad}: rechte Spalte nicht gefunden')
            koerper = m.group(1)
        elif p['template'] == 'trail.php':
            # Der redaktionelle Teil kommt aus der REST-API, das Formular
            # wird umgebogen. Kopfbild und Meldungsbereich stecken in
            # layouts/trial.html.
            koerper = trial_formular(p['content']['rendered'])
        else:
            koerper = rumpf(pfad)
        schreiben(seitenziel(pfad, hat_kinder), {
            'title': entity(p['title']['rendered']),
            'seo_title': entity(yoast(p, 'title')),
            'description': entity(yoast(p, 'description')),
            'date': p['date'],
            'lastmod': p['modified'],
            'og_image': ogbild(p),
            'lesezeit': lesezeit(p),
            'handbuch': True if p['template'] == 'manual.php' else None,
            'layout': 'trial' if p['template'] == 'trail.php' else None,
            'weight': p['menu_order'] or None,
            'wp_id': p['id'],
        }, korrigieren(pfad, relativ(koerper)))
        n += 1
    return n


# ---------------------------------------------------------------- Beitraege

def beitraege_schreiben():
    kat = {c['id']: c for c in w.kategorien()}
    autor = {1: 'Christoph Dyllick-Brenzinger', 2: 'Dennis Früh', 3: 'Ralf D.'}
    n = 0
    for b in w.beitraege():
        pfad = w.pfad(b['link'])
        m = BEITRAG.search(rumpf(pfad))
        if not m:
            raise SystemExit(f'Beitrag {pfad}: Textbereich nicht gefunden')
        # Hugos eigene Teaser-Marke. Achtung: Hugo balanciert .Summary
        # nicht - bei fuenf Beitraegen sitzt die Marke mitten im Absatz,
        # das schliessende </p> fehlt dann im Teaser. Der Browser
        # schliesst es am Kartenrand, siehe README.
        koerper = absatz_ergaenzen(MEHR.sub('<!--more-->', m.group(1)))
        kategorien = [kat[c]['slug'] for c in b['categories'] if c in kat]
        schreiben(CONTENT / 'news' / f'{b["slug"]}.html', {
            'title': entity(b['title']['rendered']),
            # Muss stehen: der Permalink /:slug/ nimmt sonst den Titel und
            # macht aus /sharing/ ein /einfach-dateien-austauschen/.
            'slug': b['slug'],
            'seo_title': entity(yoast(b, 'title')),
            'description': entity(yoast(b, 'description')),
            'date': b['date'],
            'lastmod': b['modified'],
            'og_image': ogbild(b),
            'beitragsbild': beitragsbild(b),
            'lesezeit': lesezeit(b),
            'category': kategorien or None,
            'autor': autor.get(b['author']),
            'wp_id': b['id'],
        }, korrigieren(pfad, relativ(koerper)))
        n += 1
    return n


def newsseite_schreiben():
    p = w.newsseite()
    schreiben(CONTENT / 'news' / '_index.html', {
        'title': entity(p['title']['rendered']),
        'seo_title': entity(yoast(p, 'title')),
        'description': entity(yoast(p, 'description')),
        'date': p['date'],
        'lastmod': p['modified'],
        'og_image': ogbild(p),
        'wp_id': p['id'],
    }, '')


def kategorien_schreiben():
    """Beschreibungstexte der drei Kategorien fuer /category/<slug>/."""
    ziel = w.REPO / 'data' / 'kategorien.yaml'
    ziel.parent.mkdir(exist_ok=True)
    zeilen = []
    for c in w.kategorien():
        zeilen.append(f'{c["slug"]}:')
        zeilen.append(f'  name: {yamlwert(entity(c["name"]))}')
        zeilen.append(f'  beschreibung: {yamlwert(entity(c["description"]))}')
    ziel.write_text('\n'.join(zeilen) + '\n', encoding='utf-8')
    return len(w.kategorien())


def main():
    for eintrag in CONTENT.iterdir() if CONTENT.exists() else []:
        if eintrag.name in EIGENE:
            continue
        shutil.rmtree(eintrag) if eintrag.is_dir() else eintrag.unlink()
    CONTENT.mkdir(exist_ok=True)
    s = seiten_schreiben()
    newsseite_schreiben()
    b = beitraege_schreiben()
    k = kategorien_schreiben()
    print(f'{s} Seiten, {b} Beitraege, {k} Kategorien nach {CONTENT} geschrieben')


if __name__ == '__main__':
    sys.exit(main())
