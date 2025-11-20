from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from spotify_client import get_access_token, SpotifyAuthError


SPOTIFY_PLAYLIST_URL = "https://api.spotify.com/v1/playlists/4Bo5jqVdZTOQiXiY4PiiWC"


def fetch_playlist_tracks(access_token: str, playlist_id: str) -> list[dict[str, Any]]:
    """
    Holt alle Tracks einer öffentlichen Playlist über die Spotify Web API.

    Rückgabe: Liste von Dicts mit artist, title, spotify_url.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    url = SPOTIFY_PLAYLIST_URL.format(playlist_id=playlist_id)

    tracks: list[dict[str, Any]] = []

    params: dict[str, Any] = {
        # wir beschränken die Felder, damit die Antwort schlank bleibt
        "fields": "tracks.items(track(name,artists(name),external_urls)),tracks.next"
    }

    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("tracks", {}).get("items", [])
        for item in items:
            track = item.get("track") or {}
            name = track.get("name") or ""
            artists = track.get("artists") or []
            artist_names = ", ".join(a.get("name", "") for a in artists)
            link = (track.get("external_urls") or {}).get("spotify", "")

            tracks.append(
                {
                    "artist": artist_names,
                    "title": name,
                    "spotify_url": link,
                }
            )

        # nächste Seite
        next_url = data.get("tracks", {}).get("next")
        url = next_url
        params = None  # ab jetzt steckt alles in next-URL

    return tracks


def run_smoketest(playlist_id: str) -> None:
    """
    Führt den Smoketest aus:
    - Token holen
    - Playlist lesen
    - JSON-Datei schreiben
    """
    try:
        token = get_access_token()
    except SpotifyAuthError as exc:
        print(f"[SMOKETEST] SpotifyAuthError: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        print(f"[SMOKETEST] Unerwarteter Fehler beim Token holen: {exc}")
        return

    try:
        tracks = fetch_playlist_tracks(token, playlist_id)
    except Exception as exc:  # noqa: BLE001
        print(f"[SMOKETEST] Fehler beim Laden der Playlist: {exc}")
        return

    out_path = Path(f"smoketest_playlist_{playlist_id}.json")
    out_path.write_text(json.dumps(tracks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[SMOKETEST] Playlist-ID: {playlist_id}")
    print(f"[SMOKETEST] Anzahl Tracks: {len(tracks)}")
    print(f"[SMOKETEST] Ausgabe: {out_path.resolve()}")


if __name__ == "__main__":
    # 👉 HIER deine Test-Playlist-ID eintragen
    TEST_PLAYLIST_ID = "4Bo5jqVdZTOQiXiY4PiiWC"

    if TEST_PLAYLIST_ID == "DEINE_PLAYLIST_ID_HIER":
        print(
            "[SMOKETEST] Bitte in smoketest_playlist.py die Variable "
            "TEST_PLAYLIST_ID auf eine echte Spotify-Playlist-ID setzen."
        )
    else:
        run_smoketest(TEST_PLAYLIST_ID)
