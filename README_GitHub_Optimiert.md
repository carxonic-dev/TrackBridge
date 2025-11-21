# 🎧 Spotify → yt-dlp Downloader (Pro Edition)

> Ein leistungsstarkes, professionelles CLI‑Tool zum Exportieren, Analysieren und Herunterladen von Spotify‑Playlists – mit DJ‑Kompatibilitätsprofilen, Multi‑Worker‑Engine, Re‑Encoding, Tagging‑Pipeline und Zukunftsperspektive „MusicVault“.

---

## 🚀 Features

### 🔹 1. Spotify‑Playlist‑Export (Extended JSON)
- Vollständige Playlist‑Metadaten
- Titel, Künstler, Album, ISRC
- BPM / Key (falls verfügbar)
- Audio‑Feature‑Fallback‑Handling
- Präzise Track‑Indizes & Normalisierung

### 🔹 2. yt-dlp Runner (Multi‑Worker)
- Parallele Downloads (2–8 Worker)
- Retry‑System pro Track
- SkipExisting‑Logik
- Fortschrittsausgabe pro Track
- Robuste Fehlerbehandlung

### 🔹 3. DJ‑Kompatibilitätsprofil
Optimiert für:
- Pioneer CDJ‑2000 Nexus 2
- Rekordbox
- Traktor
- Serato  
→ unterstützt: **AAC/M4A**, **AIFF**, **WAV** (optional), **MP3**  
→ Vermeidet problematische Formate: **WEBM**, **OPUS**, **OGG**

### 🔹 4. Re‑Encoding‑Engine (FFmpeg)
- Automatische Formatkorrektur
- Optional: „Immer DJ‑kompatibles Format erzwingen“
- Verlustfreie Strategien (Copy Mode)
- Warnung bei unnötigen Re‑Encodes

### 🔹 5. Tagging‑System
- ID3‑Tag & Cover‑Support (in Arbeit)
- JSON‑basierte Metadatenquelle
- Zukunft: Tag‑Templates pro DJ‑Software

### 🔹 6. Playlist‑Analyse
- Scan eines Playlist‑Ordners
- Übersicht über Formate, inkompatible Dateien, Duplikate
- Vorbereitung für MusicVault

---

## 📦 Installation

### 1. Repository klonen
```bash
git clone https://github.com/<DEIN-USER>/spotify_2_yt-dlp.git
cd spotify_2_yt-dlp
```

### 2. venv erstellen
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

### 3. Spotify API vorbereiten
`.env` Datei erstellen:

```
SPOTIFY_CLIENT_ID=xxxxx
SPOTIFY_CLIENT_SECRET=yyyyy
```

---

## 🧪 CLI‑Befehle

### Token‑Check
```bash
python main.py sanity-check
```

### Playlist als JSON exportieren
```bash
python main.py export --playlist-id <ID> --limit 10
```

### yt-dlp Textliste erzeugen
```bash
python main.py export-ytdlp --playlist-id <ID> --output meine_liste.txt
```

### Download‑Plan erstellen (Dry‑Run)
```bash
python main.py plan-downloads --playlist-id <ID>
```

### Downloads starten
```bash
python main.py run-downloads --playlist-id <ID> --limit 20
```

### Analyse des Ordners (Format & DJ‑Kompatibilität)
```bash
python main.py analyze-playlist --playlist-id <ID>
```

---

## 🏗 Architektur

```
Spotify API
   ↓
Extended JSON
   ↓
Download Planner
   ↓
yt-dlp Runner (Multi Worker)
   ↓
Re-Encoding (optional)
   ↓
Tagging (WIP)
   ↓
DJ-kompatible Audio Library
```

---

## 🛣 Roadmap

### v1.0 – MVP (CLI)
- ✓ Vollständige Playlist‑Pipeline
- ✓ yt-dlp Runner
- ✓ SkipExisting
- ✓ Re-Encode
- ✓ Analyse‑Modul
- ✓ CLI Dokumentation

### v1.1 – Tagging Engine
- ✔ ID3 / MP4 Tags
- ✔ Cover‑Import
- ✔ DJ‑Kompatibilitätsnormen

### v1.2 – MusicVault (separates Projekt)
- Multi‑User Library
- Duplikaterkennung
- Playlist‑Imports (VDJ, Rekordbox, iTunes, Serato)
- SQL‑Backend
- Web‑UI

---

## 🧑‍💻 Contributing

Pull‑Requests willkommen!  
Bitte vorher Issues nutzen, damit wir koordiniert arbeiten.

---

## 📄 Lizenz
MIT – freie Nutzung für private & kommerzielle Projekte.

---

## ⭐ Wenn dir das Tool hilft…
Gern ein ⭐ auf GitHub dalassen – damit unterstützt du die Weiterentwicklung!
