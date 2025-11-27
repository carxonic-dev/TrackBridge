# spotify_2_yt-dlp

Ein leistungsstarkes, professionelles CLI‑Tool zum **Exportieren**, **Analysieren**, **Herunterladen**, **Taggen** und **Verwalten** von Spotify‑Playlists – optimiert für **DJs**, **Content‑Creator**, **Archivare** und **Automations-Freaks**. Entwickelt für Stabilität, Präzision und saubere Audio‑Workflows.

Unterstützt:
- Spotify → Extended‑JSON Export
- yt‑dlp Download mit Format-Priorisierung
- Mutagen‑Tagging (ID3 / MP4)
- SQLite‑Registry für Datei‑Tracking
- Nachträgliches Tagging (Retag-Pipeline)
- Analyse von Playlists im Dateisystem

Der Fokus liegt auf **Robustheit**, **Automatisierung** und **sauberen Metadaten**, ohne Experimente im Audiotagging.

---

## 🚀 Features

### 🎧 Playlist-Export
- Exportiert öffentliche Spotify-Playlists als **Extended‑JSON**.
- Optionaler Export einer **yt-dlp Suchliste** (für manuelle Workflows).
- Enthält alle notwendigen Informationen für Download, Tagging & Registry.

### ⬇️ Download-Pipeline (run-downloads)
- yt‑dlp Integration mit Format-Priorisierung:
  - `m4a` → `aac` → `mp3` → `flac` → `alac`
- Parallele Worker + Retry-Logik
- Automatische Dateibenennung nach Track-Index
- Speicherort pro Playlist (saubere Ordnerstruktur)

### 🏷 Präzises Tagging
- Mutagen-basierte Engine, setzt zuverlässig:
  - Titel
  - Artist / Album Artist
  - Album
  - Track-Index
  - BPM (falls in JSON)
  - Key (falls in JSON)
- Kommentar enthält **keine URLs**, nur technische Werte (BPM/Key).
- DJ-kompatible Werte für Rekordbox, Engine DJ, Serato, Traktor.

### 📚 SQLite-Registry (optional)
- Aktivierbar über `config.json`.
- Speichert:
  - Spotify-Track-ID
  - Titel, Artist, Dauer
  - Optional: **Spotify-URL** (sauber, nicht im Audio-Tag)
  - Verknüpfte Files + Dateimetadaten
- Praktisch für spätere Erweiterungen:
  - Duplicate-Check
  - Reencode-Historie
  - Datei-Management

### 🔁 Retag-Pipeline (tag-playlist)
- Wendet das Tagging **nachträglich** auf vorhandene Dateien an.
- Ideal nach Änderungen im Tagging-Algorithmus.
- Optional: Registry erneut aktualisieren.
- Zero-Risk für bestehende Files, da kein Download nötig.

### 🔍 Playlist-Analyser
- Prüft lokale Playlist-Ordner auf:
  - Formate & Codecs
  - DJ-Kompatibilität
  - fehlende oder doppelte Dateien

---

## 📦 Installation

### Spotify Developer Key einrichten
Damit das Tool funktionieren kann, benötigst du eine **Spotify Client ID** und ein **Client Secret**.

Du kannst diese Daten auf zwei Wegen hinterlegen:

---
### **Option A – `.env` verwenden (empfohlen für Entwickler)**
Lege im Projektordner eine Datei `.env` an und trage ein:
```
SpotifyClientId=DEINE-ID
SpotifyClientSecret=DEIN-SECRET
```
Diese Variante ist ideal für lokale Entwicklung, da keine sensiblen Daten in der `config.json` landen.

---
### **Option B – Daten in `config.json` hinterlegen (empfohlen für Endnutzer / Deployment)**
Füge folgendes in deine `config.json` ein:
```json
"SpotifyClientId": "DEINE-ID",
"SpotifyClientSecret": "DEIN-SECRET"
```
Die Werte werden automatisch über `config.py` geladen:
```python
SPOTIFY_CLIENT_ID = CONFIG.get("SpotifyClientId", "")
SPOTIFY_CLIENT_SECRET = CONFIG.get("SpotifyClientSecret", "")
```

---
### Spotify Developer App anlegen

**Schritt 1 – Spotify Developer Dashboard öffnen**  
https://developer.spotify.com/dashboard

**Schritt 2 – Login**  
Mit deinem Spotify-Account einloggen.

**Schritt 3 – Neue App anlegen**  
"Create App" → beliebiger Name, z. B. *spotify_2_yt-dlp*.

**Schritt 4 – Redirect-URL setzen**  
Für dieses Tool ausreichend:
```
http://localhost/
```

**Schritt 5 – Client ID & Secret kopieren**

**Schritt 6 – In `.env` oder `config.json` hinterlegen**

---
### Funktionstest
```bash
python main.py sanity-check
```
Wenn alles korrekt gesetzt wurde, bestätigt der Sanity‑Check die erfolgreiche Authentifizierung.

Installation

```bash
git clone https://github.com/<dein-user>/spotify_2_yt-dlp.git
cd spotify_2_yt-dlp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ⚙️ Konfiguration (`config.json`)

```json
{
  "SpotifyClientId": "<id>",
  "SpotifyClientSecret": "<secret>",
  "OutputDirectory": "D:/Projekte/20_DATA/Playlist_export_spotify",
  "MaxParallelDownloads": 2,
  "DownloadMaxRetries": 2,
  "SkipExistingFiles": true,
  "RegistryEnabled": true,
  "RegistryStoreSpotifyUrl": true,
  "AudioPreferredFormats": ["m4a", "aac", "mp3", "flac", "alac"],
  "DjCompatibilityProfile": "cdj_default",
  "DjWarnOnIncompatible": true
}
```

Wichtig:
- **RegistryStoreSpotifyUrl** bestimmt, ob die Spotify-URL in die Registry geschrieben wird.
- Die URL wird **nie** ins Audiofile geschrieben, nur in die DB.

---

## 🧰 CLI-Kommandos

### 🔧 sanity-check
```bash
python main.py sanity-check
```
Prüft Spotify-API & Grundkonfiguration.

### 📤 export
```bash
python main.py export --playlist-id <ID>
```
Exportiert Playlist als Extended‑JSON.

### 🧾 export-ytdlp
```bash
python main.py export-ytdlp --playlist-id <ID>
```
Erzeugt reine Suchliste für yt‑dlp.

### 🗂 plan-downloads
```bash
python main.py plan-downloads --playlist-id <ID>
```
Dry‑Run ohne echte Downloads.

### ⬇️ run-downloads
```bash
python main.py run-downloads --playlist-id <ID> --limit 20
```
Kompletter Download-/Tagging-/Registry-Workflow.

### 🏷 tag-playlist
```bash
python main.py tag-playlist --playlist-id <ID> --limit 10
```
- Taggt bereits vorhandene Dateien nach.
- Optional: `--no-registry`

### 🔍 analyze-playlist
```bash
python main.py analyze-playlist --playlist-id <ID>
```
Analysiert lokalen Playlist-Ordner.

---

## 🧪 Typischer Workflow

1. **Sanity-Check**  
```bash
python main.py sanity-check
```

2. **Export**  
```bash
python main.py export --playlist-id <ID>
```

3. **Downloads starten**  
```bash
python main.py run-downloads --playlist-id <ID>
```

4. **Nachträgliches Tagging (optional)**  
```bash
python main.py tag-playlist --playlist-id <ID>
```

---

## ☕ Buy Me a Coffee
Wenn dir das Projekt gefällt oder du meinen weiteren Open‑Source‑Kram unterstützen möchtest:

👉 **https://www.buymeacoffee.com/<deinname>**

Jede Unterstützung hilft, öfter Updates & neue Features zu liefern. 🙌

---

## 📄 Lizenz
MIT License – frei für private & kommerzielle Nutzung.

---

## ❤️ Credits
Projektarchitektur, Tagging-Engine und Workflow-Design mit besonderem Fokus auf:
- DJ‑Kompatibilität
- saubere Metadaten
- reproduzierbare Abläufe
- Erweiterbarkeit (Web‑Frontend, GUI, Plugins)

Dieses Projekt wurde u. a. durch Pair‑Programming mit einer KI verbessert – aber alle wichtigen Entscheidungen bleiben menschlich. 😉

