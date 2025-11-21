from __future__ import annotations

import argparse
from pathlib import Path

from playlist_exporter import (
    export_playlist_to_json,
    export_playlist_to_ytdlp_txt,
)
from yt_dlp_runner import (
    plan_downloads_for_playlist,
    print_download_plan,
    run_downloads_for_playlist,
)
from spotify_client import get_access_token, SpotifyAuthError
from collection_analyzer import analyze_playlist_folder


def sanity_check() -> bool:
    """
    Prüft, ob:
    - .env korrekt geladen wird
    - ein Access-Token von Spotify geholt werden kann
    """
    try:
        token = get_access_token()
    except SpotifyAuthError as exc:
        print(f"[SANITY] SpotifyAuthError: {exc}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[SANITY] Unerwarteter Fehler: {exc}")
        return False
    else:
        print(f"[SANITY] Access-Token erhalten (Länge: {len(token)})")
        return True


def build_parser() -> argparse.ArgumentParser:
    """
    Baut den Argument-Parser für das CLI-Tool.

    Subcommands:
      - sanity-check
      - export
      - export-ytdlp
      - plan-downloads
      - run-downloads
      - analyze-playlist
    """
    parser = argparse.ArgumentParser(
        prog="spotify_2_yt-dlp",
        description="CLI-Tool zum Export von öffentlichen Spotify-Playlists und Download per yt-dlp.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ------------------------------------------------------------------
    # sanity-check
    # ------------------------------------------------------------------
    sanity_parser = subparsers.add_parser(
        "sanity-check",
        help="Prüft Zugriff auf Spotify (Token-Test).",
    )
    sanity_parser.set_defaults(func=handle_sanity_check)

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------
    export_parser = subparsers.add_parser(
        "export",
        help="Exportiert eine öffentliche Playlist nach JSON.",
    )
    export_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (z. B. 37i9dQZF1DX0Yxoavh5qJV).",
    )
    export_parser.add_argument(
        "--output",
        type=str,
        help="Optionaler Pfad zur Ausgabedatei (Standard: spotify_playlist_<ID>.json im Output-Ordner).",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: Anzahl der zu exportierenden Tracks begrenzen (z. B. 10).",
    )
    export_parser.set_defaults(func=handle_export_playlist)

    # ------------------------------------------------------------------
    # export-ytdlp
    # ------------------------------------------------------------------
    export_ytdlp_parser = subparsers.add_parser(
        "export-ytdlp",
        help="Erzeugt eine yt-dlp-Trackliste (Textdatei mit ytsearch1:Artist - Title).",
    )
    export_ytdlp_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (z. B. 37i9dQZF1DX0Yxoavh5qJV).",
    )
    export_ytdlp_parser.add_argument(
        "--output",
        type=str,
        help="Optionaler Pfad zur Ausgabedatei (Standard: laut config.json/OutputDirectory).",
    )
    export_ytdlp_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: Anzahl der zu exportierenden Tracks begrenzen.",
    )
    export_ytdlp_parser.set_defaults(func=handle_export_ytdlp)

    # ------------------------------------------------------------------
    # plan-downloads
    # ------------------------------------------------------------------
    plan_parser = subparsers.add_parser(
        "plan-downloads",
        help=(
            "Erzeugt eine Download-Planung für yt-dlp auf Basis der "
            "Extended-JSON einer Playlist (Dry-Run, keine echten Downloads)."
        ),
    )
    plan_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (muss zuvor mit 'export' exportiert worden sein).",
    )
    plan_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: Anzahl der geplanten Tracks begrenzen (z. B. 10).",
    )
    plan_parser.set_defaults(func=handle_plan_downloads)

    # ------------------------------------------------------------------
    # run-downloads
    # ------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run-downloads",
        help=(
            "Startet die Downloads für eine Playlist basierend auf der "
            "Extended-JSON (nutzt yt-dlp)."
        ),
    )
    run_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (muss zuvor mit 'export' exportiert worden sein).",
    )
    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: Anzahl der zu ladenden Tracks begrenzen (z. B. 10).",
    )
    run_parser.set_defaults(func=handle_run_downloads)

    # ------------------------------------------------------------------
    # analyze-playlist
    # ------------------------------------------------------------------
    analyze_parser = subparsers.add_parser(
        "analyze-playlist",
        help=(
            "Analysiert den lokalen Playlist-Ordner und zeigt eine Übersicht "
            "über Formate & DJ-Kompatibilität."
        ),
    )
    analyze_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID, deren Zielordner analysiert werden soll.",
    )
    analyze_parser.set_defaults(func=handle_analyze_playlist)

    return parser


# ----------------------------------------------------------------------
# Handler-Funktionen für die Subcommands
# ----------------------------------------------------------------------


def handle_sanity_check(args: argparse.Namespace) -> None:  # noqa: ARG001
    """
    Handler für `sanity-check`.
    """
    ok = sanity_check()
    if ok:
        print("[CLI] Sanity check OK – Projekt bereit für weitere Aktionen.")
    else:
        print("[CLI] Sanity check FEHLGESCHLAGEN – bitte .env / Netzwerk prüfen.")


def handle_export_playlist(args: argparse.Namespace) -> None:
    """
    Handler für `export`.
    """
    playlist_id: str = args.playlist_id
    output_arg: str | None = args.output
    limit: int | None = getattr(args, "limit", None)

    output_path = Path(output_arg) if output_arg else None

    try:
        json_path = export_playlist_to_json(
            playlist_id=playlist_id,
            output_path=output_path,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[CLI] Fehler beim JSON-Export: {exc}")
        return

    print("[CLI] Export erfolgreich.")
    print(f"[CLI] Playlist-ID: {playlist_id}")
    print(f"[CLI] Ausgabe: {json_path.resolve()}")


def handle_export_ytdlp(args: argparse.Namespace) -> None:
    """
    Handler für `export-ytdlp`.
    """
    playlist_id: str = args.playlist_id
    output_arg: str | None = args.output
    limit: int | None = getattr(args, "limit", None)

    output_path = Path(output_arg) if output_arg else None

    try:
        path = export_playlist_to_ytdlp_txt(
            playlist_id=playlist_id,
            output_path=output_path,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[CLI] Fehler beim Export der yt-dlp-Trackliste: {exc}")
        return

    print("[CLI] yt-dlp-Trackliste erfolgreich erstellt.")
    print(f"[CLI] Playlist-ID: {playlist_id}")
    print(f"[CLI] Ausgabe: {path.resolve()}")


def handle_plan_downloads(args: argparse.Namespace) -> None:
    """
    Handler für `plan-downloads`.
    """
    playlist_id: str = args.playlist_id
    limit: int | None = args.limit

    try:
        jobs = plan_downloads_for_playlist(playlist_id, limit=limit)
    except FileNotFoundError as exc:
        print(f"[CLI] Fehler: {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        print(f"[CLI] Unerwarteter Fehler bei der Planerstellung: {exc}")
        return

    print_download_plan(jobs)


def handle_run_downloads(args: argparse.Namespace) -> None:
    """
    Handler für `run-downloads`.
    """
    playlist_id: str = args.playlist_id
    limit: int | None = args.limit

    try:
        run_downloads_for_playlist(playlist_id, limit=limit)
    except FileNotFoundError as exc:
        print(f"[CLI] Fehler: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"[CLI] Unerwarteter Fehler beim Download-Run: {exc}")


def handle_analyze_playlist(args: argparse.Namespace) -> None:
    """
    Handler für `analyze-playlist`.
    """
    playlist_id: str = args.playlist_id
    analyze_playlist_folder(playlist_id)


def main() -> None:
    """
    Einstiegspunkt für das CLI.
    """
    parser = build_parser()
    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return
    func(args)


if __name__ == "__main__":
    main()
