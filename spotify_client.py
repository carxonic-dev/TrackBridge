import base64
from typing import Optional

import requests

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyAuthError(Exception):
    """Fehler bei der Spotify-Authentifizierung."""


def get_access_token() -> str:
    """
    Holt ein Access-Token via Client-Credentials-Flow.
    Wirft SpotifyAuthError, wenn Env-Variablen fehlen oder keine Antwort kommt.
    """
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise SpotifyAuthError(
            "SPOTIFY_CLIENT_ID oder SPOTIFY_CLIENT_SECRET ist nicht gesetzt. "
            "Bitte .env prüfen."
        )

    auth_bytes = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("utf-8")
    b64_auth = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    resp = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
    resp.raise_for_status()

    payload = resp.json()
    token: Optional[str] = payload.get("access_token")

    if not token:
        raise SpotifyAuthError("Kein access_token in der Spotify-Antwort gefunden.")

    return token
