from __future__ import annotations

from pathlib import Path
from typing import Optional

from config import DJ_COMPATIBILITY_PROFILE
from config import DENY_WAV_COMPLETELY

# Bekannte, CDJ-2000NXS2-kompatible Endungen (Container/Codecs)
CDJ2000NXS2_COMPATIBLE_EXTENSIONS = {
    "aiff", "aif",  # bevorzugt
    "alac",         # lossless, Apple
    "flac",         # lossless
    "m4a", "aac",   # AAC
    "mp3",          # fallback
    "wav",          # allerletzter fallback – tags sehr eingeschränkt
}

if DENY_WAV_COMPLETELY:
    CDJ2000NXS2_COMPATIBLE_EXTENSIONS.discard("wav")

def is_cdj2000nxs2_compatible(ext: str) -> bool:
    """
    Prüft, ob eine Dateiendung für CDJ-2000NXS2 als kompatibel gilt.
    """
    return ext.lower() in CDJ2000NXS2_COMPATIBLE_EXTENSIONS


def is_ext_compatible_with_active_profile(ext: str) -> bool:
    """
    Prüft eine Endung gegen das in der Config gesetzte DJ-Profil.

    - "cdj2000nxs2" -> nutzt is_cdj2000nxs2_compatible
    - "none" oder unbekannt -> immer True (kein Check)
    """
    profile = (DJ_COMPATIBILITY_PROFILE or "").lower()

    if profile == "cdj2000nxs2":
        return is_cdj2000nxs2_compatible(ext)

    if profile in ("", "none"):
        # Kein aktives Profil -> nichts blockieren
        return True

    # Fallback: bis wir weitere Profile definieren, nichts hart ablehnen
    return True
