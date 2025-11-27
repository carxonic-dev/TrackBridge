# Appendix 1 – Developer Guide (Level C)

Ein vollständiger, tiefgehender Entwickler-Guide für **spotify_2_yt-dlp**. Dieses Dokument richtet sich an Entwickler, Contributor, GUI-Bauer, Automations-Fans und alle, die das Projekt erweitern, debuggen oder für eigene Tools nutzen möchten.

Ziel: Eine **saubere, modulare, nachvollziehbare Architektur**, die langfristig erweiterbar bleibt, ohne die Codebasis zu verkomplizieren.

---

# 📚 Inhaltsverzeichnis
- [Einleitung](#einleitung)
- [Projektarchitektur](#projektarchitektur)
- [Modulübersicht](#modulübersicht)
- [Registry-Design (SQLite)](#registry-design-sqlite)
- [Tagging-Engine](#tagging-engine)
- [yt-dlp Runner & Worker-Architektur](#yt-dlp-runner--worker-architektur)
- [CLI-Architektur](#cli-architektur)
- [Format-Profile / DJ-Kompatibilität](#format-profile--dj-kompatibilität)
- [API-Hooks für GUI-Entwickler](#api-hooks-für-gui-entwickler)
- [Unit-Tests & Debugging](#unit-tests--debugging)
- [Roadmap & Erweiterungsmöglichkeiten](#roadmap--erweiterungsmöglichkeiten)

---

# Einleitung
spotify_2_yt-dlp ist modular aufgebaut, um:
- saubere Trennung zwischen **CLI**, **Business-Logic**, **Tagging**, **Registry** und **Download-Pipeline** sicherzustellen,
- Erweiterungen ohne technische Brüche zu ermöglichen,
- eine spätere GUI (Desktop oder Web) direkt andocken zu lassen.

Dieses Dokument beschreibt die komplette technische Struktur.

---

# Projektarchitektur
Grundverzeichnis:
```
spotify_2_yt-dlp/
 ┣ main.py                # CLI Entry
 ┣ spotify_client.py      # Spotify API
 ┣ playlist_exporter.py   # JSON-Export
 ┣ yt_dlp_runner.py       # Download-Pipeline
 ┣ tagging.py             # Mutagen Tagging Engine
 ┣ track_registry.py      # SQLite Registry Layer
 ┣ format_profiles.py     # DJ-kompatible Formatprofile
 ┣ util_filenames.py      # Safe Filename Generator
 ┣ config.py              # Config + Flags
 ┣ data/                  # Registry DB + Logs
 ┗ ... weitere Module
```

Mehrere Module sind bewusst „low-coupled“, damit spätere Erweiterungen wie z. B. GUI, Webservice oder Docker-Jobs ohne große Eingriffe möglich sind.

---

# Modulübersicht
## `config.py`
Zentrale Konfiguration. Lädt:
- `.env`
- `config.json`
- Standardwerte

Alle Flags (z. B. RegistryEnabled, RegistryStoreSpotifyUrl) werden hier gesetzt.

## `spotify_client.py`
Kommuniziert mit:
- Token-Endpoint (`SPOTIFY_TOKEN_URL`)
- Playlist-API
- Track-Metadaten

## `playlist_exporter.py`
Ziel: Extended-JSON erzeugen mit:
- Titel, Artist, Dauer
- BPM/Key (falls API erlaubt)
- Vollständige Track-Objects

## `yt_dlp_runner.py`
Download-Engine:
- Worker-System (Threads)
- Retry-Logik
- Format-Priorisierung
- Mapping audio -> Mutagen-Tagging
- Registry-Integration

## `tagging.py`
- Setzt Metadaten
- Einheitlich für alle Formate
- Zero-URL-Policy

## `track_registry.py`
Dedicated SQLite-Layer:
- Tabellen `tracks` und `files`
- Migrationen
- Upsert-Funktionen
- Registry-Debug-Funktion

## `format_profiles.py`
DJ-Kompatibilitätslayer:
- CDJ-Profil als Standard
- Erweiterbar (Denon, XDJ, Traktor)
- Geeignet für Format-Warnungen in analyze-playlist

---

# Registry-Design (SQLite)
## Ziele
- Wiedererkennbarkeit von Downloads
- Verknüpfung: Track-ID → Datei
- Grundlage für Duplicate Checks
- Grundlage für Reencode Checks
- Optionale Speicherung der Spotify-URL

## Tabellenstruktur
### `tracks`
```
spotify_track_id TEXT PRIMARY KEY
source_url TEXT NULL
primary_artist TEXT
track_title TEXT
album_name TEXT
track_number INT
best_file_id TEXT NULL
```

### `files`
```
track_id TEXT           # FK zu tracks.spotify_track_id
absolute_path TEXT
format TEXT
is_missing INT DEFAULT 0
PRIMARY KEY(track_id, absolute_path)
```

## Migrationslogik
Beim Start von `track_registry.py`:
- Tabellen werden erstellt, falls nicht vorhanden.
- Neue Spalten werden automatisch erzeugt (`ALTER TABLE`), falls fehlen.

Damit ist die Registry upgrade-fähig ohne Nutzereingriffe.

---

# Tagging-Engine
Mutagen-basiert. Einheitliches Interface:
```
apply_tags_to_file(path, metadata_dict)
```

### Setzt:
- Titel
- Artist(s)
- Album
- Tracknummer
- BPM (optional)
- Key (optional)

### Setzt NICHT:
- Kommentar-URLs
- Cover Art (Feature für zukünftige Versionen)

Design-Ziel:
- Keine DJ-Software wird verwirrt
- Maximale Kompatibilität
- Keine "exotischen" Frames

---

# yt-dlp Runner & Worker-Architektur
Download-Pipeline:

## Ablauf:
1. Extended-JSON laden
2. Download-Jobs erzeugen
3. Worker starten
4. Retry-Logik anwenden
5. Datei übergeben an Tagging-Engine
6. Registry updaten

## Worker-Modell
Threaded Worker W1, W2, …

Jeder Worker:
- zieht Job aus Queue
- führt Download aus
- versucht bis `DownloadMaxRetries`
- ruft Tagging + Registry auf

Fehler führen nicht zum Abbruch des Gesamtlaufs.

---

# CLI-Architektur
Alle CLI-Befehle definieren ihren eigenen Subparser:
```
subparsers = parser.add_subparsers(dest="command")
```

Jeder Befehl setzt:
```
parser.set_defaults(func=handler)
```

### Wichtige CLI-Handler:
- `handle_sanity_check`
- `handle_export_playlist`
- `handle_export_ytdlp`
- `handle_plan_downloads`
- `handle_run_downloads`
- `handle_analyze_playlist`
- `handle_tag_playlist`
- `handle_debug_registry`

CLI bleibt bewusst schlank.

---

# Format-Profile / DJ-Kompatibilität
Profiles definiert in `format_profiles.py`.
Beispielstruktur:
```
{
  "cdj_default": {
    "preferred_formats": ["m4a", "aac", "mp3", "wav", "flac"],
    "warn_formats": ["alac"],
    "tag_requirements": {
      "artist": true,
      "title": true,
      "track_number": true
    }
  }
}
```

Weitere Profile möglich:
- XDJ-XZ / XDJ-RX3
- Denon Prime
- Traktor 4
- Serato Player (Laptop)

Die CLI-Analyse (`analyze-playlist`) kann entsprechende Warnungen ausgeben.

---

# API-Hooks für GUI-Entwickler
GUI sollte ausschließlich die **öffentlichen API-Funktionen** nutzen, z. B.:

```
export_playlist()
run_downloads_for_playlist()
tag_playlist_files()
analyze_playlist_path()
```

Design-Hinweis:
- GUI ruft intern Python-Funktionen auf
- NICHT direkt Dateien/Registry anfassen
- Logging-Ausgaben können im GUI-Logfenster dargestellt werden

Mögliche GUI-Technologien:
- Tkinter
- PySide6 / Qt
- PyWebview
- Electron + Python Backend
- Streamlit (Web-GUI)

---

# Unit-Tests & Debugging
## Unit-Test-Empfehlungen
- Tagging-Tests (mit temporären Dateien)
- Registry-Tests (in temporärer SQLite-DB)
- Export-Tests (Mock-Spotify)
- Downloader-Tests (Mock yt-dlp)

## Debugging Tools
- `debug-registry` (integriert)
- SQL-Viewer (SQLite Browser)
- Logging aus `yt_dlp_runner`
- Testplaylist mit 1–2 Tracks

---

# Roadmap & Erweiterungsmöglichkeiten
## Kurzfristig
- Format-Profile erweitern
- Registry-Deduplizierung
- Test-Suite hinzufügen

## Mittelfristig
- GUI bauen (Desktop/Web)
- Auto-Reencode für inkompatible Player
- BPM/Key-Metadaten aus alternativen Quellen

## Langfristig
- Webservice / API
- Multi-User Playlisten-Verwaltung
- Cloud-Sync / Remote-Downloader

---

> Dieses Dokument dient als technische Grundlage für alle Entwickler, Contributor und GUI-Entwickler, die auf dem Projekt aufbauen möchten.

