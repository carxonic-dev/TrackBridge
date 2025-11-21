# spotify_2_yt-dlp  
CLI-Tool zum Exportieren von Spotify-Playlists und automatischem Download über yt-dlp  
Version 1.0 · Stand 20-11-2025

---

## 📌 Überblick

Dieses Tool bietet eine vollständige Pipeline:

1. **Spotify-Playlist einlesen**  
2. **Metadaten + Audioinformationen als Extended-JSON exportieren**  
3. **Optional: yt-dlp-Suchliste erzeugen**
4. **Download-Plan erzeugen (Dry-Run)**  
5. **Downloads parallel mit Worker-Threads durchführen**
6. **Format-Analyse & DJ-Kompatibilitätscheck**  
7. **(optional) Track-Registry / Datenbank-Schicht**

Alle Schritte können einzeln oder kombiniert ausgeführt werden.

---

## ⚙️ Installation

### 1. Repository klonen
```bash
git clone <repo-url>
cd spotify_2_yt-dlp
```

### 2. Virtuelle Umgebung
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Abhängigkeiten
```bash
pip install -r requirements.txt
```

yt-dlp muss **global** installiert sein:

```powershell
winget install yt-dlp
```

---

## 📂 Projektstruktur

```
spotify_2_yt-dlp/
│ main.py
│ config.py
│ format_profiles.py
│ yt_dlp_runner.py
│ spotify_exporter.py
│ track_registry.py
│ download_planner.py
│ analyze_utils.py
│ config.json
│ .env (optional)
```

---

## 🚀 CLI Kommando-Übersicht

Top-Level Hilfe:
```bash
python main.py -h
```

### Verfügbare Kommandos

| Befehl | Beschreibung |
|--------|--------------|
| `sanity-check` | Testet Spotify-Token & Projektstruktur. |
| `export` | Exportiert Playlist → JSON (Extended-Format). |
| `export-ytdlp` | Erzeugt eine yt-dlp-Trackliste (Textdatei mit ytsearch1:Artist – Title). |
| `plan-downloads` | Erstellt Download-Plan (Dry-Run). |
| `run-downloads` | Führt Downloads parallel mit yt-dlp aus. |
| `analyze-playlist` | Prüft Dateien, Formate, DJ-Kompatibilität. |

---

# 🔧 Detaillierte CLI-Dokumentation

---

## 1️⃣ sanity-check

```bash
python main.py sanity-check
```

Prüft:

- Zugriff auf Spotify
- Tokens
- config.json vorhanden?
- Zielverzeichnisse erreichbar?

---

## 2️⃣ export

Exportiert eine Spotify-Playlist als erweiterte JSON.

```bash
python main.py export --playlist-id <ID> [--limit <n>] [--output <pfad>]
```

### Parameter:

| Parameter | Bedeutung |
|----------|-----------|
| `--playlist-id` | Spotify Playlist-ID |
| `--limit` | Maximale Anzahl Titel (optional) |
| `--output` | Ausgabepfad (optional) |

### Beispiel:
```bash
python main.py export --playlist-id 3ENm4IUzswtJ2i0LBYQBSr --limit 50
```

---

## 3️⃣ export-ytdlp

Erzeugt eine Textdatei im Format:

```
ytsearch1:Artist - Title
ytsearch1:Artist - Title
...
```

```bash
python main.py export-ytdlp --playlist-id <ID> [--limit <n>] [--output <pfad>]
```

---

## 4️⃣ plan-downloads

Erzeugt einen Download-Plan (Dry-Run), keine Downloads.

```bash
python main.py plan-downloads --playlist-id <ID> [--limit <n>]
```

Oder basierend auf bereits exportierter JSON:

```bash
python main.py plan-downloads --json path/to/file.json
```

---

## 5️⃣ run-downloads

Startet die tatsächlichen Downloads.

```bash
python main.py run-downloads --playlist-id <ID> [--limit <n>]
```

oder

```bash
python main.py run-downloads --json path/to/file.json
```

Features:

- parallele Downloads (Worker)
- Retry-Mechanismus
- SkipExisting (kein Überschreiben)
- Zielpfad aus config.json
- Debug-Ausgabe zu jedem Job

---

## 6️⃣ analyze-playlist

Analysiert einen Playlist-Ordner:

- vorhandene Dateiformate
- mehrere Versionen/Qualität
- DJ-Kompatibilität (MP3/AAC/M4A/AIFF/WAV)
- WEBM / OPUS Warnungen
- fehlende Tracks

```bash
python main.py analyze-playlist --playlist-path <pfad>
```

---

# 📁 config.json

Beispiel:

```json
{
  "OutputRoot": "D:/Projekte/20_DATA/Playlist_export_spotify",
  "MaxParallelDownloads": 2,
  "RetryCount": 2,
  "AudioPreferredFormats": ["m4a", "mp3"],
  "DJCompatibilityProfile": "CDJ-2000-NXS2"
}
```

---

# 🔒 Track-Registry (optional)

Die SQLite-Registry kann:

- behaltene Dateien tracken
- Pfade nach Verschiebungen referenzieren
- Duplikate verhindern
- unterschiedliche User-Profile verwalten (Zukunft)

Aktivierung später über Config/GUI.

---

# 📈 Roadmap

- ID3-Tagging (MP3/M4A/AIFF)  
- Cover-Download  
- Reencode-Engine  
- DJ-Kompatibilitätsfilter  
- GUI (Electron/Qt/Python-GUI)  
- Multi-User-Profiles  
- MusicVault-System  

---

# 🧪 Beispiele

### Playlist exportieren → JSON:
```bash
python main.py export --playlist-id 3ENm4IUzswtJ2i0LBYQBSr
```

### yt-dlp-Liste erzeugen:
```bash
python main.py export-ytdlp --playlist-id 3ENm4IUzswtJ2i0LBYQBSr
```

### Downloads starten:
```bash
python main.py run-downloads --playlist-id 3ENm4IUzswtJ2i0LBYQBSr --limit 10
```

---

# © Autor

Carsten · spotify_2_yt-dlp (2025)
