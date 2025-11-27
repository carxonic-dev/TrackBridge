from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Pfad zur SQLite-Datenbank dynamisch relativ zum Projektordner
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "track_registry.db"


# ---------------------------------------------------------------------------
# Datamodel (Python-Seite)
# ---------------------------------------------------------------------------

@dataclass
class TrackInfo:
    """
    Repräsentiert die Basisinformationen eines Spotify-Tracks.

    Diese Struktur kann direkt aus den Extended-JSON-Daten befüllt werden.
    """
    spotify_track_id: str
    title: str
    primary_artist: str
    duration_ms: Optional[int] = None


@dataclass
class FileInfo:
    """
    Repräsentiert eine lokal vorhandene Datei zu einem Track.
    """
    id: int
    track_id: str
    absolute_path: Path
    format: str
    is_missing: bool


# ---------------------------------------------------------------------------
# SQLite-Helfer
# ---------------------------------------------------------------------------

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context-Manager für eine SQLite-Verbindung.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """
    Legt die benötigten Tabellen an, falls sie noch nicht existieren.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                spotify_track_id TEXT PRIMARY KEY,
                title            TEXT NOT NULL,
                primary_artist   TEXT NOT NULL,
                duration_ms      INTEGER,
                best_file_id     INTEGER,
                created_at       TEXT NOT NULL,
                last_seen_at     TEXT NOT NULL,
                reencode_status  TEXT,
                tagging_status   TEXT,
                FOREIGN KEY (best_file_id) REFERENCES files(id)
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id       TEXT NOT NULL,
                absolute_path  TEXT NOT NULL,
                format         TEXT NOT NULL,
                file_size      INTEGER,
                mtime          INTEGER,
                added_at       TEXT NOT NULL,
                last_seen_at   TEXT NOT NULL,
                is_missing     INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (track_id) REFERENCES tracks(spotify_track_id)
            );
            """
        )


# Beim Import einmal sicherstellen, dass die DB-Struktur vorhanden ist
init_db()


# ---------------------------------------------------------------------------
# Qualitätsbewertung von Formaten (für "best_file"-Logik)
# ---------------------------------------------------------------------------

FORMAT_QUALITY: dict[str, int] = {
    # Lossless, DJ-/DAW-tauglich
    "aiff": 100,
    "aif": 100,
    "flac": 95,
    "alac": 95,
    "wav": 90,

    # Gute, weit verbreitete lossy-Formate
    "m4a": 80,
    "aac": 78,
    "mp3": 70,

    # Problematische Formate aus DJ-Sicht
    "opus": 40,
    "webm": 35,
}


def _format_quality(ext: str) -> int:
    """
    Liefert einen groben Qualitäts-Score für eine Dateiendung.

    Unbekannte Endungen bekommen einen niedrigen Default-Wert.
    """
    return FORMAT_QUALITY.get(ext.lower(), 10)


# ---------------------------------------------------------------------------
# Track-Operationen
# ---------------------------------------------------------------------------

def upsert_track_basic(info: TrackInfo) -> None:
    """
    Fügt einen Track neu ein oder aktualisiert die Basisinformationen.

    - Erstellt den Track, falls nicht vorhanden.
    - Aktualisiert Titel/Artist/Duration, falls sich etwas geändert hat.
    - Aktualisiert immer das last_seen_at.
    """
    now = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT title, primary_artist, duration_ms
            FROM tracks
            WHERE spotify_track_id = ?;
            """,
            (info.spotify_track_id,),
        )
        row = cur.fetchone()

        if row is None:
            # Neuer Track
            cur.execute(
                """
                INSERT INTO tracks (
                    spotify_track_id,
                    title,
                    primary_artist,
                    duration_ms,
                    best_file_id,
                    created_at,
                    last_seen_at,
                    reencode_status,
                    tagging_status
                )
                VALUES (?, ?, ?, ?, NULL, ?, ?, NULL, NULL);
                """,
                (
                    info.spotify_track_id,
                    info.title,
                    info.primary_artist,
                    info.duration_ms,
                    now,
                    now,
                ),
            )
        else:
            # Existierender Track -> Basisdaten ggf. aktualisieren
            cur.execute(
                """
                UPDATE tracks
                SET title = ?,
                    primary_artist = ?,
                    duration_ms = ?,
                    last_seen_at = ?
                WHERE spotify_track_id = ?;
                """,
                (
                    info.title,
                    info.primary_artist,
                    info.duration_ms,
                    now,
                    info.spotify_track_id,
                ),
            )


def get_track(spotify_track_id: str) -> Optional[TrackInfo]:
    """
    Holt Basisinformationen zu einem Track aus der Registry.

    Gibt None zurück, wenn der Track nicht bekannt ist.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT spotify_track_id, title, primary_artist, duration_ms
            FROM tracks
            WHERE spotify_track_id = ?;
            """,
            (spotify_track_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return TrackInfo(
        spotify_track_id=row[0],
        title=row[1],
        primary_artist=row[2],
        duration_ms=row[3],
    )


# ---------------------------------------------------------------------------
# File-Operationen
# ---------------------------------------------------------------------------

def _insert_file_for_track(
    spotify_track_id: str,
    path: Path,
    fmt: str,
) -> int:
    """
    Legt einen neuen File-Datensatz für einen Track an und gibt die ID zurück.
    """
    now = datetime.utcnow().isoformat(timespec="seconds")
    stat = path.stat() if path.exists() else None

    file_size = stat.st_size if stat is not None else None
    mtime = int(stat.st_mtime) if stat is not None else 0

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO files (
                track_id,
                absolute_path,
                format,
                file_size,
                mtime,
                added_at,
                last_seen_at,
                is_missing
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0);
            """,
            (
                spotify_track_id,
                str(path),
                fmt.lower(),
                file_size,
                mtime,
                now,
                now,
            ),
        )
    file_id = cur.lastrowid
    assert file_id is not None  # Für Pylance & für dich als Sanity-Check
    return int(file_id)



def _get_best_file_row(spotify_track_id: str) -> Optional[tuple]:
    """
    Liefert (id, absolute_path, format) für die aktuell als 'best' markierte Datei.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT f.id, f.absolute_path, f.format
            FROM tracks t
            JOIN files f ON t.best_file_id = f.id
            WHERE t.spotify_track_id = ?;
            """,
            (spotify_track_id,),
        )
        row = cur.fetchone()

    return row


def register_file_for_track(
    info: TrackInfo,
    file_path: Path,
) -> None:
    """
    Registriert eine Datei zu einem Track und aktualisiert ggf. den "best_file".

    - Stellt sicher, dass der Track-Eintrag existiert (upsert).
    - Legt einen neuen File-Datensatz an.
    - Entscheidet anhand des Formats, ob diese Datei besser ist als die bisherige.
    """
    # 1) Sicherstellen, dass der Track erfasst ist
    upsert_track_basic(info)

    ext = file_path.suffix.lstrip(".").lower()
    new_quality = _format_quality(ext)

    # 2) Bisheriges "best_file" abfragen
    best_row = _get_best_file_row(info.spotify_track_id)
    best_file_id: Optional[int] = None
    best_quality: int = -1

    if best_row is not None:
        best_file_id = int(best_row[0])
        best_ext = Path(best_row[1]).suffix.lstrip(".").lower()
        best_quality = _format_quality(best_ext)

    # 3) Neue Datei eintragen
    new_file_id = _insert_file_for_track(info.spotify_track_id, file_path, ext)

    # 4) Falls es bisher keinen Best-File gab oder die neue Datei besser ist,
    #    Tracks-Tabelle aktualisieren
    if best_file_id is None or new_quality > best_quality:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tracks
                SET best_file_id = ?
                WHERE spotify_track_id = ?;
                """,
                (new_file_id, info.spotify_track_id),
            )


def get_best_file_for_track(spotify_track_id: str) -> Optional[Path]:
    """
    Gibt den Pfad zur aktuell besten bekannten Datei für einen Track zurück.

    Wenn kein best_file gesetzt oder die Datei auf der Platte nicht mehr
    vorhanden ist, wird None zurückgegeben.
    """
    row = _get_best_file_row(spotify_track_id)
    if row is None:
        return None

    path = Path(row[1])
    if not path.exists():
        return None

    return path
