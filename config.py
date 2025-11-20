from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict, List
import os
from dotenv import load_dotenv



# ---------------------------------------------------------------------------
# Basis-Konfiguration / Pfade
# ---------------------------------------------------------------------------

# Basisverzeichnis = Projektordner
BASE_DIR = Path(__file__).resolve().parent

# Pfad zur config.json
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config() -> Dict[str, Any]:
    """
    Lädt die Konfiguration aus config.json.

    Schlägt fehl, wenn die Datei nicht existiert oder kein gültiges JSON ist.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    return data


# Globale CONFIG, die du im restlichen Modul nutzen kannst
CONFIG: Dict[str, Any] = _load_config()


# ---------------------------------------------------------------------------
# Spotify-Einstellungen
# ---------------------------------------------------------------------------

SPOTIFY_CLIENT_ID: str = CONFIG.get("SpotifyClientId", "")
SPOTIFY_CLIENT_SECRET: str = CONFIG.get("SpotifyClientSecret", "")
SPOTIFY_TOKEN_URL: str = CONFIG.get(
    "SpotifyTokenUrl",
    "https://accounts.spotify.com/api/token",
)
SPOTIFY_API_BASE_URL: str = CONFIG.get(
    "SpotifyApiBaseUrl",
    "https://api.spotify.com/v1",
)


# ---------------------------------------------------------------------------
# Output / Download / Audio-Formate
# ---------------------------------------------------------------------------

OUTPUT_DIRECTORY: Path = Path(
    CONFIG.get("OutputDirectory", BASE_DIR / "output")
).resolve()

AUDIO_PREFERRED_FORMATS = CONFIG.get("AudioPreferredFormats", ["m4a", "mp3"])

MAX_PARALLEL_DOWNLOADS: int = int(CONFIG.get("MaxParallelDownloads", 2))
MAX_RETRIES_PER_JOB: int = int(CONFIG.get("MaxRetriesPerJob", 2))

SKIP_EXISTING_FILES: bool = bool(CONFIG.get("SkipExistingFiles", True))

DJ_COMPATIBILITY_PROFILE: str | None = CONFIG.get("DjCompatibilityProfile")
ALLOW_REENCODE_FOR_INCOMPATIBLE: bool = bool(
    CONFIG.get("AllowReencodeForIncompatible", True)
)

REGISTRY_ENABLED: bool = bool(CONFIG.get("RegistryEnabled", False))



# --- .env laden --------------------------------------------------------------

env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)

SPOTIFY_CLIENT_ID: str = (
    os.getenv("SPOTIFY_CLIENT_ID")
    or CONFIG.get("SpotifyClientId")
    or ""
).strip()

SPOTIFY_CLIENT_SECRET: str = (
    os.getenv("SPOTIFY_CLIENT_SECRET")
    or CONFIG.get("SpotifyClientSecret")
    or ""
).strip()


# --- config.json laden -------------------------------------------------------

CONFIG_JSON = BASE_DIR / "config.json"

if not CONFIG_JSON.exists():
    raise FileNotFoundError(f"config.json fehlt: {CONFIG_JSON}")

with CONFIG_JSON.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# Basis-Einstellungen
_raw_output_dir = CONFIG.get("OutputDirectory")

if _raw_output_dir is None:
    # Fallback auf Standard-Ordner im Projekt
    OUTPUT_DIRECTORY: Path = (BASE_DIR / "output").resolve()
else:
    OUTPUT_DIRECTORY = Path(str(_raw_output_dir)).expanduser().resolve()


DEFAULT_FORMAT = CONFIG.get("DefaultFormat", "json")

# yt-dlp-bezogene Settings
YTDLP_TEXTFILE_PATTERN = CONFIG.get(
    "YTDLP_TextFilePattern",
    "spotify_{playlist_id}_yt-dlp.txt",
)

AUDIO_PREFERRED_FORMATS = CONFIG.get(
    "AudioPreferredFormats",
    ["m4a", "mp3", "aac", "opus", "flac"],
)


MAX_PARALLEL_DOWNLOADS = int(CONFIG.get("MaxParallelDownloads", 2))

# Audio-Dateinamen & Pfadlängen
AUDIO_OUTPUT_EXTENSION = CONFIG.get("AudioOutputExtension", "m4a")
AUDIO_FILENAME_TEMPLATE = CONFIG.get(
    "AudioFilenameTemplate",
    "{track_number_padded} {title_sanitized}",
)
MAX_FILENAME_LENGTH = int(CONFIG.get("MaxFilenameLength", 80))

# Download-Retries
DOWNLOAD_MAX_RETRIES = int(CONFIG.get("DownloadMaxRetries", 2))

"""
# Timeout-Einstellungen (für yt-dlp)
YTDLP_SOCKET_TIMEOUT = int(CONFIG.get("YTDLP_SocketTimeout", 15))
YTDLP_READ_TIMEOUT = int(CONFIG.get("YTDLP_ReadTimeout", 30))
YTDLP_CONNECT_TIMEOUT = int(CONFIG.get("YTDLP_ConnectTimeout", 15))
# Proxy-Einstellungen
YTDLP_HTTP_PROXY = CONFIG.get("YTDLP_HttpProxy", None)
YTDLP_HTTPS_PROXY = CONFIG.get("YTDLP_HttpsProxy", None)
YTDLP_PROXY = CONFIG.get("YTDLP_Proxy", None)
"""

SKIP_EXISTING_FILES = bool(CONFIG.get("SkipExistingFiles", True))

KNOWN_AUDIO_EXTENSIONS: list[str] = CONFIG.get(
    "KnownAudioExtensions",
    [
        "m4a",
        "aac",
        "mp3",
        "flac",
        "alac",
        "aiff",
        "aif",
        "wav",
        "webm",
        "opus",
    ],
)

DJ_COMPATIBILITY_PROFILE = CONFIG.get(
    "DJCompatibilityProfile",
    "none"
)

DJ_WARN_ON_INCOMPATIBLE = bool(
    CONFIG.get("DJWarnOnIncompatible", True))

ALLOW_REENCODE_FOR_INCOMPATIBLE = bool(
    CONFIG.get("AllowReencodeForIncompatible", False)
)
PREFERRED_HIGH_QUALITY_TARGET = CONFIG.get(
    "PreferredHighQualityTarget",
    "aiff",
)

REMOVE_SOURCE_AFTER_REENCODE = bool(
    CONFIG.get("RemoveSourceAfterReencode", True)
)

DENY_WAV_COMPLETELY = bool(
    CONFIG.get("DenyWavCompletely", False)
)
