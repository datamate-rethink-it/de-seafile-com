# de.seafile.com

Die deutsche Seafile-Website als statische Seite. Gebaut mit Hugo,
ausgeliefert von Caddy in einem Container, davor das native nginx des
Servers.

Vorher lief hier WordPress 6.8.11 mit dem eigenentwickelten Theme
`seafileger` und neun Plugins. Abgeloest am 21.10.2026.

Gebaut nach demselben Muster wie
[ionas-com](https://github.com/datamate-rethink-it/ionas-com) und
[datamate-org](https://github.com/datamate-rethink-it/datamate-org).

---

## Umfang

| | |
|---|---|
| Seiten | 61, davon 47 im Anleitungsbaum unter `/support/benutzer/anleitung/` |
| Beitraege | 45 in drei Kategorien: funktionen (19), anleitungen (16), release-notes (10) |
| Beitragsseite | `/news/`, alle Beitraege auf einer Seite - `/news/page/2/` hat schon im WordPress mit 404 geantwortet |
| Kategoriearchive | `/category/anleitungen/`, `/category/funktionen/`, `/category/release-notes/` |
| Feeds | `/feed/` und je ein Feed pro Kategorie |
| Sitemaps | `/sitemap_index.xml`, `/post-sitemap.xml`, `/page-sitemap.xml` - Adressen und Aufbau wie bei Yoast SEO |
| Suche | `/suche/`, Pagefind; die WordPress-Suche unter `/?s=` wird per JavaScript dorthin umgeleitet |
| Weiterleitungen | 861, dazu vier Adressen mit 410 |
| Medien | 824 Dateien, rund 150 MB |

Der neueste Beitrag ist vom 30.08.2022. Der Blog ist ein Archiv, nicht
mehr gepflegt - Beitraege zu alten Versionen bleiben trotzdem stehen.

## Aufbau

```
content/          Inhalt, reines HTML mit YAML-Frontmatter.
                  Erzeugt von _build/gen_content.py aus den Daten der
                  alten Installation - mit einer Ausnahme: content/suche/
                  ist von Hand geschrieben und bleibt bei einem Neulauf
                  stehen.
layouts/          Vorlagen. Hier steckt das Geruest: Kopfleiste,
                  Fusszeile, Seitenmenue der Anleitungen, Beitragskopf,
                  Feeds, Sitemaps.
data/             Die vier Menues und die Kategoriebeschreibungen. Lagen
                  frueher in der Datenbank.
webroot/          Uebernommener Dateibestand (wp-content/, Theme-CSS und
                  -Skripte, Schriften). ERZEUGT - nichts hineinlegen.
webroot-eigen/    Selbstgeschriebenes: seite.js und zwei gerettete
                  Bilder. Wird nie neu erzeugt.
deploy/           Caddyfile des Containers, die erzeugte
                  Weiterleitungsdatei, docker-compose.yml, nginx-vhost.
docs/             Was von der Website ins Repo gewandert ist.
_build/           Migrations- und Pruefwerkzeug. Nicht Teil des Baus.
```

## Bauen

```bash
hugo --gc
pagefind --site public
```

Oder als Container:

```bash
docker build -t de-seafile-com:dev .
docker run --rm -p 127.0.0.1:8083:80 de-seafile-com:dev
```

Kein `--minify`: das gaebe die Vergleichbarkeit mit dem
Referenz-Schnappschuss auf, die `_build/verify.py` nachweist.

## Ausliefern

Image `ghcr.io/datamate-rethink-it/de-seafile-com:<datum>`, auf
`127.0.0.1:8083`, davor das native nginx von 159.69.197.36.

```bash
git tag 2026-10-21 && git push --tags
# dann auf dem Server:
cd /opt/de.seafile.com
sed -i 's/^SEAFILE_DE_VERSION=.*/SEAFILE_DE_VERSION=2026-10-21/' .env
docker compose pull && docker compose up -d
```

Zurueck auf eine aeltere Fassung: alten Wert in `.env` eintragen,
dieselben zwei Befehle.

**Die Ausliefer-Regeln stecken im Image, nicht im vhost des Servers.**
861 Weiterleitungen, vier 410, die Feed-Adressen und `try_files` stehen in
`deploy/Caddyfile.container` und `deploy/redirects.caddy`. Das war der
Grund fuer den Container statt eines rsync: so sind die Regeln mit dem
Inhalt zusammen versioniert, und ein Rueckschritt nimmt sie mit.

## Weiterleitungen

`deploy/redirects.caddy` ist erzeugt (`_build/gen_redirects.py`) und
gehoert trotzdem ins Repo: so sieht man im Diff, was sich an den Adressen
aendert. Die Regeln kommen aus sieben Quellen:

| Anzahl | Quelle |
|---|---|
| 19 | Plugin *Redirection* |
| 5 | gestrichene Seiten mit Nachfolger |
| 176 | **Endstuecke von Pfaden** - `/seahub/` und `/seafile-sync-client/client-einstellungen-verwalten/` fuehren zum vollen Pfad |
| 45 | `/news/<beitrag>/` → `/<beitrag>/` |
| 605 | Anhangseiten von Bildern → die Bilddatei (Yoast) |
| 5 | **alte Slugs und Rateversuche** - `/online-collaboration` → `/online-file-editing/` |
| 5 | Datumsarchive `/2018/`…`/2022/` → `/news/` |

Nur die erste Zeile stand irgendwo geschrieben. Alles andere hat
WordPress von sich aus getan, und es faellt erst auf, wenn man es misst.

Die alten Slugs sind der unangenehmste Teil: WordPress fuehrt sie in
`postmeta` unter `_wp_old_slug`, die REST-API nennt sie nicht, und aus
dem Dateibestand sind sie nicht zu gewinnen.
`_build/gen_altlasten.py` loest das anders: es nimmt jede Adresse, die in
den eigenen Texten steht und ins Leere zeigt, legt sie einmal der
laufenden Seite vor und schreibt deren Antwort nach
`_build/wp/altlasten.json`. Danach braucht es die alte Seite nicht mehr.

### Gestrichene Seiten

| Adresse | Antwort |
|---|---|
| `/now/` | 301 → `/` |
| `/featurelog/` | 301 → `manual.seafile.com/latest/changelog/server-changelog/` |
| `/support/benutzer/anleitung/seafile-drive-client-1-0/` + 2 Unterseiten | 301 auf die SeaDrive-2.0-Entsprechung |
| `/instructions-for-translations/` | 410, Text liegt in `docs/uebersetzungen.md` |
| `/plugin-integration/` | 410 |
| `/support/administratoren/dokumentation-seafile-app-ucs/` und die englische Fassung | 410 |

Begruendungen in `BESTANDSAUFNAHME.md`.

## Pruefungen

Vier Skripte. Die ersten drei laufen bei jedem Push
(`.github/workflows/build.yml`), die anderen beiden von Hand.

```bash
hugo --gc && pagefind --site public
python3 -E -s _build/verify.py        # Text, Medien und Verweise gegen den Schnappschuss
python3 -E -s _build/verify_news.py   # Beitragsseite, Kategorien, Feeds, Sitemaps
python3 -E -s _build/linkcheck.py     # seiteninterne Verweise

python3 -E -s _build/linkcheck_extern.py   # fremde Server, braucht Netz
docker build -t de-seafile-com:dev . && \
  docker run -d --name t -p 127.0.0.1:8083:80 de-seafile-com:dev && \
  python3 -E -s _build/verify_status.py    # Statuscodes gegen die laufende Seite
```

`verify.py` vergleicht nicht Markup gegen Markup - das Geruest ist neu
geschrieben -, sondern den sichtbaren Text jedes Blockelements, die
eingebundenen Mediendateien und die Verweisziele. Gemeldet wird nur, was
verschwindet. Damit bleibt die Pruefung auch nach dem Umzug brauchbar,
wenn jemand einen Text aendert.

`verify_status.py` fragt jede der 160 Adressen des Schnappschusses beim
Container und vergleicht mit `_build/status-live.json`. Bei datamate.org
hat genau diese Pruefung zehn Beitraege gefunden, die ein zu weit
gefasstes 410-Muster eingefangen hatte.

## Nicht wegwerfen

- `_build/reference/` - Schnappschuss der alten Seite, 159 Adressen.
  Grundlage von `verify.py`.
- `_build/wp/` - die REST-Daten der alten Installation, dazu
  `altlasten.json` und `status-live.json`.
- `webroot-eigen/` - wird nie neu erzeugt.

## Neu aufsetzen

`_build/gen_content.py` und `_build/gen_static.py` brauchen den
entpackten WordPress-Dateibestand unter `_build/wporig/`. Der liegt nicht
im Repo: 503 MB, und `wp-config.php` enthaelt den Brevo-Schluessel,
`template-parts/content-trail-page.php` das MySQL-root-Passwort des
Trial-Servers.

**Das Quellarchiv `de-seafile-com.tar.gz` ist am 21.10.2026 geloescht
worden.** Es war eine Dublette des entpackten Baums, der nur noch oertlich
auf Christophs Rechner liegt. Geht auch der weg, sind `gen_content.py` und
`gen_static.py` nur noch Dokumentation — gebaut werden kann die Seite
trotzdem jederzeit, `content/` und `webroot/` liegen im Repo.

Verloren ist dabei nichts vom Inhalt: alle 824 Original-Mediendateien
stecken in `webroot/`, es fehlen nur die 1 375 von WordPress erzeugten
Zuschnitte. Was es sonst nirgends mehr gibt, ist der *Produktionsstand*
von `content-trial-page.php` — die Fassung in der Historie von
[seafile-trial](https://github.com/datamate-rethink-it/seafile-trial) ist
von Mai 2024 und hat weder Honigtopf noch reCAPTCHA noch den
Brevo-Event. Abgeloest ist alles drei vom Go-Dienst dort.

```bash
python3 -E -s _build/gen_content.py
python3 -E -s _build/gen_static.py     # braucht einmal Netz fuer die Schriften
python3 -E -s _build/gen_redirects.py
```

`gen_menues.py` und `gen_altlasten.py` laufen nur einmal bei der
Migration; danach werden `data/` und `wp/altlasten.json` von Hand
gepflegt.

## Das Trial

`/trial/` ist die einzige Seite, an der etwas gerechnet wird. Das
Formular legt in Echtzeit einen Seafile-Mandanten an (7 Tage, 7 Benutzer,
777 MB).

Frueher lief das in `template-parts/content-trail-page.php` auf dem
Webserver: direkter MySQL-Zugriff als root ueber das offene Internet auf
die Datenbanken des Trial-Servers, Seafile-Admin-Zugang und Brevo-Key im
Quelltext. Jetzt laeuft der Code **auf dem Trial-Server selbst**
(`trial.seafile-demo.de`), wo Seafile-API und Datenbank oertlich liegen.
Auf diesem Rechner bleibt kein Zugangsdatum zurueck.

Das Formular postet nach `/api/trial`; Caddy im Image reicht das weiter.
Weitergereicht statt direkt angesprochen, damit der Browser bei gleicher
Herkunft bleibt - kein CORS, kein Preflight.

Das Aufraeumen nach Ablauf macht unveraendert ein n8n-Flow auf
`n8n.seatable.com`: alle 12 Stunden die Organisationen ueber die
Admin-API holen, `ctime + 8 Tage`, loeschen was drueber ist.

Der Endpunkt selbst liegt in
[seafile-trial](https://github.com/datamate-rethink-it/seafile-trial) und
laeuft seit dem 21.10.2026 - ein Go-Dienst ohne Datenbank, neben Seafile im
selben Compose-Stack. Die Wiederanmeldesperre liest er aus Brevo.

Hier in diesem Repo steckt davon nur zweierlei: das Formular auf `/trial/`
und die eine `handle`-Regel in `deploy/Caddyfile.container`.

## Was sich geaendert hat

Gegenueber dem WordPress-Stand mit Absicht anders:

- **Schriften werden selbst ausgeliefert.** `template.min.css` und
  `print.min.css` holten Raleway und Roboto Slab per `@import` von
  `fonts.googleapis.com` - also bei jedem Aufruf eine Anfrage an Google,
  auf einer Seite, die mit Kontrolle ueber die eigenen Daten wirbt.
- **Kein Cookie-Banner.** Es gab nichts mehr zu melden: WP Statistics ist
  weg, und das Banner stand ohnehin nur wegen reCAPTCHA auf `/trial/`.
  Das reCAPTCHA selbst ist noch da und laedt Google unbedingt - sein
  Austausch ist offen.
- **Eine Lightbox statt zweier.** Das Theme brachte eine mit, das Plugin
  *Simple Lightbox* eine zweite; beide wurden geladen.
- **Ein jQuery statt zweier.** Das Theme lud ein eigenes, WordPress ein
  weiteres.
- **Keine Gutenberg-Stile.** Im ganzen Text steht kein einziges
  `wp-block-*`; `aligncenter` und Co. stehen in `template.min.css`.
- **Die Startseite hat einen Schraegstrich.** In der Sitemap stand sie
  mit, im Canonical ohne.
- **Suchfeld auch im Anleitungsbaum.** Bisher stand es nur auf `/news/`
  und den Kategoriearchiven - also genau dort, wo man 45 Beitraege auch
  so ueberblickt.
- **Zwei Bilder liegen jetzt hier.** Siehe unten.

## Fallstricke

Was beim Umzug Zeit gekostet hat, in der Hoffnung, dass es das naechste
Mal schneller geht.

- **Die REST-API verschluckt die `<!--more-->`-Marke.** `content.rendered`
  enthaelt sie nicht, nur die gerenderte Einzelseite hat
  `<span id="more-NNN"></span>`. Ohne sie waere der Teaser jedes Beitrags
  auf `/news/` der ganze Artikel. Darum kommt der Text aus
  `_build/reference/` und nicht aus der API.

- **WordPress loest Endstuecke von Pfaden auf, nicht nur Slugs.**
  `/seafile-sync-client/client-einstellungen-verwalten/` fuehrt zum vollen
  Pfad, obwohl der Slug `client-einstellungen-verwalten` zweimal vergeben
  ist. Nur Slugs nachzubauen reicht nicht.

- **`_wp_old_slug` ist unsichtbar.** Alte Slugs stehen in `postmeta` und
  in keiner API. Siehe `gen_altlasten.py`.

- **Die Medien-REST-API nennt Anhangseiten direkt**: `link` ist die
  Adresse der Anhangseite, `source_url` die der Datei. Raten muss man
  nichts. Aber: `source_url` kommt **unkodiert**, der Server leitet auf
  die prozentkodierte Form. Ohne `quote()` weicht jede Regel mit Umlaut im
  Dateinamen ab. Und der Elternpfad folgt dem *Slug* der Seite: die
  Startseite hat den Slug `startseite`, ihre Anhangseiten liegen unter
  `/startseite/<bild>/`.

- **Dateinamen mit Umlauten.** Beim Aussortieren verwaister Dateien muss
  man Prozent-Kodierung und NFC/NFD sauber behandeln. Mein erster Suchlauf
  hat elf vorhandene Bilder als „fehlt" gemeldet.

- **In TOML gehoert jeder einfache Schluessel zur zuletzt geoeffneten
  Tabelle.** `[sitemap]` mitten zwischen den obersten Schluesseln hat
  `removePathAccents` und alles danach stillschweigend verschluckt. Der
  Bau lief gruen.

- **`disableKinds = ['taxonomy']` reicht nicht.** Hugo baut die Seite
  dann nicht als HTML, legt aber weiter ihren RSS-Feed unter
  `/category/index.xml` an. Erst `taxonomy = []` in `[outputs]` macht
  Schluss. Und `[sitemap] disable = true` leert Hugos eigene
  `sitemap.xml`, schreibt sie aber weiter - sie verdeckt sonst die
  Weiterleitung von `/sitemap.xml` und wird im Dockerfile geloescht.

- **Caddy: `error @matcher 410` reicht nicht.** Caddy sortiert die
  Direktiven, und `error` landet dabei hinter den `handle`-Bloecken. Die
  statische Auslieferung greift zuerst, findet nichts und antwortet 404
  statt 410. Als `handle @matcher { error 410 }` steht die Regel dort, wo
  sie geschrieben ist.

- **`isPlainText = true` schaltet Gos HTML-Maskierung ab.** Fuer XML will
  man das, aber dann muss jeder Titel durch `htmlEscape`: „Knowledge
  Management und Sync & Share" hat einen Kategorie-Feed ungueltig
  gemacht. Erzeugtes XML **parsen**, nicht Vorkommen zaehlen - bei
  datamate.org waren drei Sitemaps drei Stunden lang ungueltig online,
  waehrend der Bau gruen durchlief.

- **Hugo balanciert `.Summary` nicht.** Bei fuenf Beitraegen sitzt die
  `<!--more-->`-Marke mitten im Absatz; das `</p>` fehlt dann im Teaser.
  Der Browser schliesst es am Kartenrand - sichtbar ist nichts, aber der
  Quelltext weicht ab.

- **`the_modified_date` zeigt Ortszeit.** `modified_gmt` aus der API ist
  UTC; wer das uebernimmt, schreibt „Zuletzt geaendert" einen Tag zu
  frueh. Die Frontmatter fuehrt jetzt Ortszeit ohne Zonenangabe und
  `timeZone = 'Europe/Berlin'` in `hugo.toml`.

- **Das alte Theme hatte zwei Markup-Fehler, die Inhalt zusammenhielten.**
  `content.php` legte um den Beitragstext ein `<p>`, das nie geschlossen
  wurde - bei drei Beitraegen war das der einzige Absatz, den ihr
  einleitender Text hatte. Und `index.php` schrieb auf `/news/` ein
  zweites `<p>` statt eines `</p>`. Beides ist jetzt repariert, und
  `verify.py` musste lernen, das nicht als Verlust zu melden.

- **Das Kartenbild ist `the_post_thumbnail_url()`, nicht `og:image`.**
  Die beiden koennen auf verschiedene Dateien zeigen.

- **Ein Umzug kann die Nachbarseite zerschiessen.** Der Beitrag zu Server
  6.3 lud zwei Screenshots als Heissverweis von
  `www.datamate.org/wp-content/uploads/2018/06/`. Beim dortigen Umzug
  fielen sie als „verwaist" weg - der Suchlauf dort sah nur Verweise
  *innerhalb* von datamate.org. Gerettet aus dem lokalen Archiv, liegen
  jetzt unter `webroot-eigen/eigen/bilder/`. Dazu antwortet die
  SeaMate-Kachel auf `/support/administratoren/` seither mit 410; sie ist
  entfernt. **Nach jedem Umzug einer verbundenen Seite
  `linkcheck_extern.py` laufen lassen.**

## Noch offen

- Beim Abschalten des WordPress: Brevo-Key, MySQL-root-Passwort des
  Trial-Servers, Seafile-Admin-Zugang und reCAPTCHA-Secret wechseln. Alle
  vier standen im Klartext im WordPress und sind auf den Systemen weiter
  gueltig — geloescht ist nur das Archiv, nicht das Passwort. Beim
  Seafile-Admin mitbedenken, dass `trial-service` denselben Zugang
  benutzt (siehe seafile-trial).
- `/downloads/` nennt Client 9.0.18, SeaDrive 3.0.21 und Server 12.0.14.
  Inhaltspflege, keine Migration.
- Alle `release-notes`-Beitraege enden bei Server 9.0 (2022).
- reCAPTCHA v2 auf `/trial/` laedt Google unbedingt.
- Der Client-Zertifikat-Riegel im alten nginx-vhost schuetzte
  `/wissen/wp-login.php` - den Pfad von ionas.com, den es hier nie gab.
  `/wp-login.php` war damit offen. Erledigt sich mit dem Abschalten.
