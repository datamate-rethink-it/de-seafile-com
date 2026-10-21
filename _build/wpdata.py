#!/usr/bin/env python3
"""Gemeinsame Grundlage aller Migrationsskripte.

Hier steht an einer Stelle, welche Adressen der alten WordPress-Installation
bleiben, welche entfallen und welche weiterleiten. gen_content.py,
gen_static.py und gen_redirects.py lesen alle von hier - sonst laufen
Inhalt, Dateibestand und Weiterleitungen auseinander.

Die Rohdaten in wp/ stammen aus der REST-API der laufenden Seite und werden
nicht neu erzeugt; reference/ ist der Schnappschuss, gegen den geprueft wird.
"""
import json
import pathlib
import re
from urllib.parse import quote

BASE = 'https://de.seafile.com'
B = pathlib.Path(__file__).resolve().parent
WP = B / 'wp'
REFERENCE = B / 'reference'
REPO = B.parent

# --------------------------------------------------------------- Rohdaten


def laden(name):
    return json.loads((WP / name).read_text(encoding='utf-8'))


def pfad(link):
    """https://de.seafile.com/foo/ -> /foo/"""
    return link.replace(BASE, '') or '/'


# --------------------------------------------------------- was entfaellt
#
# Entschieden am 21.10.2026, Begruendung in BESTANDSAUFNAHME.md.

# 410 Gone: ersatzlos gestrichen, kein Nachfolger.
ENTFALLEN = {
    # Interner Stilleitfaden fuer Uebersetzungen, nie verlinkt gewesen.
    # Der Text liegt jetzt in docs/uebersetzungen.md.
    '/instructions-for-translations/',
    # Entwurf mit sieben dummyimage.com-Platzhaltern.
    '/plugin-integration/',
    # Seafile-App fuer UCS wird nicht mehr angeboten.
    '/support/administratoren/documentation-seafile-app-ucs/',
    '/support/administratoren/dokumentation-seafile-app-ucs/',
}

# 301: gestrichen, aber es gibt einen Nachfolger.
ERSETZT = {
    # Entwurf einer zweiten Startseite von 2019.
    '/now/': '/',
    # Featurelog endet bei Version 7.0.5 (2019), Seafile ist bei 13. Die
    # Seite selbst verweist fuers vollstaendige Changelog aufs Manual -
    # allerdings auf manual.seafile.com/changelog.html, was schon tot ist.
    '/featurelog/': 'https://manual.seafile.com/latest/changelog/server-changelog/',
    # SeaDrive 1.0, durch 2.0 abgeloest. Die Seiten sagen das selbst im
    # ersten Satz. Alle drei Ziele existieren.
    '/support/benutzer/anleitung/seafile-drive-client-1-0/':
        '/support/benutzer/anleitung/seafile-drive-client/',
    '/support/benutzer/anleitung/seafile-drive-client-1-0/client-einstellungen-verwalten/':
        '/support/benutzer/anleitung/seafile-drive-client/client-einstellungen-verwalten/',
    '/support/benutzer/anleitung/seafile-drive-client-1-0/seadrive-mit-server-verbinden/':
        '/support/benutzer/anleitung/seafile-drive-client/seadrive-mit-server-verbinden/',
}

GESTRICHEN = ENTFALLEN | set(ERSETZT)

# Die 19 Regeln des Plugins Redirection, aus dem Export vom 21.10.2026.
# Alle am selben Tag gegen die laufende Seite geprueft.
PLUGIN_WEITERLEITUNGEN = {
    '/dateien-mit-dem-seafile-client-synchronisieren/':
        '/support/benutzer/anleitung/seafile-sync-client/',
    '/en/': 'https://www.seafile.com/en/home/',
    '/en/about-the-future-of-seafile/': '/support/administratoren/roadmap/',
    '/en/important-infos-about-app-seafile-de-and-licensing-purchases-through-our-web-shops/':
        'https://www.seafile.com/en/home/',
    '/en/seafile-now-accepts-bitcoin-via-bitpay/': 'https://www.seafile.com/en/home/',
    '/en/some-background-information-about-our-conflict-with-paypal/':
        'https://www.seafile.com/en/home/',
    '/fr/produits/hebergement-de-serveur-seafile/': 'https://fr.seafile.com/',
    '/seafile-akzeptiert-jetzt-bitcoin-zahlungen-ueber-bitpay/': '/get-seafile/',
    '/seafile-community-edition-server-5-1-2/': '/downloads/',
    '/seafile-desktop-client-5-1-1/': '/downloads/',
    '/seafile-professional-5-1/': '/downloads/',
    '/seafile-professional-5-1-3-ist-veroeffentlicht/': '/downloads/',
    '/seafile-professional-5-1-7/': '/downloads/',
    '/ueber-uns/geschichte/': '/',
    '/versionsvergleich/': '/seafile-editionen/',
    '/versionsvergleich/professional-features/': '/seafile-editionen/',
    '/wichtige-informationen-zu-app-seafile-de-und-zu-lizenzkaeufen/':
        '/support/administratoren/verwaltung-lizenzdatei-seafile/',
    '/wp-content/uploads/2016/03/seafile-unlock.jpg': '/',
    '/zur-zukunft-von-seafile/': '/support/administratoren/roadmap/',
}


# ------------------------------------------------------------- Inhalte

def seiten():
    """Alle Seiten, die bleiben - ohne /news/ (das ist die Beitragsseite)."""
    aus = []
    for p in laden('pages-full.json'):
        pf = pfad(p['link'])
        if pf in GESTRICHEN or pf == '/news/':
            continue
        aus.append(p)
    return aus


def newsseite():
    """Die Seite /news/ - im WordPress die Beitragsseite, hat keinen Inhalt."""
    for p in laden('pages-full.json'):
        if pfad(p['link']) == '/news/':
            return p
    raise SystemExit('Seite /news/ fehlt in pages-full.json')


def beitraege():
    return laden('posts-full.json')


def kategorien():
    return [c for c in laden('categories.json') if c['count']]


# ------------------------------------------- Weiterleitungen, die WordPress
#                                              selbst gemacht hat
#
# Nichts davon steht irgendwo geschrieben; alle vier Arten sind am
# 21.10.2026 an der laufenden Seite nachgemessen worden.

def pfadsuffixe():
    """/seahub/ und /seafile-sync-client/client-einstellungen-verwalten/
    -> /support/benutzer/anleitung/seahub/ und den vollen Pfad.

    WordPress findet eine Seite nicht nur ueber ihren Slug, sondern ueber
    jedes Endstueck ihres Pfades, und leitet dann per 301 auf die
    vollstaendige Adresse. Beides steht in den eigenen Texten:
    /seahub/ kommt aus der Anleitung, /seafile-sync-client/
    client-einstellungen-verwalten/ aus einer Querverweisung - und ohne
    die Endstuecke ginge der zweite Verweis ins Leere, weil der Slug
    `client-einstellungen-verwalten` zweimal vergeben ist (Sync- und
    Drive-Client) und als nacktes Stueck darum nicht eindeutig waere.

    Nur eindeutige Endstuecke: wo zwei Seiten dasselbe Endstueck haben,
    hat WordPress auch nicht geraten.
    """
    nach_suffix = {}
    for p in seiten():
        teile = pfad(p['link']).strip('/').split('/')
        for i in range(1, len(teile)):          # echte Endstuecke, ohne das Ganze
            nach_suffix.setdefault('/' + '/'.join(teile[i:]) + '/', set()).add(pfad(p['link']))
    # Belegte Adressen gewinnen immer: /funktionen/ ist ein Endstueck,
    # aber es gibt keine eigene Seite dort - /downloads/ dagegen schon.
    belegt = {pfad(p['link']) for p in seiten()} | {pfad(p['link']) for p in beitraege()}
    aus = {}
    for quelle, ziele in nach_suffix.items():
        if len(ziele) != 1 or quelle in belegt or quelle in GESTRICHEN:
            continue
        aus[quelle] = next(iter(ziele))
    return aus


def altlasten():
    """Adressen, die nur WordPress kannte - alte Slugs und Rateversuche.

    Beispiele aus den eigenen Texten: /online-collaboration ->
    /online-file-editing/ und /zentrale-benutzerverwaltung-ad-ldap-
    integration/ -> /ad-ldap/. Das sind frueher vergebene Slugs, die
    WordPress in postmeta unter _wp_old_slug mitfuehrt; die REST-API
    nennt sie nicht. Dazu kommt redirect_guess_404_permalink, das aus
    Teilen raet (/wiki -> /wikis/, /download -> /downloads/).

    Nachbauen laesst sich das nicht, einsammeln schon: _build/
    gen_altlasten.py fragt jede Adresse, die in den eigenen Texten steht
    und ins Leere zeigt, einmal bei der laufenden Seite ab und schreibt
    die Antwort nach altlasten.json. Von da an braucht es die alte Seite
    nicht mehr.
    """
    datei = WP / 'altlasten.json'
    if not datei.exists():
        return {}
    aus = {}
    for quelle, ziel in json.loads(datei.read_text(encoding='utf-8')).items():
        if ziel and ziel not in GESTRICHEN:
            aus[quelle] = ziel
    return aus


def news_praefix():
    """/news/<beitrag>/ -> /<beitrag>/

    /news/ ist im WordPress die Beitragsseite; ihr Pfad laesst sich jedem
    Beitrag voranstellen, WordPress leitet dann auf die kanonische Adresse.
    """
    return {f'/news{pfad(b["link"])}': pfad(b['link']) for b in beitraege()}


def anhangseiten():
    """/<beitrag>/<bild>/ -> /wp-content/uploads/...

    Yoast gibt den WordPress-Anhangseiten eine 301 auf die Bilddatei.
    Raten muss man dafuer nichts: die Medien-REST-API nennt in `link` die
    Adresse der Anhangseite und in `source_url` die der Datei. 605 Stueck,
    davon 96 ohne Elternseite - die liegen direkt unter /<slug>/.

    Achtung: der Elternpfad folgt dem *Slug* der Seite, nicht ihrer
    Adresse. Die Startseite hat den Slug `startseite`, ihre Anhangseiten
    liegen deshalb unter /startseite/<bild>/ und nicht unter /<bild>/.

    Und: `source_url` kommt unkodiert, der Server leitet aber auf die
    prozentkodierte Form (`Konto%C3%84ndern.png`). Ohne quote() weicht
    jede Regel mit Umlaut im Dateinamen vom bisherigen Verhalten ab.
    """
    aus = {}
    for m in laden('media.json'):
        quelle, ziel = pfad(m['link']), m['source_url'].replace(BASE, '')
        if not ziel.startswith('/wp-content/uploads/'):
            continue
        aus[quote(quelle)] = quote(ziel)
    return aus


def datumsarchive():
    """/2018/ ... /2022/ -> /news/

    Datumsarchive antworten heute mit 200, stehen aber in keiner Sitemap.
    """
    jahre = sorted({b['date'][:4] for b in beitraege()})
    return {f'/{j}/': '/news/' for j in jahre}


def alle_weiterleitungen():
    """Alle 301 an einer Stelle, nach Vorrang zusammengefuehrt.

    Reihenfolge ist Absicht: was das Plugin ausdruecklich sagt, schlaegt
    das, was WordPress von sich aus getan haette.
    """
    aus = {}
    for quelle in (anhangseiten(), news_praefix(), pfadsuffixe(), altlasten(),
                   datumsarchive(), ERSETZT, PLUGIN_WEITERLEITUNGEN):
        aus.update(quelle)
    aus['/sitemap.xml'] = '/sitemap_index.xml'
    # Keine Regel darf auf etwas zeigen, das es nicht mehr gibt.
    for q, z in list(aus.items()):
        if z in GESTRICHEN:
            raise SystemExit(f'Weiterleitung {q} zeigt auf gestrichene Seite {z}')
    return dict(sorted(aus.items()))


# ---------------------------------------------------------------- Medien

THUMBNAIL = re.compile(r'-\d+x\d+\.(png|jpe?g|gif|webp)$', re.I)

# Von keiner Seite verlinkt, bleiben trotzdem - ausdrueckliche Entscheidung
# vom 21.10.2026.
BEHALTEN_OHNE_VERWEIS = {
    '2018/11/Seafile_Preisliste_Stand_November2018.pdf',
    '2018/11/Seafile_Lizenzvertrag_Stand_November2018.pdf',
    '2020/03/Seafile-Outlook-Add-In-0.9-by-datamate.zip',
    '2020/03/Seafile-Outlook-Add-In-0.9.0.1-by-datamate.zip',
}
