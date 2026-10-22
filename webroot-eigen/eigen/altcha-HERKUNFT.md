# Herkunft von altcha.min.js

ALTCHA-Widget 3.5.0, MIT-Lizenz (`altcha-LICENSE.txt`).

Bezogen am 22.10.2026 aus der npm-Registry, nicht von einem CDN — das
waere eine Fremdanfrage, und genau die wollten wir loswerden:

    curl https://registry.npmjs.org/altcha/-/altcha-3.5.0.tgz
    # sha1 97b32f1d0f9335d0662d7ed4587ab23ae4af8fbc, stimmt mit der
    # von npm veroeffentlichten Pruefsumme ueberein
    tar xzf altcha-3.5.0.tgz package/dist/main/altcha.min.js

Genommen ist `dist/main/`, nicht `dist/external/`: das Buendel ist in
sich geschlossen, der Rechen-Worker steckt als Blob darin und wird nicht
als zweite Datei nachgeladen.

Die Gegenstelle ist `trial-service` im Repo
<https://github.com/datamate-rethink-it/seafile-trial> — es erzeugt die
Aufgabe unter `/api/trial/challenge` und prueft die Loesung beim
Absenden. Widget und Bibliothek muessen dasselbe Protokoll sprechen:
Widget 3.x und `altcha-lib-go/v2` tun das (Schluesselableitung,
PBKDF2/SHA-256).

Aktualisieren: neue Fassung ziehen, Pruefsumme vergleichen, diese Datei
anpassen — und danach eine echte Anmeldung durchspielen.

## Zweite Datei: altcha-de.js

`dist/i18n/de.js` aus demselben Paket, unveraendert. Sie traegt sich
selbst in `globalThis.$altcha.i18n` ein und muss deshalb **nach**
`altcha.min.js` geladen werden. Ohne sie zeigt das Widget englische
Texte — `language="de"` allein reicht nicht.

## Fallstrick: die Attributnamen haben sich zwischen 2.x und 3.x geaendert

Beim Umbau zuerst falsch gemacht, mit den Namen aus der v2-Doku:

| v2 | v3 |
|---|---|
| `challengeurl="…"` | `challenge="…"` |
| `strings='{…}'` | `language="de"` plus Sprachdatei |
| `hidelogo hidefooter` | `configuration='{"hideLogo":true,"hideFooter":true}'` |

`challengeurl` ist dabei der boesartige: ein unbekanntes Attribut wird
stillschweigend ignoriert, das Widget hat dann gar keine Adresse fuer die
Aufgabe und zeigt nur "Verification failed. Try again later." — ohne
Hinweis darauf, dass die Konfiguration nie angekommen ist.
