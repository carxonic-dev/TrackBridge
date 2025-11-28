# TrackBridge – Playlist2Audio Engine

*(vollständig überarbeitet und GitHub-ready)*

TrackBridge ist ein leistungsstarkes, professionelles CLI‑Tool zum Exportieren, Analysieren, Herunterladen, Taggen und Verwalten von Spotify‑Playlisten – optimiert für DJs, Content‑Creator, Archivare, KI‑Automations‑Workflows und alle, die saubere Audio‑Libraries lieben.

Der Kern von TrackBridge:
**Spotify‑Playlist rein → DJ‑taugliche, sauber getaggte Audiodateien raus.**

---

## 🚀 Features

### 🎧 Playlist‑Export

* Exportiert Spotify‑Playlisten als Extended‑JSON.
* Optionaler Export einer yt‑dlp Suchliste.
* Enthält alle Metadaten für Download, Tagging & Registry.

### ⬇️ Download‑Pipeline

* Automatischer Download‑Plan.
* yt‑dlp Integration mit Format‑Priorisierung.
* Parallele Worker + Retry‑Mechanik.
* Saubere Ordnerstruktur pro Playlist.

### 🏷 Präzises Tagging

* Mutagen‑Engine (MP3, M4A/MP4, AIFF).
* Setzt: Titel, Artist, Album, Tracknummer, BPM, Key.
* Covers möglich.
* DJ‑kompatibel (Rekordbox, Serato, Traktor, Engine DJ).

### 📚 SQLite‑Registry (optional)

* Speichert Track‑ID, Künstler, Pfad, Größe, Hash, Timestamp.
* Optional Speicherung der Spotify‑URL (nur DB, nie Audiofile).

### 🔁 Retag‑Pipeline

* Nachträgliches Tagging vorhandener Dateien.
* Keine Downloads nötig.

### 🔍 Playlist‑Analyse

* Format‑Check, DJ‑Kompatibilität, Duplicate‑Scan.

---

## 🧬 Architektur & Module

```
main.py               → CLI / Subcommands
spotify_client.py     → API Zugriff
playlist_exporter.py  → JSON Export
yt_dlp_runner.py      → Downloads & Worker
tagging.py            → Mutagen Tagging
track_registry.py     → SQLite Registry
format_profiles.py    → DJ‑Profile
config.py             → Config / Validation
collection_analyzer.py→ Analyse‑Tools
```

---

## 📦 Installation

### Spotify Developer App einrichten

1. [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. App erstellen
3. Redirect‑URL: [http://localhost/](http://localhost/)
4. Client‑ID & Secret kopieren
5. In `.env` oder `config.json` eintragen

### Option A – `.env`

```
SpotifyClientId=DEINE-ID
SpotifyClientSecret=DEIN-SECRET
```

### Option B – `config.json`

```json
{
  "SpotifyClientId": "<ID>",
  "SpotifyClientSecret": "<SECRET>"
}
```

### TrackBridge installieren

```
git clone https://github.com/carxonic-dev/TrackBridge.git
cd TrackBridge
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## ⚙ Konfiguration (config.json)

```json
{
  "OutputDirectory": "~/Music/TrackBridge",
  "MaxParallelDownloads": 2,
  "DownloadMaxRetries": 2,
  "SkipExistingFiles": true,
  "RegistryEnabled": true,
  "RegistryStoreSpotifyUrl": true,
  "AudioPreferredFormats": ["m4a", "aac", "mp3", "flac", "alac"],
  "DJCompatibilityProfile": "cdj_default",
  "DJWarnOnIncompatible": true
}
```

---

## 🧰 CLI‑Kommandos

### 🔧 **sanity-check**

```bash
python main.py sanity-check
```

### 📤 **export**

```bash
python main.py export --playlist-id <ID> --limit 50
```

### 🧾 **export‑ytdlp**

```bash
python main.py export-ytdlp --playlist-id <ID>
```

### 🗂 **plan‑downloads**

```bash
python main.py plan-downloads --playlist-id <ID> --limit 10
```

### ⬇️ **run‑downloads**

```bash
python main.py run-downloads --playlist-id <ID> --limit 20
```

### 🏷 **tag‑playlist**

```bash
python main.py tag-playlist --playlist-id <ID> --limit 10
```

### 🔍 **analyze‑playlist**

```bash
python main.py analyze-playlist --playlist-id <ID>
```

### 🛠 **debug-registry**

```bash
python main.py debug-registry
```

---

## 🧪 Typischer Workflow

```
python main.py sanity-check
python main.py export --playlist-id <ID>
python main.py run-downloads --playlist-id <ID>
python main.py tag-playlist --playlist-id <ID>
```

---

## 🤖 Zukunft & MusicVault‑Integration

TrackBridge wird langfristig eng mit **MusicVault** verzahnt:

* automatische Library‑Übernahme
* Duplicate‑Erkennung
* GUI / Web‑UI
* Multi‑User Profile
* Reencode‑Engine

---

## ☕ Support

Wenn dir TrackBridge oder eines meiner anderen Open-Source-Projekte weiterhilft, kannst du meine Arbeit hier unterstützen:

[![Buy Me A Coffee](https://img.buymeacoffee.com/button-api/?text=Support%20me&emoji=☕&slug=carxonicdev&button_colour=0d1117&font_colour=ffffff&font_family=Inter&outline_colour=8A2BE2&coffee_colour=FF0F87)](https://buymeacoffee.com/carxonicdev)

---

## 📄 Lizenz

MIT License – freie Nutzung für private & kommerzielle Projekte.

---

## ❤️ Credits

Developed by **carxonic-dev**, mit Fokus auf DJ‑Kompatibilität, saubere Metadaten, stabile Workflows & moderne Python‑Architektur.
