"""
tagging.py

Zentrale Tagging-Routine für spotify_2_yt-dlp.

- Gemeinsame Metadaten-Pipeline auf Basis der Extended-JSON-Daten.
- Format-spezifische Implementierungen für:
  - M4A / MP4 (AAC)
  - MP3 (ID3)
  - AIFF (ID3 im AIFF-Container)

Grundprinzip:
- Es werden nur Felder geschrieben, für die wir sinnvolle Werte haben.
- Keine Platzhalter wie "UNKNOWN" o. Ä.
"""

from __future__ import annotations

# pyright: reportMissingImports=false, reportPrivateImportUsage=false

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mutagen-Import (optional, defensiv)
# ---------------------------------------------------------------------------

try:
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.easyid3 import EasyID3
    from mutagen import id3 as mutagen_id3  # type: ignore[import]
    from mutagen.id3 import ID3, APIC, ID3NoHeaderError  # type: ignore[import]
except ImportError:  # pragma: no cover - wird zur Laufzeit abgefangen
    MP4 = None  # type: ignore[assignment]
    MP4Cover = None  # type: ignore[assignment]
    EasyID3 = None  # type: ignore[assignment]
    ID3 = None  # type: ignore[assignment]
    APIC = None  # type: ignore[assignment]
    ID3NoHeaderError = Exception  # type: ignore[assignment]
    mutagen_id3 = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Datenstruktur für Tags
# ---------------------------------------------------------------------------


@dataclass
class TrackTagData:
    """
    Repräsentiert die Metadaten, die wir in eine Audio-Datei schreiben wollen.

    Alle Felder sind optional, damit wir mit unvollständigen Daten arbeiten
    können, ohne das Tagging komplett zu blockieren.
    """

    title: Optional[str] = None
    artists: list[str] | None = None
    album: Optional[str] = None
    album_artist: Optional[str] = None
    track_number: Optional[int] = None
    track_total: Optional[int] = None
    disc_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    bpm: Optional[float] = None
    musical_key: Optional[str] = None
    comment: Optional[str] = None
    spotify_url: Optional[str] = None
    cover_image_bytes: Optional[bytes] = None
    cover_mime_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_tags_to_file(audio_path: Path, meta: Mapping[str, Any]) -> None:
    """
    Wendet Metadaten auf eine Audio-Datei an.

    :param audio_path: Ziel-Datei (bereits von yt-dlp heruntergeladen).
    :param meta: Track-Metadaten aus der Extended-JSON-Struktur.
    """
    if not audio_path.exists():
        logger.warning("Tagging übersprungen - Datei nicht gefunden: %s", audio_path)
        return

    if MP4 is None or EasyID3 is None or ID3 is None:
        logger.warning(
            "Mutagen nicht verfügbar - Tagging wird übersprungen. "
            "Bitte 'mutagen' in der venv installieren."
        )
        return

    tag_data = _extract_tag_data(meta)

    suffix = audio_path.suffix.lower()
    try:
        if suffix == ".m4a":
            _tag_m4a(audio_path, tag_data)
        elif suffix == ".mp3":
            _tag_mp3(audio_path, tag_data)
        elif suffix in (".aif", ".aiff"):
            _tag_aiff(audio_path, tag_data)
        else:
            logger.info(
                "Kein Tagging für dieses Format implementiert: %s", audio_path.suffix
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fehler beim Tagging von %s: %s", audio_path, exc)


# ---------------------------------------------------------------------------
# Gemeinsame Metadaten-Aufbereitung
# ---------------------------------------------------------------------------

def _extract_tag_data(meta: Mapping[str, Any]) -> TrackTagData:
    """
    Wandelt das Metadaten-Dict aus der Extended-JSON in eine TrackTagData-Struktur.

    Erwartete Keys (alle optional):
    - title
    - primary_artist
    - all_artists / artists (Liste von Namen)
    - album_name / album
    - album_artist
    - track_number
    - total_tracks / album_total_tracks
    - disc_number
    - release_year / release_date
    - genre / main_genre
    - bpm
    - key_label / musical_key
    - spotify_url
    """

    title = cleanup_str(meta.get("title"))
    primary_artist = cleanup_str(meta.get("primary_artist"))

    album_name = cleanup_str(meta.get("album_name") or meta.get("album"))
    album_artist = cleanup_str(meta.get("album_artist") or primary_artist)
    spotify_url = cleanup_str(meta.get("spotify_url"))

    # Rich-Genre: bevorzugt genres_combined, dann primary_genre, dann alte Felder
    genres_combined = meta.get("genres_combined")
    primary_genre = cleanup_str(meta.get("primary_genre"))

    genre: Optional[str] = None

    if isinstance(genres_combined, list) and genres_combined:
        cleaned_genres: list[str] = []
        for g in genres_combined:
            s = cleanup_str(g)
            if s:
                cleaned_genres.append(s)

        if cleaned_genres:
            # Rich-Mode: mehrere Genres mit Semikolon trennen
            genre = "; ".join(cleaned_genres)
    elif primary_genre:
        genre = primary_genre
    else:
        genre = cleanup_str(meta.get("genre") or meta.get("main_genre"))


    # Künstlerliste: "all_artists" bevorzugen, sonst "artists"
    artists_raw = meta.get("all_artists")
    if artists_raw is None:
        artists_raw = meta.get("artists", [])

    artists_list: list[str] = []
    if isinstance(artists_raw, list):
        tmp = [cleanup_str(a) for a in artists_raw if isinstance(a, str)]
        artists_list = [a for a in tmp if a]  # None & leer raus
    elif primary_artist:
        artists_list = [primary_artist]

    # Numerische Felder defensiv parsen
    def _to_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    track_number = _to_int(meta.get("track_number"))
    track_total = _to_int(meta.get("total_tracks") or meta.get("album_total_tracks"))
    disc_number = _to_int(meta.get("disc_number"))

    # Jahr: zuerst "release_year", sonst aus "release_date" (YYYY-MM-DD) ableiten
    release_year_value: Any = meta.get("release_year")
    if release_year_value is None:
        release_date = meta.get("release_date")
        if isinstance(release_date, str) and release_date:
            release_year_value = release_date[:4]

    year = _to_int(release_year_value)

    bpm = _to_float(meta.get("bpm"))
    musical_key = cleanup_str(meta.get("key_label") or meta.get("musical_key"))

    # Kommentar - nur wenn wir wirklich Infos haben
    comment_parts: list[str] = []
    # Spotify-URL kommt NICHT mehr in die Datei, nur in die Registry
    if bpm is not None:
        comment_parts.append(f"BPM: {bpm:g}")
    if musical_key:
        comment_parts.append(f"Key: {musical_key}")
    comment = " | ".join(comment_parts) if comment_parts else None

    # Cover-Bytes sind aktuell noch nicht aus der JSON befüllt - Platzhalter
    cover_bytes: Optional[bytes] = None
    cover_mime: Optional[str] = None

    return TrackTagData(
        title=title,
        artists=artists_list or None,
        album=album_name,
        album_artist=album_artist,
        track_number=track_number,
        track_total=track_total,
        disc_number=disc_number,
        year=year,
        genre=genre,
        bpm=bpm,
        musical_key=musical_key,
        comment=comment,
        spotify_url=spotify_url,
        cover_image_bytes=cover_bytes,
        cover_mime_type=cover_mime,
    )


def cleanup_str(value: Any) -> Optional[str]:
    """
    Wandelt einen Wert in einen bereinigten String um.

    - Nur echte Strings werden akzeptiert.
    - Leading/Trailing-Whitespace wird entfernt.
    - Leere Strings → None.
    """
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _has_text(value: Optional[str]) -> bool:
    """Hilfsfunktion: True nur bei nicht-leerem Text."""
    return bool(value and value.strip())


# ---------------------------------------------------------------------------
# Format-spezifische Implementierungen
# ---------------------------------------------------------------------------


def _tag_m4a(path: Path, data: TrackTagData) -> None:
    """
    Schreibt Metadaten in eine M4A/MP4-Datei.
    """
    assert MP4 is not None  # nur für Typchecker
    audio = MP4(path)

    if _has_text(data.title):
        audio["\xa9nam"] = [data.title]  # type: ignore[list-item]
    if data.artists:
        audio["\xa9ART"] = [", ".join(data.artists)]  # type: ignore[list-item]
    if _has_text(data.album):
        audio["\xa9alb"] = [data.album]  # type: ignore[list-item]
    if _has_text(data.album_artist):
        audio["aART"] = [data.album_artist]  # type: ignore[list-item]
    if _has_text(data.genre):
        audio["\xa9gen"] = [data.genre]  # type: ignore[list-item]
    if data.year is not None:
        audio["\xa9day"] = [str(data.year)]  # type: ignore[list-item]

    # Tracknummer (Track, Total)
    if data.track_number is not None:
        track_total = data.track_total or 0
        audio["trkn"] = [(data.track_number, track_total)]  # type: ignore[list-item]

    # Disknummer
    if data.disc_number is not None:
        audio["disk"] = [(data.disc_number, 0)]  # type: ignore[list-item]

    # BPM
    if data.bpm is not None:
        audio["tmpo"] = [int(round(data.bpm))]  # type: ignore[list-item]

    # Key - eigenes Atom, viele Player lesen das
    if _has_text(data.musical_key):
        audio["----:com.apple.iTunes:KEY"] = [  # type: ignore[index]
            data.musical_key.encode("utf-8")  # type: ignore[arg-type]
        ]

    # Kommentar
    if _has_text(data.comment):
        audio["\xa9cmt"] = [data.comment]  # type: ignore[list-item]

    # Cover optional - vorbereitet für später
    if (
        data.cover_image_bytes
        and data.cover_mime_type
        and MP4Cover is not None  # type: ignore[truthy-function]
    ):
        covr = MP4Cover(data.cover_image_bytes, imageformat=MP4Cover.FORMAT_JPEG)
        audio["covr"] = [covr]  # type: ignore[list-item]

    audio.save()
    logger.info("Tags in M4A geschrieben: %s", path)


def _tag_mp3(path: Path, data: TrackTagData) -> None:
    """
    Schreibt Metadaten in eine MP3-Datei (EasyID3 + optional Cover über ID3).
    """
    assert EasyID3 is not None  # nur für Typchecker

    try:
        audio = EasyID3(path)
    except ID3NoHeaderError:  # type: ignore[misc]
        # Datei hat noch keine ID3-Tags - neu initialisieren
        audio = EasyID3()
        audio.save(path)  # Header anlegen
        audio = EasyID3(path)

    if _has_text(data.title):
        audio["title"] = data.title  # type: ignore[index]
    if data.artists:
        audio["artist"] = ", ".join(data.artists)  # type: ignore[index]
    if _has_text(data.album):
        audio["album"] = data.album  # type: ignore[index]
    if _has_text(data.album_artist):
        audio["albumartist"] = data.album_artist  # type: ignore[index]
    if _has_text(data.genre):
        audio["genre"] = data.genre  # type: ignore[index]
    if data.year is not None:
        audio["date"] = str(data.year)  # type: ignore[index]

    if data.track_number is not None:
        if data.track_total:
            audio["tracknumber"] = f"{data.track_number}/{data.track_total}"  # type: ignore[index]
        else:
            audio["tracknumber"] = str(data.track_number)  # type: ignore[index]

    if data.bpm is not None:
        audio["bpm"] = f"{data.bpm:g}"  # type: ignore[index]

    if _has_text(data.musical_key):
        audio["initialkey"] = data.musical_key  # type: ignore[index]

    if _has_text(data.comment):
        audio["comment"] = data.comment  # type: ignore[index]

    audio.save()
    logger.info("Tags in MP3 geschrieben: %s", path)

    # Cover-Art bei MP3 separat über ID3-Frames
    if (
        data.cover_image_bytes
        and data.cover_mime_type
        and ID3 is not None
        and APIC is not None
    ):
        id3 = ID3(path)
        id3.add(
            APIC(
                encoding=3,
                mime=data.cover_mime_type,
                type=3,
                desc="Cover",
                data=data.cover_image_bytes,
            )
        )
        id3.save(v2_version=3)
        logger.info("Cover in MP3 eingebettet: %s", path)


def _tag_aiff(path: Path, data: TrackTagData) -> None:
    """
    Schreibt Metadaten in eine AIFF-Datei (ID3-Tags im AIFF-Container).
    """
    if ID3 is None or mutagen_id3 is None:
        logger.warning(
            "ID3-Unterstützung nicht verfügbar – AIFF-Tagging übersprungen."
        )
        return

    try:
        id3 = ID3(path)
    except ID3NoHeaderError:  # type: ignore[misc]
        id3 = ID3()

    # Bequeme Kurzformen für Frames
    TIT2 = mutagen_id3.TIT2
    TPE1 = mutagen_id3.TPE1
    TALB = mutagen_id3.TALB
    TPE2 = mutagen_id3.TPE2
    TCON = mutagen_id3.TCON
    TDRC = mutagen_id3.TDRC
    TRCK = mutagen_id3.TRCK
    COMM = mutagen_id3.COMM
    TBPM = mutagen_id3.TBPM
    TKEY = mutagen_id3.TKEY

    if _has_text(data.title):
        id3["TIT2"] = TIT2(encoding=3, text=data.title)
    if data.artists:
        id3["TPE1"] = TPE1(encoding=3, text=", ".join(data.artists))
    if _has_text(data.album):
        id3["TALB"] = TALB(encoding=3, text=data.album)
    if _has_text(data.album_artist):
        id3["TPE2"] = TPE2(encoding=3, text=data.album_artist)
    if _has_text(data.genre):
        id3["TCON"] = TCON(encoding=3, text=data.genre)
    if data.year is not None:
        id3["TDRC"] = TDRC(encoding=3, text=str(data.year))

    if data.track_number is not None:
        track_text = str(data.track_number)
        if data.track_total:
            track_text = f"{data.track_number}/{data.track_total}"
        id3["TRCK"] = TRCK(encoding=3, text=track_text)

    if data.bpm is not None:
        id3["TBPM"] = TBPM(encoding=3, text=f"{data.bpm:g}")
    if _has_text(data.musical_key):
        id3["TKEY"] = TKEY(encoding=3, text=data.musical_key)

    if _has_text(data.comment):
        id3["COMM"] = COMM(
            encoding=3,
            lang="eng",
            desc="",
            text=data.comment,
        )

    if data.cover_image_bytes and data.cover_mime_type and APIC is not None:
        id3.add(
            APIC(
                encoding=3,
                mime=data.cover_mime_type,
                type=3,
                desc="Cover",
                data=data.cover_image_bytes,
            )
        )

    id3.save(path)
    logger.info("Tags in AIFF geschrieben: %s", path)
