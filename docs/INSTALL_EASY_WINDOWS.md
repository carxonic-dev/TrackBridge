<!-- markdownlint-disable MD022 MD032 MD033 MD025 MD040 MD034 MD031 MD026 --> MD022 MD032 MD033 -->
# INSTALL_EASY_WINDOWS.md
TrackBridge – Einfache Installation für Windows 10 & Windows 11

**Version:** 1.0
**Stand:** 29-11-2025
**Status:** Stable (Easy Windows Guide)

Diese Anleitung ist für Menschen gedacht, die **keine technischen Vorkenntnisse** haben.
Wenn du weißt, wie man eine Maus bedienst, Dateien öffnest und mal ein Programm installiert hast – reicht das völlig.

TrackBridge holt deine **Spotify-Playlisten** und macht daraus sauber getaggte **Audiodateien**, lokal auf deinem Rechner.

---

## 📌 Inhalt
1. [Vorbereitung: Was du brauchst](#1-vorbereitung-was-du-brauchst)
2. [TrackBridge herunterladen](#2-trackbridge-herunterladen)
3. [Ordner C:\Tools\TrackBridge anlegen](#3-ordner-ctoolstrackbridge-anlegen)
4. [ZIP entpacken und Dateien kopieren](#4-zip-entpacken-und-dateien-kopieren)
5. [PowerShell (Administrator) öffnen](#5-powershell-administrator-öffnen)
6. [Benötigte Programme installieren](#6-benötigte-programme-installieren)
7. [TrackBridge-Ordner in der PowerShell öffnen](#7-trackbridge-ordner-in-der-powershell-öffnen)
8. [Virtuelle Umgebung erstellen & aktivieren](#8-virtuelle-umgebung-erstellen--aktivieren)
9. [Abhängigkeiten installieren](#9-abhängigkeiten-installieren)
10. [config.json einrichten](#10-configjson-einrichten)
11. [Erster Funktionstest](#11-erster-funktionstest)
12. [Häufige Fehler (kurz erklärt)](#12-häufige-fehler-kurz-erklärt)
13. [Fertig! 🎉](#13-fertig)

---

<a id="1-vorbereitung-was-du-brauchst"></a>
## 1. Vorbereitung: Was du brauchst
Für TrackBridge benötigst du:
- Windows 10 oder Windows 11
- ein kostenloses Spotify-Konto
- ein Spotify Developer Konto
- Python, Git, ffmpeg, yt-dlp (werden installiert)

---

<a id="2-trackbridge-herunterladen"></a>
## 2. TrackBridge herunterladen
1. Browser öffnen.
2. https://github.com/carxonic-dev/TrackBridge öffnen.
3. Auf **„Code“** klicken → **„Download ZIP“**.
4. ZIP speichern.

---

<a id="3-ordner-ctoolstrackbridge-anlegen"></a>
## 3. Ordner C:\Tools\TrackBridge anlegen
1. Windows-Explorer öffnen.
2. Links auf **„Dieser PC“** klicken.
3. **Lokaler Datenträger (C:)** öffnen.
4. Rechtsklick → **Neu** → **Ordner** → Name: `Tools`
5. Ordner **Tools** öffnen.
6. Rechtsklick → **Neu** → **Ordner** → Name: `TrackBridge`

---

<a id="4-zip-entpacken-und-dateien-kopieren"></a>
## 4. ZIP entpacken und Dateien kopieren
1. ZIP-Datei rechtsklicken → **„Alle extrahieren…“**.
2. Entpackten Ordner öffnen.
3. STRG+A → alles markieren.
4. STRG+C → kopieren.
5. Zu `C:\Tools\TrackBridge` wechseln.
6. STRG+V → einfügen.

---

<a id="5-powershell-administrator-öffnen"></a>
## 5. PowerShell (Administrator) öffnen
1. Startmenü öffnen.
2. Eingeben: `PowerShell` oder `Pwsh`.
3. Rechtsklick → **Als Administrator ausführen**.

---

<a id="6-benötigte-programme-installieren"></a>
## 6. Benötigte Programme installieren
Alle folgenden Befehle in die PowerShell eingeben und **Enter** drücken.

### Winget prüfen:
```powershell
winget --version
```

### Python installieren:
```powershell
winget install Python.Python.3.12
```

### Git installieren:
```powershell
winget install Git.Git
```

### ffmpeg installieren:
```powershell
winget install Gyan.FFmpeg
```

### yt-dlp installieren:
```powershell
winget install yt-dlp.yt-dlp
```

---

<a id="7-trackbridge-ordner-in-der-powershell-öffnen"></a>
## 7. TrackBridge-Ordner in der PowerShell öffnen
```powershell
cd C:\Tools\TrackBridge
```

---

<a id="8-virtuelle-umgebung-erstellen--aktivieren"></a>
## 8. Virtuelle Umgebung erstellen & aktivieren & aktivieren
### Erstellen:
```powershell
python -m venv .venv
```

### Aktivieren:
```powershell
.\.venv\Scripts\Activate.ps1
```

Falls Windows eine Sicherheitswarnung zeigt:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

<a id="9-abhängigkeiten-installieren"></a>
## 9. Abhängigkeiten installieren
```powershell
pip install -r requirements.txt
```

---

<a id="10-configjson-einrichten"></a>
## 10. config.json einrichten
1. Explorer öffnen → `C:\Tools\TrackBridge`
2. Datei `config.example.json` kopieren
3. Kopie umbenennen zu `config.json`
4. Mit Editor öffnen

Beispiel:
```json
{
  "OutputDirectory": "C:/Tools/TrackBridge/output",
  "MaxParallelDownloads": 2,
  "SkipExistingFiles": true,
  "RegistryEnabled": true,
  "SpotifyClientId": "DEINE_CLIENT_ID",
  "SpotifyClientSecret": "DEIN_CLIENT_SECRET"
}
```

---

<a id="11-erster-funktionstest"></a>
## 11. Erster Funktionstest
### Spotify prüfen:
```powershell
python main.py sanity-check
```

### Playlist-ID herausfinden:
Beispiel-URL:
```
https://open.spotify.com/playlist/6OvxG32lOKVsgLLO62jrLV
```
ID = Teil nach dem letzten `/`.

### Playlist exportieren:
```powershell
python main.py export --playlist-id DEINE_ID
```

### Downloads starten:
```powershell
python main.py run-downloads --playlist-id DEINE_ID --limit 3
```

---

<a id="12-häufige-fehler-kurz-erklärt"></a>
## 12. Häufige Fehler (kurz erklärt) (kurz erklärt)
### „python wird nicht erkannt“
→ Neu installieren, PowerShell neu starten.

### „Skripte deaktiviert“
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### „yt-dlp wird nicht gefunden“
```powershell
winget install yt-dlp.yt-dlp
```

### Spotify-Fehler 401
→ Client-ID oder Secret falsch.

---

<a id="13-fertig"></a>
## 13. Fertig! 🎉! 🎉
TrackBridge ist installiert, eingerichtet und bereit zur Nutzung.

## Changelog (Letzte Änderungen)

- **29-11-2025 – Version 1.0 erstellt**
  - Easy-Guide vollständig erstellt
  - Ankerstruktur hinzugefügt
  - markdownlint-Regeln erweitert
  - Header-Hierarchie geglättet
  - Versionierung integriert

<!-- markdownlint-enable -->
