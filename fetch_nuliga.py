#!/usr/bin/env python3
"""Liest Tabellen und Spielplaene der LSV-Mannschaften aus nuLiga und schreibt data.json.
Nur Python-Standardbibliothek. Aufruf: python fetch_nuliga.py"""
import json, os, re, sys, time, datetime, hashlib, urllib.request
from urllib.parse import urljoin
import html as htmllib
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

UA = "LSV-Vereinsapp/1.0 (+https://lichtenrader-sv.de)"
LSV = "Lichtenrader SV"
TZ = ZoneInfo("Europe/Berlin")

SITE = "https://lichtenrader-sv.de"

def clean(s):
    s = htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\[?(…|\.\.\.)\]?\s*$", "", re.sub(r"\s+", " ", s).strip()).strip()
    return s if len(s) <= 170 else s[:167].rsplit(" ", 1)[0] + "..."

def fetch_news(limit=5):
    """Holt die neuesten Meldungen von der Vereinsseite: zuerst WordPress-API, sonst RSS-Feed."""
    for path in ("/wp-json/wp/v2/posts", "/wp/wp-json/wp/v2/posts"):
        raw = fetch(f"{SITE}{path}?per_page={limit}&_fields=link,title,excerpt,date")
        try:
            items = [{"t": clean(x["title"]["rendered"]), "p": clean(x["excerpt"]["rendered"]), "u": x["link"], "d": x["date"][:10]} for x in json.loads(raw)]
            if items: return items
        except Exception: pass
    raw = fetch(SITE + "/feed/")
    try:
        items = []
        for it in ET.fromstring(raw).iter("item"):
            d = ""
            try: d = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
            except Exception: pass
            items.append({"t": clean(it.findtext("title")), "p": clean(it.findtext("description")), "u": it.findtext("link"), "d": d})
        return items[:limit]
    except Exception as e:
        print("  Meldungen nicht lesbar:", e, file=sys.stderr)
        return []

class Row(list):
    def __init__(self):
        super().__init__(); self.hrefs = []

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack, self.row, self.cell, self.span, self.href = [], [], None, None, 1, ""
        self.h1, self.in_h1 = "", False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1": self.in_h1 = True
        elif tag == "table": self.stack.append([])
        elif tag == "tr" and self.stack: self.row = Row()
        elif tag in ("td", "th") and self.row is not None:
            self.cell, self.href = [], ""
            try: self.span = max(1, int(a.get("colspan", 1)))
            except ValueError: self.span = 1
        elif tag == "a" and self.cell is not None and not self.href: self.href = a.get("href", "") or ""
        elif tag == "br" and self.cell is not None: self.cell.append(" ")
    def handle_endtag(self, tag):
        if tag == "h1": self.in_h1 = False
        elif tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.row.hrefs.append(self.href)
            self.row.extend([""] * (self.span - 1)); self.row.hrefs.extend([""] * (self.span - 1))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.stack:
            if self.row: self.stack[-1].append(self.row)
            self.row = None
        elif tag == "table" and self.stack: self.tables.append(self.stack.pop())
    def handle_data(self, d):
        if self.cell is not None: self.cell.append(d)
        if self.in_h1: self.h1 += d

def fetch(url):
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as e:
            print("  Fehler:", e, file=sys.stderr); time.sleep(5)
    return None

def parse(html, base=""):
    p = Page(); p.feed(html)
    h1 = re.sub(r"\s+", " ", p.h1).strip()
    core = re.sub(r"\s+Tabelle und Spielplan.*$", "", h1)
    liga = re.split(r"\d{4}/\d{2}\s+", core)[-1].strip() or h1
    table, games, halls = [], [], {}
    for t in p.tables:
        for i, r in enumerate(t):
            low = [c.lower() for c in r]
            if "rang" in low and "mannschaft" in low:
                ix = {k: low.index(k) for k in ("rang", "mannschaft", "begegnungen", "+/-", "punkte") if k in low}
                for row in t[i + 1:]:
                    if len(row) > max(ix.values()) and row[ix["rang"]].isdigit():
                        gt = row[ix["begegnungen"]]
                        pts = row[ix["punkte"]] or ("zurückgezogen" if "zurückgezogen" in gt else "")
                        table.append({"rank": int(row[ix["rang"]]), "team": row[ix["mannschaft"]],
                                      "games": int(gt) if gt.isdigit() else 0, "diff": row[ix["+/-"]], "points": pts})
                break
            if "heimmannschaft" in low and "gastmannschaft" in low:
                h, g = low.index("heimmannschaft"), low.index("gastmannschaft")
                day = date = ""
                for row in t[i + 1:]:
                    if len(row) <= g: continue
                    if re.match(r"\d\d\.\d\d\.\d{4}", row[1]): date = row[1]
                    m2 = re.match(r"(\d\d:\d\d)", row[2])
                    if not date or not m2 or not row[h]: continue
                    d, mo, y = date[:10].split(".")
                    score = next((c for c in row[g + 1:] if re.fullmatch(r"\d+:\d+", c)), "")
                    game = {"date": f"{y}-{mo}-{d}", "time": m2.group(1), "home": row[h], "guest": row[g], "score": "" if score == "0:0" else score}
                    lm = re.search(r"location=(\d+)", row.hrefs[3]) if len(row.hrefs) > 3 else None
                    if row[3] and lm:
                        game["hall"], game["loc"] = row[3], lm.group(1)
                        halls[lm.group(1)] = {"nr": row[3], "url": urljoin(base, row.hrefs[3])}
                    games.append(game)
                break
    return liga, table, games, halls

def parse_hall(html):
    """Liest Hallenname und Adresse aus der nuLiga-Hallenseite (courtInfo). Format nicht getestet, daher grosszuegig."""
    p = Page(); p.feed(html)
    kv = {}
    for t in p.tables:
        for r in t:
            if len(r) >= 2 and r[0] and r[1]:
                kv.setdefault(r[0].lower().rstrip(": "), r[1])
    pick = lambda *keys: next((kv[k] for k in keys if k in kv), "")
    name = pick("name", "bezeichnung", "halle", "hallenname") or re.sub(r"\s+", " ", p.h1).strip()
    name = re.sub(r"\s*\(\d+\)\s*$", "", re.sub(r"\s*Hallenspielplan\s*$", "", name)).strip(" -")
    street = pick("straße", "strasse", "adresse", "anschrift")
    city = pick("plz/ort", "ort") or " ".join(x for x in (pick("plz"), pick("stadt")) if x)
    return {"name": name, "address": ", ".join(x for x in (street, city) if x)}

def resolve_halls(found, cache):
    """Holt pro Halle einmal Name und Adresse (erneuter Versuch fruehestens nach 7 Tagen)."""
    today = datetime.date.today()
    out = {}
    for loc, info in found.items():
        old = cache.get(loc, {})
        entry = {"nr": info["nr"], "name": old.get("name", ""), "address": old.get("address", ""), "tried": old.get("tried", "")}
        stale = not entry["tried"] or (today - datetime.date.fromisoformat(entry["tried"])).days >= 7
        entry["v"] = old.get("v", 0)
        if not entry["name"] or entry["v"] != 2 or (not entry["address"] and stale):
            entry["v"] = 2
            html = fetch(info["url"]); entry["tried"] = today.isoformat()
            if html:
                try: entry.update(parse_hall(html)); print("Halle", info["nr"], "->", entry["name"], "|", entry["address"])
                except Exception as e: print("  Hallenseite nicht lesbar:", e, file=sys.stderr)
            time.sleep(2)
        out[loc] = entry
    return out

def hall_text(g, halls):
    h = halls.get(g.get("loc", ""), {})
    if h.get("name"): return h["name"] + (", " + h["address"] if h.get("address") else "")
    return ("Halle " + g["hall"]) if g.get("hall") else ""

def lsv_games(t):
    return [g for g in t["games"] if LSV in g["home"] or LSV in g["guest"]]

def kickoff(g):
    return datetime.datetime.fromisoformat(f"{g['date']}T{g['time']}:00").replace(tzinfo=TZ)

def ics_esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")

def write_calendars(teams, halls={}):
    """Pro Mannschaft eine Kalenderdatei (abonnierbar) mit Erinnerung 1 Tag und 2 Stunden vorher."""
    os.makedirs("kalender", exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fmt = lambda d: d.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for t in teams:
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//LSV Vereinsapp//DE", "CALSCALE:GREGORIAN",
                 "X-WR-CALNAME:" + ics_esc("LSV " + t["name"]), "X-WR-TIMEZONE:Europe/Berlin"]
        for g in lsv_games(t):
            ko = kickoff(g)
            uid = hashlib.md5((g["home"] + "|" + g["guest"]).encode()).hexdigest()[:12]
            lines += ["BEGIN:VEVENT", f"UID:{t['slug']}-{uid}@lichtenrader-sv.de", "DTSTAMP:" + stamp,
                      "DTSTART:" + fmt(ko), "DTEND:" + fmt(ko + datetime.timedelta(minutes=90)),
                      "SUMMARY:" + ics_esc(f"LSV {t['name']}: {g['home']} - {g['guest']}")]
            if hall_text(g, halls): lines.append("LOCATION:" + ics_esc(hall_text(g, halls)))
            for trig, txt in (("-P1D", "Morgen"), ("-PT2H", "In 2 Stunden")):
                lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:" + trig,
                          "DESCRIPTION:" + ics_esc(f"{txt}: {g['home']} - {g['guest']}"), "END:VALARM"]
            lines.append("END:VEVENT")
        lines.append("END:VCALENDAR")
        with open(f"kalender/{t['slug']}.ics", "w", encoding="utf-8", newline="") as f:
            f.write("\r\n".join(lines) + "\r\n")

def ntfy(topic, title, message, when):
    body = json.dumps({"topic": topic, "title": title, "message": message, "tags": ["handball"],
                       "delay": str(int(when.timestamp()))}).encode()
    req = urllib.request.Request("https://ntfy.sh", data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
    urllib.request.urlopen(req, timeout=30).read()

def send_reminders(teams, halls={}):
    """Plant Push-Nachrichten ueber ntfy.sh: Vorabend 18:00 Uhr und 2 Stunden vor Anpfiff.
    ntfy haelt die Nachricht bis zum Zeitpunkt (max. 3 Tage), deshalb wird nur 70 Stunden vorausgeplant."""
    try: sent = json.load(open("notified.json", encoding="utf-8"))
    except Exception: sent = {}
    now = datetime.datetime.now(TZ)
    for t in teams:
        for g in lsv_games(t):
            if g["score"]: continue
            ko = kickoff(g)
            plan = [("tag", (ko - datetime.timedelta(days=1)).replace(hour=18, minute=0), "Morgen"),
                    ("2h", ko - datetime.timedelta(hours=2), "In 2 Stunden")]
            for kind, when, lead in plan:
                key = "|".join([t["name"], g["date"], g["time"], g["home"], g["guest"], kind])
                if key in sent or not (now + datetime.timedelta(minutes=2) < when <= now + datetime.timedelta(hours=70)):
                    continue
                msg = f"{lead}, {ko.strftime('%d.%m.')} um {g['time']} Uhr: {g['home']} - {g['guest']}" + (f" ({hall_text(g, halls)})" if hall_text(g, halls) else "")
                try:
                    ntfy(t["topic"], "LSV " + t["name"], msg, when)
                    sent[key] = now.isoformat(timespec="seconds"); print("Erinnerung geplant:", key)
                except Exception as e:
                    print("  ntfy-Fehler:", e, file=sys.stderr)
    json.dump(sent, open("notified.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)

def main():
    teams = json.load(open("teams.json", encoding="utf-8"))
    try: old = {t["name"]: t for t in json.load(open("data.json", encoding="utf-8"))["teams"]}
    except Exception: old = {}
    out, found = [], {}
    for i, t in enumerate(teams):
        print("Lese", t["name"])
        html = fetch(t["url"])
        entry = {"name": t["name"], "url": t["url"], "slug": t["slug"], "topic": t["topic"], "liga": "", "table": [], "games": []}
        if html:
            liga, table, games, hs = parse(html, t["url"])
            found.update(hs)
            entry.update(liga=liga, table=table, games=games)
            print("  ", liga, "|", len(table), "Tabellenzeilen,", len(games), "Spiele")
        elif t["name"] in old:
            entry = old[t["name"]]          # alten Stand behalten
        out.append(entry)
        if i < len(teams) - 1: time.sleep(2)
    try: prev = json.load(open("data.json", encoding="utf-8"))
    except Exception: prev = {}
    used = {g["loc"] for t in out for g in t["games"] if g.get("loc") and (LSV in g["home"] or LSV in g["guest"]) and not g["score"]}
    halls = resolve_halls({k: v for k, v in found.items() if k in used}, prev.get("halls", {}))
    if not found: halls = prev.get("halls", {})
    news = fetch_news() or prev.get("news", [])
    print(len(news), "Meldungen")
    if prev.get("teams") == out and prev.get("halls") == halls and prev.get("news") == news:
        print("Keine Aenderungen an den Daten.")
    else:
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        json.dump({"updated": now, "teams": out, "halls": halls, "news": news}, open("data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print("data.json geschrieben.")
    write_calendars(out, halls)
    if os.environ.get("SEND_REMINDERS") == "1":
        send_reminders(out, halls)

if __name__ == "__main__": main()
