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
    Baut den CLI-Parser für spotify_2_yt-dlp.

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
        description=(
            "CLI-Tool zum Exportieren von Spotify-Playlists und automatischem "
            "Download per yt-dlp."
        ),
    )

    subparsers = parser.add_subparsers(
        title="Befehle",
        dest="command",
        metavar=(
            "{sanity-check,export,export-ytdlp,"
            "plan-downloads,run-downloads,tag-playlist,analyze-playlist}"
        ),
    )

    # ------------------------------------------------------------------
    # sanity-check
    # ------------------------------------------------------------------
    sanity_parser = subparsers.add_parser(
        "sanity-check",
        help="Prüft Zugriff auf Spotify (Token-Test) und Basis-Konfiguration.",
    )
    sanity_parser.set_defaults(func=handle_sanity_check)

    # ------------------------------------------------------------------
    # export
    # ------------------------------------------------------------------
    export_parser = subparsers.add_parser(
        "export",
        help="Exportiert eine öffentliche Playlist als Extended-JSON.",
    )
    export_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (z.B. 3ENm4IUzswtJ2i0LBYQBSr).",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: maximale Anzahl zu exportierender Tracks (Standard: alle).",
    )
    export_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Optional: Ausgabedatei. Wenn nicht gesetzt, wird ein Standardpfad "
            "basierend auf der config.json verwendet."
        ),
    )
    export_parser.set_defaults(func=handle_export_playlist)

    # ------------------------------------------------------------------
    # export-ytdlp
    # ------------------------------------------------------------------
    export_ytdlp_parser = subparsers.add_parser(
        "export-ytdlp",
        help=(
            "Erzeugt eine yt-dlp-Trackliste (Textdatei mit "
            "Zeilen im Format 'ytsearch1:Artist - Title')."
        ),
    )
    export_ytdlp_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID, die als Basis für die Suchliste dient.",
    )
    export_ytdlp_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: maximale Anzahl zu exportierender Tracks (Standard: alle).",
    )
    export_ytdlp_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Optional: Ausgabedatei für die Textliste. "
            "Wenn nicht gesetzt, wird ein Standardpfad verwendet."
        ),
    )
    export_ytdlp_parser.set_defaults(func=handle_export_ytdlp)

    # ------------------------------------------------------------------
    # plan-downloads
    # ------------------------------------------------------------------
    plan_parser = subparsers.add_parser(
        "plan-downloads",
        help=(
            "Erzeugt eine Download-Planung (Dry-Run) für yt-dlp auf Basis einer "
            "Spotify-Playlist bzw. einer Extended-JSON."
        ),
    )

    plan_source = plan_parser.add_mutually_exclusive_group(required=True)
    plan_source.add_argument(
        "--playlist-id",
        help=(
            "Spotify-Playlist-ID. Die Extended-JSON wird bei Bedarf automatisch erzeugt."
        ),
    )
    plan_source.add_argument(
        "--json",
        type=str,
        help=(
            "Pfad zu einer bereits exportierten Extended-JSON-Datei, die als "
            "Grundlage für die Planung genutzt wird."
        ),
    )

    plan_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: maximale Anzahl geplanter Downloads (Standard: alle).",
    )
    plan_parser.set_defaults(func=handle_plan_downloads)

    # ------------------------------------------------------------------
    # run-downloads
    # ------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run-downloads",
        help=(
            "Startet die Downloads für eine Playlist basierend auf der "
            "Extended-JSON (nutzt yt-dlp, parallele Worker, Retry-Logik)."
        ),
    )

    run_source = run_parser.add_mutually_exclusive_group(required=True)
    run_source.add_argument(
        "--playlist-id",
        help=(
            "Spotify-Playlist-ID. Die Extended-JSON wird bei Bedarf automatisch erzeugt."
        ),
    )
    run_source.add_argument(
        "--json",
        type=str,
        help=(
            "Pfad zu einer bereits exportierten Extended-JSON-Datei, die als "
            "Grundlage für die Downloads genutzt wird."
        ),
    )

    run_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: maximale Anzahl tatsächlicher Downloads (Standard: alle).",
    )
    run_parser.set_defaults(func=handle_run_downloads)

    # ------------------------------------------------------------------
    # tag-playlist
    # ------------------------------------------------------------------
    tag_parser = subparsers.add_parser(
        "tag-playlist",
        help=(
            "Wendet Tagging (und optional Registry-Update) auf bereits "
            "heruntergeladene Dateien einer Playlist an."
        ),
    )

    tag_parser.add_argument(
        "--playlist-id",
        required=True,
        help="Spotify-Playlist-ID (wie beim Export).",
    )
    tag_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional: Anzahl der zu verarbeitenden Tracks begrenzen.",
    )
    tag_parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Registry-Update für diesen Lauf deaktivieren.",
    )

    tag_parser.set_defaults(func=handle_tag_playlist)


    # ------------------------------------------------------------------
    # analyze-playlist
    # ------------------------------------------------------------------
    analyze_parser = subparsers.add_parser(
        "analyze-playlist",
        help=(
            "Analysiert eine Playlist im lokalen Dateisystem (Formate, "
            "DJ-Kompatibilität, Duplikate, fehlende Tracks)."
        ),
    )

    analyze_source = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_source.add_argument(
        "--playlist-path",
        type=str,
        help=(
            "Pfad zum lokalen Playlist-Ordner mit heruntergeladenen Dateien "
            "(z.B. OutputRoot/<playlist-id>/)."
        ),
    )
    analyze_source.add_argument(
        "--playlist-id",
        type=str,
        help=(
            "Spotify-Playlist-ID. Der lokale Pfad wird aus der config/Logik abgeleitet."
        ),
    )

    analyze_parser.set_defaults(func=handle_analyze_playlist)

    # ------------------------------------------------------------------
    # Fallback: wenn kein Subcommand angegeben wurde
    # ------------------------------------------------------------------
    parser.set_defaults(func=None)

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


def handle_tag_playlist(args: argparse.Namespace) -> None:
    """
    CLI-Handler für den Befehl 'tag-playlist'.

    Nutzt die Extended-JSON und die bereits vorhandenen Audiodateien,
    um Tagging und optional die Registry zu aktualisieren.
    """
    from yt_dlp_runner import retag_downloads_for_playlist

    update_registry = not getattr(args, "no_registry", False)

    retag_downloads_for_playlist(
        playlist_id=args.playlist_id,
        limit=args.limit,
        update_registry=update_registry,
    )


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
