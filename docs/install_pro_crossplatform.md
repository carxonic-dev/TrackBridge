# TrackBridge – PRO Installation Guide (Windows, macOS, Linux)

Version 1.2.1
Stand: 29-11-2025  (Feinschliff v1.2.1)
Status: PRO / Compact Edition

Dieser Guide richtet sich an Anwender, die sich mit Terminalbefehlen sicher fühlen und eine klare, schnelle Installation bevorzugen.
Keine langen Erklärungen – aber genug Kontext, damit du sofort weißt, was du tust.

**Worum es hier geht:**

- Schnellstart ohne unnötige Schritte
- Plattformübergreifende Befehle
- Best-Practice Installationspfade
- Sauberes, reproduzierbares Setup

**Für wen ist dieser Guide NICHT gedacht?**

- absolute Einsteiger
- Nutzer, die jeden Schritt bebildert benötigen

Für diese Zielgruppe existiert der **Easy Windows Guide**.

--- (Windows, macOS, Linux)
Version 1.2
Stand: 29-11-2025
Status: PRO / Compact Edition

Dieser Guide richtet sich an Anwender mit soliden Terminalkenntnissen.
Keine Erklärungen, kein Ballast – nur die relevanten Befehle.

---

## 📌 Inhalt

- [TL;DR](#tldr--kurz--klar)
- [Systemanforderungen](#systemanforderungen)
- [Abhängigkeiten installieren](#abhängigkeiten-installieren)
- [TrackBridge Setup](#trackbridge-setup)
- [Konfiguration](#konfiguration)
- [CLI-Befehle](#cli-befehle)
- [Troubleshooting](#troubleshooting)

---

## TL;DR – Kurz & klar

Wähle ein Installationsverzeichnis deiner Wahl (empfohlen: **C:/Tools/TrackBridge** unter Windows oder `~/Tools/TrackBridge` unter macOS/Linux). Danach einfach der Befehlsfolge folgen:

```bash
# Repository klonen
git clone https://github.com/carxonic-dev/TrackBridge.git
cd TrackBridge

# Virtuelle Umgebung anlegen
python -m venv .venv
source .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt

# Konfiguration anlegen
cp config.example.json config.json      # Windows: copy config.example.json config.json

# Funktionstest
python main.py sanity-check

```

TrackBridge ist jetzt vollständig eingerichtet und betriebsbereit.

---

## Systemanforderungen

Benötigt wird lediglich eine moderne Python‑Umgebung und Grundwerkzeuge für den Download‑/Konvertierungsprozess:

- **Python 3.10+**
- **Git** (für Updates & Repository‑Zugriff)
- **ffmpeg** (Audioverarbeitung)
- **yt-dlp** (YouTube‑Extraktion)
- **Spotify Client-ID & Secret**

Alles Weitere wird automatisch per `pip install -r requirements.txt` nachgeladen.

---

## Abhängigkeiten installieren

Die folgenden Befehle installieren alle benötigten Systempakete pro Plattform.
Die Struktur ist bewusst identisch gehalten.

### Windows

```powershell
winget install Python.Python.3.12
winget install Git.Git
winget install Gyan.FFmpeg
winget install yt-dlp.yt-dlp
```

### macOS (Homebrew)

```bash
brew install python git ffmpeg yt-dlp
```

### Linux – Debian/Ubuntu

```bash
sudo apt update && \
  sudo apt install -y python3 python3-venv python3-pip git ffmpeg
pip install yt-dlp
```

### Linux – Arch

```bash
sudo pacman -S python python-pip git ffmpeg yt-dlp
```

---

## TrackBridge Setup

Kurz, klar und ohne Ballast:

### Git-Version

```bash
git clone https://github.com/carxonic-dev/TrackBridge.git
cd TrackBridge
```

### Virtuelle Umgebung

```bash
python -m venv .venv
source .venv/bin/activate     # macOS/Linux
.\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
```

---

## Konfiguration

```bash
cp config.example.json config.json       # macOS/Linux
copy config.example.json config.json     # Windows
```

### Minimalbeispiel

```json
{
  "OutputDirectory": "./output",
  "MaxParallelDownloads": 4,
  "SpotifyClientId": "CLIENT_ID",
  "SpotifyClientSecret": "CLIENT_SECRET"
}
```

---
## CLI-Befehle

### Essentials

```bash
python main.py sanity-check
python main.py export --playlist-id <ID>
python main.py run-downloads --playlist-id <ID>
```

### Nützlich, aber optional

```bash
python main.py export --file playlists.txt   # Batch-Export
```

---

## Troubleshooting

### Die 3 häufigsten Fehler

**1) yt-dlp fehlt**

```bash
which yt-dlp   # macOS/Linux
where yt-dlp   # Windows
```

**2) venv lässt sich nicht aktivieren (Windows)**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**3) Spotify 401**

Falsche Client-ID/Secret oder Token abgelaufen.

---
__Ende PRO Guide Version 1.2.1__
