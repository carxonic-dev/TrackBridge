from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from queue import Queue, Empty
from tagging import apply_tags_to_file
from track_registry import TrackInfo, register_file_for_track

from config import (
    OUTPUT_DIRECTORY,
    MAX_PARALLEL_DOWNLOADS,
    DOWNLOAD_MAX_RETRIES,
    AUDIO_PREFERRED_FORMATS,
    SKIP_EXISTING_FILES,
    KNOWN_AUDIO_EXTENSIONS,
    DJ_COMPATIBILITY_PROFILE,
    DJ_WARN_ON_INCOMPATIBLE,
    REGISTRY_ENABLED,
    REGISTRY_STORE_SPOTIFY_URL,  # NEU
    # ALLOW_REENCODE_FOR_INCOMPATIBLE,
    # PREFERRED_HIGH_QUALITY_TARGET,
)

from format_profiles import is_ext_compatible_with_active_profile
from reencode_engine import reencode_if_needed

import subprocess
import threading
import time
import json

from util_filenames import build_audio_filename

# ---------------------------------------------------------------------------
# Download-Status-Konstanten
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"

# ---------------------------------------------------------------------------
# Datenmodell für Download-Jobs
# ---------------------------------------------------------------------------

@dataclass
class DownloadJob:
    """
    Repräsentiert einen geplanten Download für eine Audio-Datei.

    Aktuell: Nur Planung (Dry-Run). Später:
    - Status (queued, running, done, failed)
    - Fehlercodes
    - tatsächlicher Dateipfad
    - YouTube-Video-ID (falls wir das später auflösen)
    """
    playlist_id: str
    track_index: int  # 0-basiert
    title: str
    primary_artist: str
    search_query: str
    target_dir: Path
    output_stem: str  # Dateiname ohne Extension
    spotify_track_id: str | None = None
    spotify_url: str | None = None
    track_meta: Dict[str, Any] | None = None  # Extended-JSON-Daten für Tagging


# ---------------------------------------------------------------------------
# Hilfsfunktionen zum Laden der Extended-JSON
# ---------------------------------------------------------------------------

def _get_playlist_json_path(playlist_id: str) -> Path:
    """
    Liefert den Pfad zur Extended-JSON einer Playlist auf Basis der
    bisherigen Exportlogik.
    """
    return OUTPUT_DIRECTORY / f"spotify_playlist_{playlist_id}.json"


def load_playlist_data(playlist_id: str) -> Dict[str, Any]:
    """
    Lädt die Extended-JSON der Playlist.

    Erwartete Struktur:
    {
      "playlist": {...},
      "tracks": [...]
    }
    """
    json_path = _get_playlist_json_path(playlist_id)

    if not json_path.exists():
        raise FileNotFoundError(
            f"Extended-JSON für Playlist {playlist_id} nicht gefunden: {json_path}"
        )

    raw = json_path.read_text(encoding="utf-8")
    data: Dict[str, Any] = json.loads(raw)

    if "tracks" not in data:
        raise ValueError(
            f"Unerwartetes JSON-Format in {json_path}: 'tracks' fehlt."
        )

    return data


# ---------------------------------------------------------------------------
# Download-Jobs aus Playlistdaten erzeugen
# ---------------------------------------------------------------------------

def build_jobs_from_playlist_data(
    playlist_id: str,
    data: Dict[str, Any],
    per_playlist_subdir: bool = True,
) -> List[DownloadJob]:
    """
    Erzeugt eine Liste von DownloadJob-Objekten aus der Extended-JSON.

    - Titel & Artist kommen aus 'title' / 'primary_artist'
    - Dateiname wird auf Basis von build_audio_filename() gebaut
    - Zielverzeichnis:
      - Default: OUTPUT_DIRECTORY / playlist_id  (pro Playlist ein Unterordner)
    """
    tracks: List[Dict[str, Any]] = data.get("tracks", [])

    if per_playlist_subdir:
        target_root = OUTPUT_DIRECTORY / playlist_id
    else:
        target_root = OUTPUT_DIRECTORY

    target_root.mkdir(parents=True, exist_ok=True)

    jobs: List[DownloadJob] = []

    for idx, t in enumerate(tracks):
        title = (t.get("title") or "").strip()
        primary_artist = (t.get("primary_artist") or "").strip()
        spotify_track_id = t.get("spotify_track_id")
        spotify_url = t.get("spotify_url")

        if not title and not primary_artist:
            # Irgendwas sehr kaputtes, überspringen
            continue

        track_number = t.get("track_number")
        suggested_filename = t.get("suggested_filename") or build_audio_filename(
            title,
            track_number,
        )

        # output_stem = alles vor der Extension
        if "." in suggested_filename:
            output_stem = suggested_filename.rsplit(".", 1)[0]
        else:
            output_stem = suggested_filename

        # yt-dlp Search-Query
        if primary_artist and title:
            query = f"{primary_artist} - {title}"
        else:
            query = title or primary_artist

        search_query = f"ytsearch1:{query}"

        job = DownloadJob(
            playlist_id=playlist_id,
            track_index=idx,
            title=title,
            primary_artist=primary_artist,
            search_query=search_query,
            target_dir=target_root,
            output_stem=output_stem,
            spotify_track_id=spotify_track_id,
            spotify_url=spotify_url,
            track_meta=t,  # Extended-JSON-Daten für Tagging
        )
        jobs.append(job)

    return jobs


# ---------------------------------------------------------------------------
# yt-dlp Befehle generieren (noch kein echter Download)
# ---------------------------------------------------------------------------

def build_yt_dlp_command(job: DownloadJob) -> List[str]:
    """
    Erzeugt den yt-dlp Befehl für einen einzelnen Job.

    - Bevorzugt Audio-Formate aus AUDIO_PREFERRED_FORMATS (z. B. m4a),
      ohne Re-Encode zu erzwingen.
    - Fällt zurück auf bestaudio/best, wenn kein bevorzugtes Format verfügbar ist.
    """
    output_template = str(
        job.target_dir / f"{job.output_stem}.%(ext)s"
    )

    # Format-Selector bauen:
    # z. B. "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best"
    preferred_parts = [
        f"bestaudio[ext={ext}]"
        for ext in AUDIO_PREFERRED_FORMATS
        if ext
    ]
    preferred_parts.append("bestaudio/best")
    format_selector = "/".join(preferred_parts)

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        format_selector,
        "-o",
        output_template,
        job.search_query,
    ]
    return cmd

# ---------------------------------------------------------------------------
# High-Level-Funktionen: Download-Planung & Ausführung
# ---------------------------------------------------------------------------

def plan_downloads_for_playlist(
    playlist_id: str,
    limit: int | None = None,
) -> List[DownloadJob]:
    """
    High-Level-Funktion:
    - lädt Extended-JSON
    - baut Download-Jobs
    - schneidet optional auf 'limit' zu
    - gibt die Jobs zurück

    Diese Funktion führt NOCH KEINE Downloads aus.
    """
    data = load_playlist_data(playlist_id)
    jobs = build_jobs_from_playlist_data(playlist_id, data)

    if limit is not None and limit >= 0:
        jobs = jobs[:limit]

    return jobs


def print_download_plan(jobs: List[DownloadJob]) -> None:
    """
    Gibt eine übersichtliche Dry-Run-Vorschau für die Jobs aus,
    inkl. Beispiel yt-dlp-Befehl.
    """
    if not jobs:
        print("[PLAN] Keine Jobs gefunden.")
        return

    print(f"[PLAN] Geplante Downloads: {len(jobs)}")
    print(f"[PLAN] Max. parallele Downloads laut Config: {MAX_PARALLEL_DOWNLOADS}")
    print()

    for job in jobs:
        print(
            f"[PLAN] #{job.track_index + 1:02d} | {job.primary_artist} - {job.title}"
        )
        print(f"       Zieldatei: {job.target_dir / (job.output_stem + '.<ext>')}")
        if job.spotify_url:
            print(f"       Spotify:   {job.spotify_url}")
        cmd = build_yt_dlp_command(job)
        print(f"       yt-dlp:    {' '.join(cmd)}")
        print()


def _find_downloaded_file(job: DownloadJob) -> Path | None:
    """
    Versucht, die tatsächlich heruntergeladene Audiodatei für einen Job
    im Zielverzeichnis zu finden.

    Nutzt KNOWN_AUDIO_EXTENSIONS und den output_stem.
    """
    for ext in KNOWN_AUDIO_EXTENSIONS:
        candidate = job.target_dir / f"{job.output_stem}.{ext}"
        if candidate.exists():
            return candidate
    return None


def _run_single_job(job: DownloadJob) -> bool:
    """
    Führt einen einzelnen yt-dlp-Job aus.

    - Achtet auf SkipExistingFiles
    - Baut den Befehl
    - Führt ihn via subprocess.run aus
    - Gibt True zurück, wenn returncode == 0, sonst False
    """

    # 1) Optional: vorhandene Dateien prüfen
    if SKIP_EXISTING_FILES:
        existing_paths: list[Path] = []
        for ext in KNOWN_AUDIO_EXTENSIONS:
            candidate = job.target_dir / f"{job.output_stem}.{ext}"
            if candidate.exists():
                existing_paths.append(candidate)

        if existing_paths:
            print(
                "[SKIP] Datei(en) existieren bereits für "
                f"#{job.track_index + 1:02d}: "
                f"{job.primary_artist} - {job.title}"
            )
            for p in existing_paths:
                print(f"       -> {p}")
            # Aus Sicht der Pipeline ist das ein „erfolgreicher“ Job
            return True

    # 2) Zielpfad sicherstellen
    job.target_dir.mkdir(parents=True, exist_ok=True)

    # 3) yt-dlp Kommando bauen und ausführen
    cmd = build_yt_dlp_command(job)

    print(
        f"[RUN] Starte Download #{job.track_index + 1:02d}: "
        f"{job.primary_artist} - {job.title}"
    )
    print(f"[RUN] Ziel: {job.target_dir / (job.output_stem + '.<ext>')}")
    print(f"[RUN] yt-dlp: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[ERROR] yt-dlp wurde nicht gefunden. Ist es im PATH installiert?")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Unerwarteter Fehler beim Start von yt-dlp: {exc}")
        return False

    if result.returncode == 0:
        print(
            f"[OK] Download abgeschlossen: "
            f"{job.primary_artist} - {job.title}"
        )

        # Tatsächlich heruntergeladene Datei ermitteln
        downloaded = _find_downloaded_file(job)
        if downloaded is not None:
            ext = downloaded.suffix.lstrip(".").lower()

            # 1) Kompatibilitäts-Warnung (unabhängig vom Reencode)
            if DJ_WARN_ON_INCOMPATIBLE and not is_ext_compatible_with_active_profile(ext):
                print(
                    "[WARN] Das heruntergeladene Format ist möglicherweise "
                    "nicht mit dem aktiven DJ-Profil kompatibel."
                )
                print(
                    f"       Datei:  {downloaded.name} "
                    f"(.{ext}) - Profil: {DJ_COMPATIBILITY_PROFILE}"
                )
                print(
                    "       Hinweis: Für CDJ-Player sind Formate wie WAV/AIFF/"
                    "ALAC/AAC/MP3/FLAC ideal. WEBM/Opus sind dort oft nicht "
                    "direkt abspielbar."
                )

            # 2) Optionaler HQ-Reencode für inkompatible Formate
            active_path = downloaded
            new_path = reencode_if_needed(downloaded)
            if new_path is not None:
                active_path = new_path
                print(
                    f"[RUN] Aktive HQ-Datei für diesen Track: {new_path.name}"
                )

            # 3) Tagging-Hook: Metadaten aus Extended-JSON anwenden
            if job.track_meta is not None:
                try:
                    apply_tags_to_file(active_path, job.track_meta)
                    print(f"[TAG] Tags angewendet: {active_path.name}")
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"[TAG-ERROR] Tagging fehlgeschlagen für "
                        f"{active_path.name}: {exc}"
                    )

            # 4) Registry-Hook: Datei in der Track-Registry erfassen (optional)
            if REGISTRY_ENABLED and job.spotify_track_id and active_path.exists():
                try:
                    meta = job.track_meta or {}
                    duration_ms = meta.get("duration_ms")

                    source_url = None
                    if REGISTRY_STORE_SPOTIFY_URL:
                        source_url = job.spotify_url

                    track_info = TrackInfo(
                        spotify_track_id=job.spotify_track_id,
                        title=job.title,
                        primary_artist=job.primary_artist,
                        duration_ms=duration_ms,
                        source_url=source_url,
                    )
                    register_file_for_track(track_info, active_path)
                    print(f"[REG] Datei registriert: {active_path}")
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"[REG-ERROR] Registrierung fehlgeschlagen für "
                        f"{active_path}: {exc}"
                    )


        return True

    print(
        f"[ERROR] Download fehlgeschlagen (rc={result.returncode}): "
        f"{job.primary_artist} - {job.title}"
    )
    if result.stderr:
        print("[ERROR] yt-dlp stderr:")
        print(result.stderr.strip())
    return False


def _worker_thread(
    name: str,
    queue: Queue[DownloadJob],
    results: Dict[int, bool],
) -> None:
    """
    Worker, der aus der Queue Jobs zieht, mit Retries ausführt und
    das Ergebnis im 'results'-Dict (track_index -> Erfolg) speichert.
    """
    while True:
        try:
            job = queue.get_nowait()
        except Empty:
            return

        success = False
        attempts = DOWNLOAD_MAX_RETRIES + 1

        for attempt in range(1, attempts + 1):
            print(
                f"[WORKER {name}] Versuch {attempt}/{attempts} für "
                f"#{job.track_index + 1:02d}: {job.primary_artist} - {job.title}"
            )
            success = _run_single_job(job)
            if success:
                break
            else:
                if attempt < attempts:
                    print(
                        f"[WORKER {name}] Retry geplant für "
                        f"{job.primary_artist} - {job.title}"
                    )
                    time.sleep(1.0)  # kleiner Backoff

        results[job.track_index] = success
        queue.task_done()


def run_downloads_for_playlist(
    playlist_id: str,
    limit: int | None = None,
) -> None:
    """
    Startet die Downloads für eine Playlist basierend auf der Extended-JSON.

    - nutzt plan_downloads_for_playlist() für die Jobliste
    - entscheidet anhand MAX_PARALLEL_DOWNLOADS, ob sequentiell oder parallel
    - verwendet DOWNLOAD_MAX_RETRIES für Wiederholungsversuche
    """
    jobs = plan_downloads_for_playlist(playlist_id, limit=limit)
    if not jobs:
        print("[RUN] Keine Downloads geplant - Abbruch.")
        return

    print(
        f"[RUN] Starte Downloads für Playlist {playlist_id} "
        f"({len(jobs)} Track(s))"
    )
    print(f"[RUN] Konfiguration: max. parallele Downloads = {MAX_PARALLEL_DOWNLOADS}")
    print(f"[RUN] Konfiguration: max. Retries pro Job     = {DOWNLOAD_MAX_RETRIES}")
    print()

    # Sequential Mode
    if MAX_PARALLEL_DOWNLOADS <= 1:
        results: Dict[int, bool] = {}
        for job in jobs:
            success = False
            attempts = DOWNLOAD_MAX_RETRIES + 1
            for attempt in range(1, attempts + 1):
                print(
                    f"[RUN] Versuch {attempt}/{attempts} für "
                    f"#{job.track_index + 1:02d}: {job.primary_artist} - {job.title}"
                )
                success = _run_single_job(job)
                if success:
                    break
                elif attempt < attempts:
                    print(
                        f"[RUN] Retry geplant für "
                        f"{job.primary_artist} - {job.title}"
                    )
                    # optionaler kleiner Backoff
                    time.sleep(1.0)

            results[job.track_index] = success

        _print_summary(jobs, results)
        return

    # Parallel Mode mit Threads
    job_queue: Queue[DownloadJob] = Queue()
    results_parallel: Dict[int, bool] = {}

    for job in jobs:
        job_queue.put(job)

    workers: list[threading.Thread] = []
    worker_count = min(MAX_PARALLEL_DOWNLOADS, len(jobs))

    print(f"[RUN] Starte {worker_count} Worker-Thread(s).")
    print()

    for i in range(worker_count):
        t = threading.Thread(
            target=_worker_thread,
            args=(f"W{i+1}", job_queue, results_parallel),
            daemon=True,
        )
        t.start()
        workers.append(t)

    # Warten, bis Queue leer ist
    job_queue.join()

    # Optional: auf Threads warten
    for t in workers:
        t.join(timeout=0.1)

    _print_summary(jobs, results_parallel)


def _print_summary(
    jobs: List[DownloadJob],
    results: Dict[int, bool],
) -> None:
    """
    Gibt eine kompakte Zusammenfassung aller Jobs aus.
    """
    total = len(jobs)
    success_count = sum(1 for idx, ok in results.items() if ok)
    fail_count = total - success_count

    print()
    print("========== DOWNLOAD-SUMMARY ==========")
    print(f"Gesamt:   {total}")
    print(f"Erfolgreich: {success_count}")
    print(f"Fehlgeschlagen: {fail_count}")
    print("======================================")

    if fail_count > 0:
        print()
        print("Fehlgeschlagene Titel:")
        for job in jobs:
            ok = results.get(job.track_index, False)
            if not ok:
                print(
                    f"- #{job.track_index + 1:02d} | "
                    f"{job.primary_artist} - {job.title}"
                )


def retag_downloads_for_playlist(
    playlist_id: str,
    limit: int | None = None,
    update_registry: bool = True,
) -> None:
    """
    Wendet das Tagging (und optional Registry-Update) auf bereits
    heruntergeladene Dateien einer Playlist an.

    Voraussetzung:
    - Extended-JSON der Playlist existiert (export wurde bereits ausgeführt)
    - Die Audiodateien liegen im erwarteten Zielordner
    """

    data = load_playlist_data(playlist_id)
    jobs = build_jobs_from_playlist_data(playlist_id, data)

    if limit is not None and limit >= 0:
        jobs = jobs[:limit]

    if not jobs:
        print(f"[TAG-PLAYLIST] Keine Tracks für Playlist {playlist_id} gefunden.")
        return

    print(
        f"[TAG-PLAYLIST] Starte Tagging für Playlist {playlist_id} "
        f"({len(jobs)} Track(s))"
    )
    print(
        f"[TAG-PLAYLIST] Registry-Update: "
        f"{'aktiv' if (REGISTRY_ENABLED and update_registry) else 'deaktiviert'}"
    )
    print()

    tagged = 0
    skipped = 0
    failed = 0

    for job in jobs:
        audio_path = _find_downloaded_file(job)
        if audio_path is None:
            print(
                f"[TAG-SKIP] Keine Datei gefunden für "
                f"#{job.track_index + 1:02d}: "
                f"{job.primary_artist} - {job.title}"
            )
            skipped += 1
            continue

        # 1) Tagging anwenden
        meta = job.track_meta or {}
        try:
            apply_tags_to_file(audio_path, meta)
            print(f"[TAG] Tags angewendet: {audio_path.name}")
            tagged += 1
        except Exception as exc:  # noqa: BLE001
            print(
                f"[TAG-ERROR] Tagging fehlgeschlagen für "
                f"{audio_path.name}: {exc}"
            )
            failed += 1
            continue

        # 2) Optional Registry-Update
        if REGISTRY_ENABLED and update_registry and job.spotify_track_id:
            try:
                duration_ms = meta.get("duration_ms")
                source_url = job.spotify_url if REGISTRY_STORE_SPOTIFY_URL else None

                track_info = TrackInfo(
                    spotify_track_id=job.spotify_track_id,
                    title=job.title,
                    primary_artist=job.primary_artist,
                    duration_ms=duration_ms,
                    source_url=source_url,
                )
                register_file_for_track(track_info, audio_path)
                print(f"[REG] Datei registriert (Tag-Run): {audio_path}")
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[REG-ERROR] Registrierung (Tag-Run) fehlgeschlagen "
                    f"für {audio_path}: {exc}"
                )

    print()
    print("====== TAG-PLAYLIST-SUMMARY ======")
    print(f"Getaggte Dateien:        {tagged}")
    print(f"Übersprungen (fehlt):    {skipped}")
    print(f"Fehler beim Tagging:     {failed}")
    print("==================================")

# Ende yt_dlp_runner.py
