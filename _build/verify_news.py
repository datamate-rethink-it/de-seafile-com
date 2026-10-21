#!/usr/bin/env python3
"""Prueft Beitragsseite, Kategoriearchive, Feeds und Sitemaps.

Das erzeugte XML wird geparst, nicht durchsucht. Bei datamate.org waren
drei Sitemaps drei Stunden lang ungueltig online, weil Hugo ein Partial
auch mit der Endung .xml durch html/template schickt und die
XML-Deklaration dabei zu &lt;?xml ?> maskiert wurde. Die <loc>-Eintraege
sahen vollstaendig aus, der Bau lief gruen - nur geparst hat es niemand.

    hugo --gc && python3 -E -s _build/verify_news.py
"""
import re
import sys
import xml.etree.ElementTree as ET

import wpdata as w

PUBLIC = w.REPO / 'public'
SM = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


def fehler(sammlung, text):
    sammlung.append(text)
    print(f'  FEHLER  {text}')


def main():
    probleme = []

    # --- jede XML-Datei muss wohlgeformt sein ----------------------
    xml_dateien = sorted(PUBLIC.rglob('*.xml'))
    for datei in xml_dateien:
        try:
            ET.parse(datei)
        except ET.ParseError as e:
            fehler(probleme, f'{datei.relative_to(PUBLIC)} ist kein gueltiges XML: {e}')
    print(f'{len(xml_dateien)} XML-Dateien geprueft')

    def locs(datei):
        return [e.text for e in ET.parse(PUBLIC / datei).getroot().iter(f'{SM}loc')]

    # --- Sitemaps gegen die alten ----------------------------------
    alt_seiten = {l.strip() for l in (w.WP / 'urls-pages.txt').read_text().splitlines() if l.strip()}
    alt_posts = {l.strip() for l in (w.WP / 'urls-posts.txt').read_text().splitlines() if l.strip()}
    neu_seiten, neu_posts = set(locs('page-sitemap.xml')), set(locs('post-sitemap.xml'))

    dazu = (neu_seiten - alt_seiten) | (neu_posts - alt_posts)
    if dazu:
        fehler(probleme, f'Adressen in der Sitemap, die es vorher nicht gab: {sorted(dazu)}')
    weg = (alt_seiten - neu_seiten) | (alt_posts - neu_posts)
    unerwartet = {u for u in weg if w.pfad(u) not in w.GESTRICHEN}
    if unerwartet:
        fehler(probleme, f'Adressen aus der Sitemap verschwunden, ohne gestrichen zu sein: {sorted(unerwartet)}')
    print(f'Sitemaps: {len(neu_seiten)} Seiten (vorher {len(alt_seiten)}), '
          f'{len(neu_posts)} Beitraege (vorher {len(alt_posts)}), {len(weg)} gestrichen')

    index = set(locs('sitemap_index.xml'))
    soll_index = {w.BASE + '/post-sitemap.xml', w.BASE + '/page-sitemap.xml'}
    if index != soll_index:
        fehler(probleme, f'sitemap_index.xml nennt {sorted(index)} statt {sorted(soll_index)}')

    # Hugos eigene sitemap.xml darf nicht ausgeliefert werden: /sitemap.xml
    # ist eine 301 auf /sitemap_index.xml. Im Image loescht das Dockerfile
    # sie; oertlich nach "hugo" ist sie da und leer.
    eigene = PUBLIC / 'sitemap.xml'
    if eigene.exists() and locs('sitemap.xml'):
        fehler(probleme, 'public/sitemap.xml ist nicht leer - sie verdeckt die Weiterleitung')

    # --- Beitragsseite und Archive ---------------------------------
    def verweise(datei):
        s = (PUBLIC / datei).read_text(encoding='utf-8')
        return {m.group(1) for m in re.finditer(r'<h4 class="card-title"><a href="([^"]+)"', s)}

    alle = {w.pfad(b['link']) for b in w.beitraege()}
    auf_news = verweise('news/index.html')
    if auf_news != alle:
        fehler(probleme, f'/news/ zeigt {len(auf_news)} Beitraege statt {len(alle)}: '
                         f'fehlt {sorted(alle - auf_news)[:5]}')
    else:
        print(f'/news/: alle {len(alle)} Beitraege verlinkt')

    kat = {c['id']: c for c in w.kategorien()}
    for c in w.kategorien():
        soll = {w.pfad(b['link']) for b in w.beitraege() if c['id'] in b['categories']}
        ist = verweise(f"category/{c['slug']}/index.html")
        if ist != soll:
            fehler(probleme, f"/category/{c['slug']}/: {len(ist)} statt {len(soll)} Beitraege")
        elif len(soll) != c['count']:
            fehler(probleme, f"/category/{c['slug']}/: {len(soll)} Beitraege, "
                             f"WordPress zaehlte {c['count']}")
        else:
            print(f"/category/{c['slug']}/: {len(soll)} Beitraege")

    # --- Feeds -----------------------------------------------------
    for datei, name in [('feed/index.xml', '/feed/')] + [
            (f"category/{c['slug']}/index.xml", f"/category/{c['slug']}/feed/")
            for c in w.kategorien()]:
        baum = ET.parse(PUBLIC / datei).getroot()
        eintraege = baum.findall('./channel/item')
        if not 1 <= len(eintraege) <= 10:
            fehler(probleme, f'{name}: {len(eintraege)} Eintraege (erwartet 1 bis 10)')
        # Die guid muss die WordPress-Kennung bleiben, sonst melden
        # Feedreader alle alten Beitraege als neu.
        for e in eintraege:
            guid = (e.findtext('guid') or '')
            if not re.fullmatch(re.escape(w.BASE) + r'/\?p=\d+', guid):
                fehler(probleme, f'{name}: guid "{guid}" ist nicht die WordPress-Kennung')
                break
    print(f'Feeds: {1 + len(w.kategorien())} geprueft')

    print(f'\n{len(probleme)} Problem(e)')
    return 1 if probleme else 0


if __name__ == '__main__':
    sys.exit(main())
