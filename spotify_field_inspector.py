from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import requests  # nur für Album/Artist-Details

from spotify_client import get_access_token
from playlist_exporter import _fetch_playlist_full, _fetch_audio_features

SPOTIFY_ALBUM_URL = "https://api.spotify.com/v1/albums/{album_id}"
SPOTIFY_ARTIST_URL = "https://api.spotify.com/v1/artists/{artist_id}"


def inspect_playlist_fields(playlist_id: str, limit: int = 20, output: Path | None = None) -> None:
    """Analysiert die verfügbaren Felder für Track, Album, Artist und Audio-Features."""

    token = get_access_token()

    # 1) Komplette Playlist inkl. aller Track-Objekte holen
    playlist_full = _fetch_playlist_full(token, playlist_id)
    raw_tracks: List[Dict[str, Any]] = playlist_full.get("__all_tracks__", [])

    if not raw_tracks:
        print("Keine Tracks in Playlist gefunden.")
        return

    # Auf eine sinnvolle Menge begrenzen
    raw_tracks = raw_tracks[:limit]

    track_keys: Set[str] = set()
    album_keys_inline: Set[str] = set()
    artist_keys_inline: Set[str] = set()

    album_ids: Set[str] = set()
    artist_ids: Set[str] = set()
    track_ids: List[str] = []

    for t in raw_tracks:
        track_keys.update(t.keys())

        album = t.get("album") or {}
        album_keys_inline.update(album.keys())
        album_id = album.get("id")
        if album_id:
            album_ids.add(album_id)

        artists = t.get("artists") or []
        for a in artists:
            if not isinstance(a, dict):
                continue
            artist_keys_inline.update(a.keys())
            aid = a.get("id")
            if aid:
                artist_ids.add(aid)

        tid = t.get("id")
        if tid:
            track_ids.append(tid)

    # 2) Audio-Features zu diesen Tracks holen
    audio_features_by_id = _fetch_audio_features(token, track_ids)
    audio_feature_keys: Set[str] = set()
    for feat in audio_features_by_id.values():
        audio_feature_keys.update(feat.keys())

    # 3) Optional: zusätzliche Album-/Artist-Felder über Detail-Endpoints
    headers = {"Authorization": f"Bearer {token}"}
    album_keys_api: Set[str] = set()
    artist_keys_api: Set[str] = set()

    for album_id in list(album_ids)[:10]:
        resp = requests.get(
            SPOTIFY_ALBUM_URL.format(album_id=album_id),
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        album_data = resp.json()
        album_keys_api.update(album_data.keys())

    for artist_id in list(artist_ids)[:10]:
        resp = requests.get(
            SPOTIFY_ARTIST_URL.format(artist_id=artist_id),
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        artist_data = resp.json()
        artist_keys_api.update(artist_data.keys())

    result = {
        "playlist_id": playlist_id,
        "track_keys_inline": sorted(track_keys),
        "album_keys_inline": sorted(album_keys_inline),
        "artist_keys_inline": sorted(artist_keys_inline),
        "album_keys_api": sorted(album_keys_api),
        "artist_keys_api": sorted(artist_keys_api),
        "audio_feature_keys": sorted(audio_feature_keys),
    }

    # Ausgabe
    print("=== Track-Keys (inline in Playlist) ===")
    print(", ".join(result["track_keys_inline"]))
    print("\n=== Album-Keys (inline in Playlist) ===")
    print(", ".join(result["album_keys_inline"]))
    print("\n=== Artist-Keys (inline in Playlist) ===")
    print(", ".join(result["artist_keys_inline"]))
    print("\n=== Album-Keys (Album-API) ===")
    print(", ".join(result["album_keys_api"]))
    print("\n=== Artist-Keys (Artist-API) ===")
    print(", ".join(result["artist_keys_api"]))
    print("\n=== Audio-Feature-Keys ===")
    print(", ".join(result["audio_feature_keys"]))

    if output is not None:
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nDetail-Report gespeichert unter: {output}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect Spotify fields for a playlist.")
    parser.add_argument("playlist_id", help="Spotify Playlist-ID")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximale Anzahl Tracks für die Analyse (Default: 20)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optionaler JSON-Report-Pfad",
    )
    args = parser.parse_args()

    inspect_playlist_fields(args.playlist_id, limit=args.limit, output=args.output)
