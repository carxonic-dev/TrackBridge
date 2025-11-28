# INSTALL – TrackBridge Schritt für Schritt

Willkommen bei **TrackBridge** 👋  
Dieses Dokument erklärt dir **von ganz vorne**, wie du TrackBridge auf deinem Rechner installierst – auch dann, wenn du:

- noch nie mit der Kommandozeile (CLI) gearbeitet hast,
- noch nie ein GitHub-Projekt selbst installiert hast,
- nicht genau weißt, was „Python“, „venv“ oder „yt-dlp“ ist.

Ziel:  
Am Ende dieser Anleitung hast du **TrackBridge installiert**, **mit Spotify verbunden** und **deine erste Playlist erfolgreich verarbeitet**.

---

## 🧭 1. Was ist TrackBridge?

Kurz gesagt:

> **Spotify-Playlist rein → sauber getaggte Audiodateien raus.**

TrackBridge:
- liest deine **öffentlichen Spotify-Playlisten**,
- erstellt daraus eine **Playlist-Datei (JSON)**,
- lädt mit **yt-dlp** passende Audios,
- versieht die Dateien mit **Tags** (Titel, Artist, BPM, Key usw.),
- und legt alles sauber sortiert ab.

---

## 👤 2. Für wen ist diese Anleitung?

Für dich, wenn du:
- Windows, macOS oder Linux nutzt,
- einen **Spotify-Account** hast,
- noch nie ein CLI-Tool installiert hast,
- aber bei TrackBridge **an die Hand genommen** werden willst.

Du musst **kein Entwickler** sein.

---

## 🧩 3. Voraussetzungen

### 3.1 Spotify Developer Account
1. Öffne https://developer.spotify.com/dashboard
2. Logge dich ein
3. „Create an app“ → Name z. B. *TrackBridge Local Tool*
4. Redirect URL: `http://localhost/`
5. Danach findest du **Client ID** & **Client Secret** → später in `config.json` eintragen.

### 3.2 Python installieren
Mindestens **Python 3.10**.

#### Windows:
https://www.python.org/downloads/windows/  
Wichtig: Haken bei **Add Python to PATH** setzen.

#### macOS:
```bash
brew install python
```

#### Linux:
```bash
sudo apt install python3 python3-venv python3-pip
```

### 3.3 Git installieren
Zum Herunterladen von GitHub.

### 3.4 ffmpeg + yt-dlp installieren

#### Windows (PowerShell):
```powershell
winget install Gyan.FFmpeg
winget install yt-dlp.yt-dlp
```

#### macOS:
```bash
brew install ffmpeg yt-dlp
```

#### Linux:
```bash
sudo apt install ffmpeg
pip install yt-dlp
```

---

## 📥 4. TrackBridge herunterladen
```bash
git clone https://github.com/carxonic-dev/TrackBridge.git
cd TrackBridge
```

---

## 🧪 5. Virtuelle Umgebung (venv)

### 5.1 Erstellen
```bash
python -m venv .venv
```

### 5.2 Aktivieren
#### Windows:
```powershell
.\.venv\Scripts\Activate.ps1
```
Wenn Fehlermeldung:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux:
```bash
source .venv/bin/activate
```

---

## 📦 6. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

---

## ⚙ 7. Konfiguration (`config.json`)

`config.example.json` → kopieren → `config.json`

Beispiel-Auszug:
```json
{
  "OutputDirectory": "~/Music/TrackBridge",
  "MaxParallelDownloads": 2,
  "RegistryEnabled": true,
  "RegistryStoreSpotifyUrl": true,
  "SpotifyClientId": "DEINE_CLIENT_ID",
  "SpotifyClientSecret": "DEIN_CLIENT_SECRET"
}
```
**Client ID/Secret eintragen!**

---

## ✅ 8. Erster Test

### Sanity-Check
```bash
python main.py sanity-check
```

### Playlist exportieren
```bash
python main.py export --playlist-id <ID>
```

### Downloads starten
```bash
python main.py run-downloads --playlist-id <ID> --limit 3
```

Danach sollten Audiodateien im `OutputDirectory` liegen.

---

## 🧰 9. Häufige Fehler

### „python nicht gefunden“
- Windows: Python nicht im PATH → erneut installieren.
- macOS/Linux: statt `python` → `python3` verwenden.

### „Activate.ps1 verboten“
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### „yt-dlp not found“
- Windows: `winget install yt-dlp.yt-dlp`
- macOS: `brew install yt-dlp`
- Linux: `pip install yt-dlp`

### Spotify-Fehler 401 / 403
- Client Secret falsch
- Playlist privat oder falsch kopiert

---

## 🔄 10. TrackBridge aktualisieren
```bash
git pull
pip install -r requirements.txt --upgrade
```

---

## 🎉 11. Geschafft!
Du hast jetzt:
- TrackBridge installiert
- Spotify angebunden
- erste Playlist erfolgreich verarbeitet

Wenn du das als dein erstes CLI-Projekt geschafft hast → **starker Move! 💪**

