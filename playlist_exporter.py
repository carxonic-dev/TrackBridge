from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

from spotify_client import get_access_token
from config import OUTPUT_DIRECTORY, YTDLP_TEXTFILE_PATTERN
from util_filenames import build_audio_filename

SPOTIFY_PLAYLIST_URL = "https://api.spotify.com/v1/playlists/{playlist_id}"
SPOTIFY_AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features"


# ---------------------------------------------------------------------------
# Low-Level: Playlist & Audio-Features holen
# ---------------------------------------------------------------------------

def _fetch_playlist_full(access_token: str, playlist_id: str) -> Dict[str, Any]:
    """
    Holt die komplette Playlist-Struktur inkl. Metadaten und Tracks.
    Wir paginieren über 'tracks.next'.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = SPOTIFY_PLAYLIST_URL.format(playlist_id=playlist_id)

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    playlist = resp.json()

    tracks: List[Dict[str, Any]] = []
    track_page = playlist.get("tracks") or {}
    while True:
        items = track_page.get("items") or []
        for item in items:
            track = item.get("track") or {}
            if track:
                tracks.append(track)

        next_url = track_page.get("next")
        if not next_url:
            break

        resp = requests.get(next_url, headers=headers, timeout=10)
        resp.raise_for_status()
        track_page = resp.json()

    playlist["__all_tracks__"] = tracks
    return playlist


def _fetch_audio_features(
    access_token: str,
    track_ids: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Holt Audio Features (u. a. BPM, Key, Mode) für eine Liste von Track-IDs.

    Wenn Spotify 403 liefert (z. B. Endpoint nicht für diesen Token verfügbar),
    geben wir ein leeres Dict zurück und lassen den Rest weiterlaufen.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    features_by_id: Dict[str, Dict[str, Any]] = {}

    if not track_ids:
        return features_by_id

    chunk_size = 100
    for i in range(0, len(track_ids), chunk_size):
        chunk = track_ids[i : i + chunk_size]
        if not chunk:
            continue

        params = {"ids": ",".join(chunk)}
        try:
            resp = requests.get(
                SPOTIFY_AUDIO_FEATURES_URL,
                headers=headers,
                params=params,
                timeout=10,
            )
            if resp.status_code == 403:
                # Kein Zugriff auf Audio-Features -> wir arbeiten ohne BPM/Key
                print(
                    "[WARN] Audio-Features-API liefert 403 Forbidden – "
                    "BPM/Key werden für diese Playlist nicht gesetzt."
                )
                return {}
            resp.raise_for_status()
        except requests.HTTPError as exc:
            print(f"[WARN] Fehler beim Laden von Audio-Features: {exc}")
            return {}

        data = resp.json()
        for feat in data.get("audio_features", []):
            if not feat:
                continue
            tid = feat.get("id")
            if tid:
                features_by_id[tid] = feat

    return features_by_id


# ---------------------------------------------------------------------------
# Datentransformation: Extended-Track-Objekte
# ---------------------------------------------------------------------------

def _build_extended_tracks(
    raw_tracks: List[Dict[str, Any]],
    audio_features_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Baut aus rohen Spotify-Trackdaten + Audio Features eine Extended-Datenstruktur,
    die als Grundlage für ID3-Tagging, Dateinamen, Queue etc. dient.
    """
    extended: List[Dict[str, Any]] = []

    for t in raw_tracks:
        track_id = t.get("id")
        name = t.get("name") or ""
        artists = t.get("artists") or []
        album = t.get("album") or {}

        artist_names = [a.get("name", "") for a in artists if a]
        primary_artist = artist_names[0] if artist_names else ""

        album_name = album.get("name") or ""
        album_artists = album.get("artists") or []
        album_artist_names = [a.get("name", "") for a in album_artists if a]
        album_primary_artist = album_artist_names[0] if album_artist_names else primary_artist

        release_date = album.get("release_date")
        track_number = t.get("track_number")
        disc_number = t.get("disc_number")
        is_explicit = bool(t.get("explicit"))
        duration_ms = t.get("duration_ms")
        external_ids = t.get("external_ids") or {}
        isrc = external_ids.get("isrc")

        images = album.get("images") or []
        cover_url = images[0].get("url") if images else None

        spotify_url = (t.get("external_urls") or {}).get("spotify")

        audio_feat = audio_features_by_id.get(track_id or "", {}) if track_id else {}
        bpm = audio_feat.get("tempo")
        key_index = audio_feat.get("key")
        mode_index = audio_feat.get("mode")
        time_signature = audio_feat.get("time_signature")

        filename = build_audio_filename(name, track_number)

        extended.append(
            {
                # Identifikation
                "spotify_track_id": track_id,
                "spotify_url": spotify_url,

                # Titel / Künstler / Album
                "title": name,
                "artists": artist_names,
                "primary_artist": primary_artist,
                "album": album_name,
                "album_artist": album_primary_artist,

                # Veröffentlichung / Nummerierung
                "release_date": release_date,
                "track_number": track_number,
                "disc_number": disc_number,
                "explicit": is_explicit,
                "duration_ms": duration_ms,
                "isrc": isrc,

                # Artwork
                "cover_url": cover_url,

                # Audio-Features (Rohdaten + Ableitungen)
                "bpm": bpm,
                "key_index": key_index,
                "mode_index": mode_index,
                "time_signature": time_signature,
                "audio_features": audio_feat,
                "key_notation": None,  # Platzhalter für z. B. "F#m"
                "key_camelot": None,   # Platzhalter für z. B. "11A"

                # Dateinamen-Vorschlag (ohne Pfad)
                "suggested_filename": filename,
            }
        )

    return extended


def fetch_playlist_tracks_extended(
    access_token: str,
    playlist_id: str,
) -> Dict[str, Any]:
    """
    High-Level: holt Playlist-Metadaten + Tracks + Audio-Features und
    gibt eine Struktur { playlist: {...}, tracks: [...] } zurück.
    """
    playlist_full = _fetch_playlist_full(access_token, playlist_id)
    raw_tracks: List[Dict[str, Any]] = playlist_full.pop("__all_tracks__", [])

    track_ids: List[str] = [
        str(t["id"]) for t in raw_tracks if t.get("id")
    ]

    audio_features_by_id = _fetch_audio_features(access_token, track_ids)
    extended_tracks = _build_extended_tracks(raw_tracks, audio_features_by_id)

    # Playlist-Metadaten extrahieren
    playlist_meta = {
        "playlist_id": playlist_id,
        "name": playlist_full.get("name"),
        "description": playlist_full.get("description"),
        "owner": (playlist_full.get("owner") or {}).get("display_name"),
        "spotify_url": (playlist_full.get("external_urls") or {}).get("spotify"),
        "snapshot_id": playlist_full.get("snapshot_id"),
        "total_tracks": len(extended_tracks),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "playlist": playlist_meta,
        "tracks": extended_tracks,
    }


# ---------------------------------------------------------------------------
# Exporte: JSON + yt-dlp-Textfile
# ---------------------------------------------------------------------------

def export_playlist_to_json(playlist_id: str, output_path: Path | None = None) -> Path:
    """
    Exportiert eine öffentliche Playlist als Extended-JSON-Datei
    mit Top-Level-Struktur { playlist: {...}, tracks: [...] }.
    """
    token = get_access_token()
    data = fetch_playlist_tracks_extended(token, playlist_id)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = OUTPUT_DIRECTORY / f"spotify_playlist_{playlist_id}.json"

    assert output_path is not None

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_path


def export_playlist_to_ytdlp_txt(
    playlist_id: str,
    output_path: Path | None = None,
) -> Path:
    """
    Erzeugt eine Textdatei mit Such-Queries für yt-dlp.
    Pro Zeile:
        ytsearch1:Artist - Title
    """
    token = get_access_token()
    data = fetch_playlist_tracks_extended(token, playlist_id)
    tracks: List[Dict[str, Any]] = data.get("tracks", [])

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        filename = YTDLP_TEXTFILE_PATTERN.format(playlist_id=playlist_id)
        output_path = OUTPUT_DIRECTORY / filename

    assert output_path is not None

    lines: List[str] = []

    for t in tracks:
        artist = (t.get("primary_artist") or "").strip()
        title = (t.get("title") or "").strip()

        if not artist and not title:
            continue

        query = f"{artist} - {title}" if artist and title else (artist or title)
        lines.append(f"ytsearch1:{query}")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
