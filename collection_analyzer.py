from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from config import (
    OUTPUT_DIRECTORY,
    KNOWN_AUDIO_EXTENSIONS,
    DJ_COMPATIBILITY_PROFILE,
)
from format_profiles import is_ext_compatible_with_active_profile


def analyze_playlist_folder(playlist_id: str) -> None:
    """
    Analysiert den Zielordner einer Playlist und gibt eine Übersicht
    über vorhandene Dateien, Formate und DJ-Kompatibilität aus.

    - Scannt OUTPUT_DIRECTORY/<playlist_id>
    - Zählt Dateien pro Extension
    - Markiert inkompatible Formate basierend auf dem aktiven DJ-Profil
    """

    base_dir = Path(OUTPUT_DIRECTORY)
    playlist_dir = base_dir / playlist_id

    print("========== PLAYLIST-ANALYSE ==========")
    print(f"Output-Basis:  {base_dir}")
    print(f"Playlist-Ordner: {playlist_dir}")
    print(f"DJ-Profil:     {DJ_COMPATIBILITY_PROFILE}")
    print("======================================")

    if not playlist_dir.exists() or not playlist_dir.is_dir():
        print("[INFO] Der Playlist-Ordner existiert nicht oder ist kein Verzeichnis.")
        print("       Bitte zuerst einen Download/Export für diese Playlist ausführen.")
        return

    # Alle bekannten Audio-Dateien einsammeln
    audio_files: List[Path] = []
    for ext in KNOWN_AUDIO_EXTENSIONS:
        audio_files.extend(playlist_dir.glob(f"*.{ext}"))

    if not audio_files:
        print("[INFO] Es wurden im Playlist-Ordner keine Audio-Dateien gefunden.")
        return

    # Zählung pro Dateiendung
    counts: Dict[str, int] = {}
    incompatible_files: List[Path] = []

    for f in audio_files:
        ext = f.suffix.lstrip(".").lower()
        counts[ext] = counts.get(ext, 0) + 1

        if not is_ext_compatible_with_active_profile(ext):
            incompatible_files.append(f)

    total = len(audio_files)
    print()
    print(f"Gesamtzahl Audio-Dateien: {total}")
    print()
    print("Formate im Ordner:")
    print("-------------------")
    for ext, cnt in sorted(counts.items(), key=lambda kv: kv[0]):
        compat_flag = (
            "OK"
            if is_ext_compatible_with_active_profile(ext)
            else "WARN"
        )
        print(f"  .{ext:<5}  -> {cnt:3d} Datei(en)   [{compat_flag}]")
    print("-------------------")

    if incompatible_files:
        print()
        print("Inkompatible oder problematische Dateien für das aktive DJ-Profil:")
        print("-----------------------------------------------------------------")
        for f in incompatible_files:
            print(f"- {f.name}")
        print("-----------------------------------------------------------------")
    else:
        print()
        print("Alle Dateien im Ordner sind mit dem aktiven DJ-Profil kompatibel.")
