from __future__ import annotations

from pathlib import Path
from typing import Optional
import subprocess

from config import (
    ALLOW_REENCODE_FOR_INCOMPATIBLE,
    PREFERRED_HIGH_QUALITY_TARGET,
    REMOVE_SOURCE_AFTER_REENCODE,
)
from format_profiles import is_ext_compatible_with_active_profile


def should_reencode_file(path: Path) -> bool:
    """
    Entscheidet, ob eine Datei für das aktive DJ-Profil reencoded
    werden soll.

    Regeln:
    - Reencode nur, wenn ALLOW_REENCODE_FOR_INCOMPATIBLE = True
    - Reencode nur, wenn das aktuelle Format NICHT kompatibel ist
      (z. B. webm/opus im CDJ-Profil).
    """
    if not ALLOW_REENCODE_FOR_INCOMPATIBLE:
        return False

    ext = path.suffix.lstrip(".").lower()
    return not is_ext_compatible_with_active_profile(ext)


def build_ffmpeg_command(
    source: Path,
    target: Path,
    target_ext: str,
) -> list[str]:
    """
    Baut einen ffmpeg-Befehl für die Audio-Konvertierung.

    Aktuell:
    - AIFF als bevorzugtes HQ-Format (pcm_s16le, 44.1 kHz, Stereo)
    - Keine Lautstärke-Normalisierung, kein weiteres Processing.
    """
    target_ext = target_ext.lower()

    # Wir könnten später pro Format unterschiedliche Parameter setzen.
    if target_ext in ("aiff", "aif"):
        # Lossless PCM, 16 Bit, 44.1 kHz, Stereo – DJ- und DAW-tauglich
        return [
            "ffmpeg",
            "-y",  # überschreiben ohne Rückfrage
            "-i",
            str(source),
            "-vn",  # kein Video
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(target),
        ]

    if target_ext in ("wav",):
        # Ähnlicher Ansatz, falls später WAV gewünscht ist
        return [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(target),
        ]

    # Fallback: copy (für zukünftige Szenarien) – aktuell eher theoretisch
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-vn",
        "-acodec",
        "copy",
        str(target),
    ]


def reencode_if_needed(downloaded: Path) -> Optional[Path]:
    """
    Führt – falls nötig und erlaubt – einen Reencode der Datei durch.

    Ablauf:
    - Wenn kein Reencode nötig -> None
    - Wenn nötig:
        - Zielendung aus PREFERRED_HIGH_QUALITY_TARGET (z. B. 'aiff')
        - ffmpeg-Aufruf
        - bei Erfolg: optional Quell-File löschen
        - Rückgabe: Pfad zur neuen Datei
    """
    if not downloaded.exists():
        return None

    if not should_reencode_file(downloaded):
        return None

    target_ext = PREFERRED_HIGH_QUALITY_TARGET.lower().lstrip(".")
    target_path = downloaded.with_suffix(f".{target_ext}")

    cmd = build_ffmpeg_command(downloaded, target_path, target_ext)

    print(
        f"[REENCODE] Starte HQ-Reencode für: {downloaded.name} "
        f"-> {target_path.name}"
    )
    print(f"[REENCODE] ffmpeg: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(
            "[REENCODE-ERROR] ffmpeg wurde nicht gefunden. "
            "Ist es im PATH installiert?"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        print(f"[REENCODE-ERROR] Unerwarteter Fehler beim Reencode: {exc}")
        return None

    if result.returncode != 0:
        print(
            f"[REENCODE-ERROR] ffmpeg Rückgabecode {result.returncode} "
            f"für Datei: {downloaded.name}"
        )
        if result.stderr:
            print("[REENCODE-ERROR] ffmpeg stderr:")
            print(result.stderr.strip())
        return None

    print(f"[REENCODE-OK] HQ-Datei erzeugt: {target_path.name}")

    if REMOVE_SOURCE_AFTER_REENCODE:
        try:
            downloaded.unlink()
            print(f"[REENCODE] Quell-Datei entfernt: {downloaded.name}")
        except Exception as exc:  # noqa: BLE001
            print(
                f"[REENCODE-WARN] Konnte Quell-Datei nicht löschen: "
                f"{downloaded} ({exc})"
            )

    return target_path
