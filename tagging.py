"""
# tagging.py
from pathlib import Path
from typing import Mapping, Any

from mutagen.mp4 import MP4, MP4Cover
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

def apply_tags_to_file(audio_path: Path, meta: Mapping[str, Any]) -> None:
    ext = audio_path.suffix.lower()

    if ext == ".m4a":
        _tag_m4a(audio_path, meta)
    elif ext == ".mp3":
        _tag_mp3(audio_path, meta)
    elif ext in {".aif", ".aiff"}:
        _tag_aiff(audio_path, meta)
    else:
        # für exotische Formate ggf. später nachrüsten
        return
"""
