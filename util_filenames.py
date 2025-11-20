from __future__ import annotations

import re
from pathlib import Path

from config import (
    AUDIO_FILENAME_TEMPLATE,
    AUDIO_OUTPUT_EXTENSION,
    MAX_FILENAME_LENGTH,
)


INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\n\r\t]+')


def sanitize_title(title: str) -> str:
    """
    Entfernt für Dateinamen unzulässige Zeichen und trimmt Leerzeichen.
    """
    cleaned = INVALID_CHARS_PATTERN.sub(" ", title)
    cleaned = " ".join(cleaned.split())
    return cleaned


def shorten_filename_stem(stem: str, max_length: int) -> str:
    """
    Kürzt den Dateinamen-Stem auf max_length Zeichen.
    """
    if len(stem) <= max_length:
        return stem
    return stem[: max_length].rstrip()


def format_track_number(track_number: int | None) -> str:
    """
    Formatiert Track-Nummer zweistellig (03, 12). Fällt auf '00' zurück, wenn None/0.
    """
    if not track_number or track_number < 0:
        return "00"
    return f"{track_number:02d}"


def build_audio_filename(title: str, track_number: int | None = None) -> str:
    """
    Erzeugt einen Dateinamen wie '03 Title.m4a' auf Basis der Config.
    """
    title_sanitized = sanitize_title(title)
    track_number_padded = format_track_number(track_number)

    stem = AUDIO_FILENAME_TEMPLATE.format(
        track_number_padded=track_number_padded,
        title_sanitized=title_sanitized,
    )

    stem_short = shorten_filename_stem(stem, MAX_FILENAME_LENGTH)
    filename = f"{stem_short}.{AUDIO_OUTPUT_EXTENSION.lstrip('.')}"
    return filename


def build_audio_path(base_dir: Path, title: str, track_number: int | None = None) -> Path:
    """
    Hilfsfunktion für später: erzeugt den vollständigen Pfad für eine Audiodatei.
    """
    filename = build_audio_filename(title, track_number)
    return base_dir / filename
