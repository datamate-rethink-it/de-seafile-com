# de.seafile.com — Bestandsaufnahme vor dem Umzug nach Hugo

Stand: 21.10.2026. Grundlage: `de-seafile-com.tar.gz` (entpackt unter
`_build/wporig/`, 503 MB) und die laufende Seite.

## Was da ist

| | |
|---|---|
| WordPress | 6.8.11, nginx (kein `.htaccess` → Routing steckt im vhost auf dem Server) |
| Server | 159.69.197.36 (eigener Host, nicht der von ionas.com/datamate.org) |
| Theme | `seafileger`, eigenentwickelt, Bootstrap 4 + jQuery |
| Plugins | Redirection, Yoast SEO, WP Statistics, Cookie Notice, AIOS, BackWPup, Classic Editor, Simple Lightbox, HTML Editor Syntax Highlighter |
| Seiten | 71 (davon 47 mit `manual.php`, 1 mit `trail.php`, 1 = `/news/` als Beitragsseite) |
| Beiträge | 45 in 3 Kategorien: funktionen (19), anleitungen (16), release-notes (10) |
| Tags | 100+, aber `/tag/<slug>/` leitet per 301 auf `/` → **keine Tag-Seiten nötig** |
| Kommentare | 0 |
| Medien | 609 Einträge; 2199 Dateien in `uploads/20*/` |

Neuester Beitrag: 30.08.2022 (Seafile Server 9.0). Die Seite ist inhaltlich
seit vier Jahren stehen geblieben.

### Gute Nachricht gegenüber datamate.org

Die REST-API liefert hier `content` **und** gültiges JSON — der Theme-/Plugin-Ausgabefehler
von datamate.org tritt nicht auf. Dazu kommt `yoast_head_json` (Title, Description,
Canonical, OG) frei Haus. Inhalt und Metadaten liegen vollständig in
`_build/wp/pages-full.json` und `_build/wp/posts-full.json`.

Außerdem: `remove_filter('the_content','wpautop')` im Theme — der Seiteninhalt ist
handgeschriebenes HTML, kein Editor-Markup. Das überträgt sich sauber nach Hugo.

### Referenz-Schnappschuss

`_build/reference/` — 159 Adressen gerendert, `_build/reference-index.json`,
Statuscodes ohne Weiterleitungsverfolgung in `_build/status-live.json`.

## Weiterleitungen — wieder vier Quellen, nicht eine

1. **Plugin *Redirection*:** 19 Regeln, alle live geprüft (301, Ziele existieren).
2. **Nackte Slugs → Hierarchiepfad** (WordPress-Canonical): `/anleitung/`,
   `/seahub/`, `/bibliotheken/`, `/rollen/`, `/2fa-aktivieren/`, `/benutzer/`,
   `/nutzungsbedingungen/` … Jede Seite mit eindeutigem Slug ist so erreichbar.
   Betrifft vor allem den 47-seitigen Anleitungsbaum.
3. **`/news/<beitrag>/` → `/<beitrag>/`** (Prefix der Beitragsseite).
4. **Yoast-Anhangseiten** `/<beitrag>/<bild>/` → Bilddatei, in Original- *und*
   Kleinschreibung (`/seafile-server-9-0/Seafile-9.0_Feature/` und
   `…/seafile-9-0_feature/`).

Dazu `redirect_guess_404_permalink` (`/get-seafil/` → `/get-seafile/`) — nicht
nachbaubar, nur einzeln. Und `/sitemap.xml` → `/sitemap_index.xml`,
`/favicon.ico` → 302 auf ein Upload-PNG.

**Noch zu beschaffen:** der nginx-vhost vom Server. Bei ionas.com stand eine
Regel (`/agb` → PDF) nur dort und in keiner Quelle im Baum.

## Die Startseite ist widersprüchlich

Sitemap sagt `https://de.seafile.com/`, Yoast-Canonical sagt
`https://de.seafile.com` ohne Schrägstrich. Derselbe Fehler wie bei
datamate.org. Beim Umzug auf `/` festlegen.

## Kann weg

| Adresse | Grund |
|---|---|
| `/now/` | Entwurf einer alternativen Startseite von 2019, kein eingehender Link |
| `/featurelog/` | Featurelog bis Version 7.0.5 (2019), seit sieben Jahren nicht gepflegt |
| `/plugin-integration/` | Entwurf von 2022, enthält sieben `dummyimage.com`-Platzhalter, bewirbt u. a. SeaMate (bei datamate.org eingestellt) |
| `/instructions-for-translations/` | interner Stilleitfaden für Übersetzungen, kein eingehender Link — gehört in ein Repo, nicht auf die Website |
| `/support/administratoren/documentation-seafile-app-ucs/` | englisches Duplikat der UCS-Doku, kein eingehender Link, Stand 2019 |
| `/support/benutzer/anleitung/seafile-drive-client-1-0/` + 2 Unterseiten | SeaDrive 1.0, durch 2.0 ersetzt; die Seite sagt das selbst im ersten Satz |

Offene Frage: `/support/administratoren/dokumentation-seafile-app-ucs/` (deutsch,
Stand 2022) — wird die Seafile-App für UCS noch angeboten?

**Beiträge bleiben alle.** Blog = Archiv, wie bei datamate.org entschieden.

## Inhaltlich veraltet (eigene Baustelle, nicht Teil des Umzugs)

- `/downloads/` verweist auf Client 9.0.18 / SeaDrive 3.0.21 / Server 12.0.14.
- Alle `release-notes`-Beiträge enden bei Server 9.0.
- Der Footer verlinkt „Seafile Drive Client 1.0".

## Medien

| | Anzahl | Platz |
|---|---|---|
| referenziert | 618 | 90 MB |
| freie Thumbnails (`-WxH`) | 1363 | 68 MB |
| freie Originale | 218 | 63 MB |

Unter den freien Originalen: 40 SVG-Icons, drei PDFs
(`Seafile_Preisliste_Stand_November2018.pdf`,
`Seafile_Lizenzvertrag_Stand_November2018.pdf`,
`Seafile-Keeper-Max-Planck-Gesellschaft.pdf`) und zwei alte
Outlook-Add-In-ZIPs (0.9 / 0.9.0.1; 1.2.2 ist referenziert).

**Fallstrick beim Aussortieren:** Viele Dateinamen enthalten Umlaute
(`SeaDrive2.0_Kontextmenü_….png`). Mein erster Suchlauf hat elf solcher Pfade
fälschlich als „fehlt" gemeldet — die Dateien sind alle da. Der echte Generator
muss Prozent-Kodierung und NFC/NFD sauber behandeln, sonst wirft er
referenzierte Bilder weg.

## Keine Malware

Die sechs PHP-Dateien in `uploads/` sind Plugin-Hausmeisterei (BackWPup-404-Stubs,
AIOS-Settings). Die 30 HTML-Dateien sind BackWPup-Logs.

## Secrets im Archiv — und auf dem laufenden Server

Das Archiv enthält Zugangsdaten im Klartext. `_build/wporig/` gehört in
`.gitignore` und darf nie in ein Repo.

| Ort | Was |
|---|---|
| `wp-config.php` | Brevo-API-Key (`BREVO_API_KEY_SEAFILE_TRIAL`), DB-Name/-Benutzer |
| `template-parts/content-trail-page.php` | **MySQL-root-Passwort** für 128.140.107.100 (Datenbanken `datamate` und `ccnet_db`), Seafile-Admin-Zugang `seafile@datamate.org`, reCAPTCHA-Secret |

Das MySQL-root-Passwort steht in einer PHP-Datei im Webroot. Solange PHP läuft,
wird sie ausgeführt statt ausgeliefert — fällt PHP aus oder greift eine
Fehlkonfiguration, liegt es offen. Port 3306 auf 128.140.107.100 ist von außen
zu, das ist die einzige Schranke.

Dazu, unabhängig vom Umzug: `content-trail-page.php` setzt `$email` ungefiltert
in ein `INSERT` ein. Das E-Mail-Regex ist am Ende nicht verankert
(`/^…(\.[a-zA-Z0-9_-]+)+/` ohne `$`), ein Wert wie `a@b.de' …` passt also durch
die Prüfung und landet roh im SQL. Die Trial-Passwörter liegen im Klartext in
`trials` und gehen zusätzlich als Brevo-Kontaktattribut `PASSWORT` raus.

Beim Abschalten des WordPress sind diese Zugangsdaten zu wechseln — der
Brevo-Key, das MySQL-root-Passwort und der Seafile-Admin-Zugang.

## Das Trial-Formular

`/trial/` ist die eine Seite, die nicht statisch werden kann. Sie legt bei
Absenden in Echtzeit einen Mandanten an. Das Testsystem läuft
(`trial.seafile-demo.de` = 128.140.107.100, antwortet).

Ablauf heute, alles in `content-trail-page.php`:

1. POST auf die eigene Adresse, Felder `email`, `org`, `terms`, Honeypot `surname`.
2. Google reCAPTCHA v2 serverseitig prüfen.
3. Doppelprüfung: E-Mail und Firmenname gegen Tabelle `trials` (DB `datamate`)
   und gegen `EmailUser` (DB `ccnet_db`) — per direktem MySQL-Zugriff über das
   Internet, als root.
4. Seafile-Admin-API: `addOrganization($org, $email, $pw)`, dann
   `updateOrganizationInfo` auf 7 Benutzer / 777 MB.
5. Zeile in `trials` schreiben (inkl. Passwort im Klartext).
6. Brevo: Kontakt in Liste 4 anlegen (Attribute u. a. `PASSWORT`) und Event
   `trial_signup` auslösen, das die Automation mit der Zugangsmail anstößt.
7. Zugangsdaten sofort auf der Seite anzeigen.

Was nirgends im Code steht: **wer die 7 Tage später wieder aufräumt.** Es gibt
keine Lösch-Logik im Formular. Das macht offenbar etwas anderes (Cronjob auf dem
Trial-Server?) — muss geklärt werden, sonst fehlt nach dem Umzug ein Stück, von
dem niemand weiß, dass es fehlte.

---

# Entscheidungen

## Trial (21.10.2026)

Die Anmeldung wandert auf den Trial-Server, die Website bleibt reines HTML.

- **Endpunkt:** Code auf `trial.seafile-demo.de` (128.140.107.100). Seafile-Admin-API
  und Datenbank laufen dort lokal; auf de.seafile.com bleibt **kein Secret** zurück.
- **Weg:** Caddy im Image nimmt `/api/trial` an und proxyt auf den Trial-Server.
  Gleiche Herkunft im Browser (kein CORS), Regel im Image statt im vhost.
- **n8n legt nicht an.** n8n läuft auf `n8n.seatable.com`, also einer dritten
  Maschine; der Anmeldepfad würde sonst über drei Hosts laufen.
- **Aufräumen bleibt bei n8n**, unverändert: alle 12 Stunden `GET` der
  Organisationen über die Admin-API, `ctime + 8 Tage`, löschen was drüber ist.
  Die Tabelle `trials` kommt darin **nicht** vor.
- **Wiederanmelde-Sperre bleibt.** `trials` ist das einzige bleibende Gedächtnis
  dafür, dass eine E-Mail/Firma schon einmal getestet hat — der Aufräumer löscht
  die Organisation, die API kennt sie danach nicht mehr. Tabelle bleibt, aber
  lokal über `localhost` und mit eigenem Benutzer statt root über das Internet.

### Offene Punkte dazu

- Sieben oder acht Tage? Seite und Nutzungsbedingungen sagen sieben, der
  n8n-Flow löscht nach acht.
- Der Flow löscht **alle** Organisationen des Servers, nicht nur Trials. Gehört
  in die Beschreibung des Flows.
- Klartextpasswort (Bildschirm, `trials`, Brevo-Attribut `PASSWORT`) durch
  Setz-Link ersetzen — noch zu entscheiden.
- reCAPTCHA v2 ersetzen (lädt heute Google unbedingt, vor jeder Zustimmung).
- Secrets wechseln, wenn WordPress abgeschaltet wird: Brevo-Key,
  MySQL-root-Passwort, Seafile-Admin-Zugang, reCAPTCHA-Secret.

## Löschkandidaten (21.10.2026)

Entschieden:

| Adresse | Antwort danach |
|---|---|
| `/now/` | 301 → `/` |
| `/instructions-for-translations/` | 410; Text als `docs/uebersetzungen.md` ins Repo |
| `/plugin-integration/` | 410; den einen Link aus `…/seafile-outlook-addin/` entfernen |
| `/featurelog/` | 301 → `https://manual.seafile.com/latest/changelog/server-changelog/` |
| `/support/administratoren/documentation-seafile-app-ucs/` | 410 |
| `/support/administratoren/dokumentation-seafile-app-ucs/` | 410; Link aus `/support/administratoren/` entfernen |
| `/support/benutzer/anleitung/seafile-drive-client-1-0/` | 301 → `…/seafile-drive-client/` |
| `…/seafile-drive-client-1-0/client-einstellungen-verwalten/` | 301 → `…/seafile-drive-client/client-einstellungen-verwalten/` |
| `…/seafile-drive-client-1-0/seadrive-mit-server-verbinden/` | 301 → `…/seafile-drive-client/seadrive-mit-server-verbinden/` |

Dazu: „Seafile Drive Client 1.0" aus dem Footer streichen.

**Achtung beim Zählen eingehender Links.** Footer und Anleitungs-Seitenmenü
stehen auf jeder Seite; die Schnappschüsse der Weiterleitungs-Quellen enthalten
das HTML ihres *Ziels*. Beides muss raus, sonst sieht eine Seite mit null
redaktionellen Verweisen nach 137 Quellen aus. Der SeaDrive-1.0-Zweig war genau
dieser Fall.

Der Link `https://manual.seafile.com/changelog.html`, auf den die
Featurelog-Seite für das vollständige Changelog verweist, ist bereits tot.

## Suche und Kleinkram (21.10.2026)

- **Pagefind** — statischer Index beim Hugo-Lauf, Suchfeld zusätzlich in die
  Anleitungs-Seitenleiste (dort gab es bisher keins). Alte `/?s=begriff`-Adressen
  fängt JavaScript auf der Startseite ab.
- **Datumsarchive** `/2018/`…`/2022/` → 301 auf `/news/`.
- **Feeds** bleiben: `/feed/` und die drei Kategorie-Feeds.
- **Bleiben trotz fehlender Verweise:** `Seafile_Preisliste_Stand_November2018.pdf`,
  `Seafile_Lizenzvertrag_Stand_November2018.pdf`, Outlook-Add-In 0.9 und 0.9.0.1.

## Auslieferung (21.10.2026)

- Repo `datamate-rethink-it/de-seafile-com`, öffentlich.
- Bleibt auf 159.69.197.36, GHCR-Image auf `127.0.0.1:8083` hinter dem dortigen nginx.
- **Die nginx-Konfiguration enthält keine Ausliefer-Regeln** — `location /` ist nur
  der WordPress-Front-Controller. Alle Weiterleitungen kommen aus WordPress und dem
  Plugin. Die vhosts für `seafile.de`/`www.seafile.de` macht Christoph selbst.
- Nebenbefund, unabhängig vom Umzug: der Client-Zertifikat-Riegel im vhost schützt
  `location = /wissen/wp-login.php` — den Pfad von ionas.com, den es hier nicht gibt.
  `/wp-login.php` antwortet mit 200 und ist ohne Zertifikat erreichbar.
