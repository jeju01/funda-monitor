# Lammers Beton — Funda Vastgoedmonitor

Wekelijkse automatische monitor voor nieuw vastgoedaanbod boven €2.500.000 op Funda.nl,
voor de provincies Noord-Brabant, Limburg, Zuid-Holland, Utrecht en Gelderland.

> **Let op over BOG (bedrijfsvastgoed):** De pyfunda 3.x library zoekt uitsluitend
> residentiële listings (koop). Commercieel vastgoed (BOG/Funda in Business) maakt gebruik
> van een andere zoekmodus die door de huidige library niet wordt ondersteund.
> De monitor rapporteert dus alleen woningen/appartementen boven €2,5M.

---

## 1. Installatie

Zorg dat Python 3.11 of hoger is geïnstalleerd. Op macOS gebruik je `python3` (niet `python`).
Maak een virtuele omgeving aan en installeer de dependencies:

```bash
cd funda_monitor
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

**Zonder virtuele omgeving** (als je packages al globaal hebt geïnstalleerd):
```bash
pip3 install -r requirements.txt
```

---

## 2. Configuratie (.env bestand)

Kopieer het voorbeeldbestand en vul je eigen gegevens in:

```bash
cp .env.example .env
```

Open `.env` en pas de waarden aan:

```
OUTLOOK_USER=jouw.email@outlook.com
OUTLOOK_PASSWORD=jouw-wachtwoord
RECIPIENT_EMAIL=ontvanger@example.com
```

**Persoonlijk account** (outlook.com / hotmail.com / live.com / live.nl):
gebruik je gewone Outlook-wachtwoord. Werkt direct.

**Zakelijk Microsoft 365-account** (bijv. @lammers.nl):
gebruik je gewone M365-wachtwoord, maar zorg dat **SMTP AUTH** is ingeschakeld:
- Microsoft 365 admin center → Gebruikers → Actieve gebruikers → jouw gebruiker
- Tabblad **Mail** → **E-mail-apps beheren** → vink **Geverifieerde SMTP** aan

Het `.env` bestand staat in `.gitignore` en wordt nooit gecommit.

---

## 3. Handmatige testrun

Voer een directe run uit (fetcht alles, vergelijkt met snapshot, stuurt e-mail):

```bash
python3 main.py --now
```

De eerste keer is er nog geen `snapshot.json` — alle gevonden objecten worden dan als "nieuw" behandeld en opgenomen in het rapport. Bij elke volgende run worden alleen écht nieuwe listings gerapporteerd.

---

## 4. Continu draaien (wekelijkse automatisering)

### macOS / Linux — als achtergrondproces

Start de scheduler (draait elke maandag om 08:00):

```bash
nohup python3 main.py > funda_monitor.log 2>&1 &
```

Controleer het logbestand:
```bash
tail -f funda_monitor.log
```

Stop het proces:
```bash
pkill -f "python3 main.py"
```

### macOS — via launchd (aanbevolen voor permanente achtergrondservice)

Maak een plist aan in `~/Library/LaunchAgents/` om het script bij opstarten automatisch te starten. Zie de Apple-documentatie voor `launchd`.

### Windows — via Taakplanner

1. Open **Taakplanner** → Maak eenvoudige taak
2. Trigger: Wekelijks, maandag, 08:00
3. Actie: Programma starten
   - Programma: `C:\pad\naar\.venv\Scripts\python.exe`
   - Argumenten: `main.py --now`
   - Beginnen in: `C:\pad\naar\funda_monitor\`

Of gebruik de continue scheduler (aanbevolen):
   - Argumenten: `main.py` (zonder `--now`)
   - De scheduler in `main.py` zorgt zelf voor het wekelijkse tijdstip.

---

## Projectstructuur

```
funda_monitor/
├── main.py          # Startpunt, orkestreert de wekelijkse run
├── fetcher.py       # pyfunda integratie: zoekt per regio en type
├── snapshot.py      # Laadt en slaat snapshot.json op
├── diff.py          # Vergelijkt huidig aanbod met vorige snapshot
├── report.py        # Bouwt de HTML e-mail op
├── mailer.py        # Verstuurt de e-mail via Gmail SMTP
├── config.py        # Constanten: regio's, minimumprijs, kleuren
├── .env             # Jouw credentials (NIET committen)
├── .env.example     # Voorbeeldbestand voor .env
├── snapshot.json    # Automatisch aangemaakt na eerste run
└── requirements.txt
```

---

## Logboek

Alle activiteit wordt gelogd naar stdout. Bij een achtergrondproces kun je dit omleiden naar een bestand (zie `nohup` voorbeeld hierboven).
