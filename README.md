# LSV Vereinsapp

Die App (`index.html`) liest `data.json`. Diese Datei erzeugt `fetch_nuliga.py` aus den nuLiga-Seiten (`teams.json`), automatisch alle 3 Stunden über GitHub Actions.

## Einrichtung (einmalig, ca. 10 Minuten)
1. Bei github.com ein kostenloses Konto anlegen und ein neues Repository erstellen (z. B. `lsv-app`).
2. Den gesamten Inhalt dieses Ordners hochladen (auch den versteckten Ordner `.github`).
3. Unter *Settings → Pages* als Quelle „Deploy from a branch“, Branch `main`, Ordner `/ (root)` wählen. Die App ist danach unter `https://<name>.github.io/lsv-app/` erreichbar.
4. Unter *Actions* den Workflow „nuLiga-Daten aktualisieren“ einmal mit „Run workflow“ starten und prüfen, dass `data.json` entsteht.
5. Neue Mannschaft oder neue Saison: Links in `teams.json` ändern.

Hinweis: Das Skript wurde nicht gegen die Live-Seiten getestet. Falls ein Lauf leere Tabellen liefert, die Ausgabe des Workflows (Actions → Lauf öffnen) an Claude schicken.

## Erinnerungen
- **Push:** Das Skript plant über den kostenlosen Dienst ntfy.sh Nachrichten (Vorabend 18 Uhr, 2 Stunden vor Anpfiff). Spieler und Eltern installieren die ntfy-App und abonnieren das Thema ihrer Mannschaft. In der App führt der Button „Push aktivieren“ dorthin.
- **Kalender:** Pro Mannschaft entsteht `kalender/<mannschaft>.ics` mit Erinnerungen. Der Button „Im Kalender abonnieren“ hält sie aktuell.
- Die Themennamen in `teams.json` enthalten eine zufällige Endung. Wer sie kennt, kann dort Nachrichten senden, deshalb nicht öffentlich posten, sondern nur über die App verteilen. Bei Missbrauch die Endung in `teams.json` und in `index.html` (Liste `CFG`) ändern.
- Ändert sich eine Anstoßzeit kurz nach der Planung, kann noch eine alte Erinnerung eintreffen.

## Hallen
Das Skript liest aus dem Spielplan die Hallennummer und ruft pro Halle einmal die nuLiga-Hallenseite ab (Name und Adresse, gespeichert in `data.json` unter `halls`). Die App zeigt die Halle bei jedem Spiel und im Spieltag-Banner mit Route-Button, Kalender und Push-Nachrichten nennen sie ebenfalls. Solange Name und Adresse nicht gelesen werden konnten, steht nur „Halle 648“. In diesem Fall die Ausgabe des Workflows (Zeilen „Halle …“) an Claude schicken, dann wird das Auslesen angepasst.

## Meldungen
Die Startseite zeigt die neuesten Beiträge von lichtenrader-sv.de. Das Skript holt sie über die WordPress-Schnittstelle (`/wp-json`) und nutzt den RSS-Feed als Ersatz. Sie landen in `data.json` unter `news`. Klappt der Abruf nicht, bleiben die zuletzt gespeicherten Meldungen stehen.

## Handy-Installation
Die App ist installierbar (Manifest, Icons, `sw.js`). Auf Android: Browsermenü → „App installieren“ oder „Zum Startbildschirm“. Auf dem iPhone: Safari → Teilen → „Zum Home-Bildschirm“. Das Icon stammt aus dem Logo-Bild. Mit einer hochauflösenden Logo-Datei (PNG ab 512 Pixel) wird es schärfer: einfach `icon-192.png`, `icon-512.png`, `icon-maskable-512.png` und `apple-touch-icon.png` ersetzen.

## Schrift
Überschriften: Anton (Slogan, Spieltag-Banner) und Antonio Bold (übrige Überschriften), Text: Systemschrift des Geräts (auf Apple-Geräten SF Pro). Die Schriftdateien liegen im Ordner `fonts/` und werden von der App selbst ausgeliefert, es gibt keine Verbindung zu Google. Benötigte Dateien: `Anton-Regular.ttf`, `Antonio-Regular.ttf`, `Antonio-Bold.ttf` (Download über fonts.google.com, Lizenz: Open Font License). Fehlen sie, nutzt die App eine Ersatzschrift.

## Teams-Seite
Die Seite „Teams“ gruppiert die Mannschaften (Männer, Frauen, männliche und weibliche Jugend) und zeigt Liga, Tabellenplatz und nächstes Spiel aus den nuLiga-Daten. Optional lassen sich pro Mannschaft Trainingszeit und Trainer anzeigen: in `teams.json` bei der Mannschaft ein Feld `"info"` ergänzen, zum Beispiel
`{"name": "1. Männer", "url": "...", "slug": "...", "topic": "...", "info": {"training": "Di und Do, 20:00 bis 21:30 Uhr", "trainer": "Name"}}`
Beim nächsten Workflow-Lauf erscheint es in der App.

## Ergebnis-Push, Heimspiel-Extras, Fotos
- **Ergebnis-Push:** Sobald nuLiga das Ergebnis eines Spiels zeigt, geht eine Nachricht an das Thema der Mannschaft („Endstand, Sieg: …“). Der Workflow läuft dafür alle 30 Minuten. Es werden nur Spiele von gestern und heute gemeldet, jedes Spiel nur einmal.
- **Heimspiel-Extras:** Im Spieltag-Banner bei Heimspielen. Die Liste steht in `index.html` in der Variable `HOME_EXTRAS` und lässt sich dort anpassen.
- **Bilder bei Meldungen:** Das Titelbild eines Beitrags auf lichtenrader-sv.de wird automatisch angezeigt. Es wird direkt von der Vereinsseite geladen.
- **Teamfotos:** Fotos als `.jpg` (am besten unter 300 KB, Querformat 16:9) in den Ordner `fotos/` legen und in `teams.json` bei der Mannschaft unter `"info"` eintragen: `"foto": "fotos/1-maenner.jpg"`. Vorher die Einwilligung der Abgebildeten bzw. Eltern einholen.

## Probetraining und Beachhandball

- `#probetraining`: Formular, das eine fertige E-Mail an info@lichtenrader-sv.de im Mailprogramm öffnet (nichts wird über die App gespeichert oder gesendet). Altersgruppen stehen in `AGES` in der index.html.
- `#beach`: Beachhandball-Seite. Termine pflegst du in `BEACH.termine` in der index.html, z. B. `{d:"12.07.2027",t:"Turnier in Berlin",o:"Ort"}`. Das Foto steht in `BEACH.foto`.
