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
