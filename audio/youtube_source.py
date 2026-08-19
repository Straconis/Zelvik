import os
import shutil
import subprocess
import tempfile
import threading
import time

import yt_dlp


class YouTubeSource:
    SAMPLE_RATE = 48000
    CHANNELS = 2
    SAMPLE_WIDTH = 2

    # Roughly three seconds of decoded PCM.
    MAX_BUFFER_BYTES = (
        SAMPLE_RATE
        * CHANNELS
        * SAMPLE_WIDTH
        * 3
    )

    def __init__(
        self,
        youtube_url,
        volume=1.0,
        loop=False,
        start_time=None,
        stop_time=None,
        cookies_file=None,
    ):
        self.youtube_url = youtube_url

        self.volume = volume
        self.loop = loop

        self.start_time = start_time
        self.stop_time = stop_time

        self.cookies_file = (
            os.path.abspath(cookies_file)
            if cookies_file
            else None
        )

        self.auth_in_use = False

        # Retries after the initial attempt.
        self.max_retries = 3

        self.process = None
        self.stderr_file = None

        self.worker_thread = None
        self.stop_event = threading.Event()

        self.buffer = bytearray()
        self.buffer_lock = threading.RLock()

        self.state_lock = threading.RLock()

        self.finished = False
        self.started = False

        self.status_text = (
            "YouTube: Stopped"
        )

        self.last_error = None

        self.error_kind = None
        self.error_message = None
        self.error_details = None
        self.error_retryable = False
        self.error_reported = False

        # Temporary media downloaded by yt-dlp.
        self.temp_dir = None
        self.media_file = None

    # -------------------------------------------------
    # Windows subprocess handling
    # -------------------------------------------------

    def _subprocess_creation_flags(self):
        """
        Prevent FFmpeg from opening a command window when
        Zelvik is packaged with PyInstaller's
        --windowed option.
        """

        if os.name == "nt":
            return subprocess.CREATE_NO_WINDOW

        return 0

    # -------------------------------------------------
    # Status
    # -------------------------------------------------

    def _set_status(
        self,
        text,
    ):
        with self.state_lock:
            self.status_text = text

        print(text)

    def _classify_error(
        self,
        details,
        default_retryable=False,
    ):
        text = (
            details or ""
        ).lower()

        authentication_terms = (
            "sign in",
            "login required",
            "log in",
            "age-restricted",
            "age restricted",
            "confirm your age",
            "authentication required",
            "cookies",
        )

        unavailable_terms = (
            "video unavailable",
            "this video is unavailable",
            "private video",
            "video is private",
            "removed by the uploader",
            "has been removed",
        )

        temporary_terms = (
            "timed out",
            "timeout",
            "connection reset",
            "connection refused",
            "temporary failure",
            "temporarily unavailable",
            "network is unreachable",
            "http error 429",
            "too many requests",
            "http error 500",
            "http error 502",
            "http error 503",
            "http error 504",
        )

        if any(
            term in text
            for term in authentication_terms
        ):
            return (
                "authentication",
                "This video requires YouTube authentication.",
                False,
            )

        if any(
            term in text
            for term in unavailable_terms
        ):
            return (
                "unavailable",
                "This YouTube video is unavailable.",
                False,
            )

        if (
            "requested format is not available"
            in text
        ):
            return (
                "format",
                (
                    "YouTube did not provide a playable "
                    "audio format."
                ),
                True,
            )

        if (
            "403" in text
            or "forbidden" in text
            or "access denied" in text
        ):
            return (
                "http_403",
                "YouTube denied access to the media stream.",
                True,
            )

        if any(
            term in text
            for term in temporary_terms
        ):
            return (
                "network",
                (
                    "A temporary network error interrupted "
                    "YouTube playback."
                ),
                True,
            )

        return (
            "playback",
            "Zelvik could not play this YouTube video.",
            default_retryable,
        )

    def _set_error(
        self,
        kind,
        message,
        details="",
        retryable=False,
    ):
        with self.state_lock:
            self.last_error = (
                details or message
            )

            self.error_kind = kind
            self.error_message = message
            self.error_details = (
                details or message
            )
            self.error_retryable = retryable
            self.error_reported = False

        self._set_status(
            f"YouTube: Failed — {message}"
        )

    def get_error_state(self):
        with self.state_lock:
            if not self.error_message:
                return None

            return {
                "kind": self.error_kind,
                "message": self.error_message,
                "details": self.error_details,
                "retryable": self.error_retryable,
                "reported": self.error_reported,
            }

    def mark_error_reported(self):
        with self.state_lock:
            self.error_reported = True

    # -------------------------------------------------
    # Start
    # -------------------------------------------------

    def start(self):
        with self.state_lock:
            if (
                self.worker_thread is not None
                and self.worker_thread.is_alive()
            ):
                return

            self.finished = False
            self.started = True

            self.last_error = None

            self.error_kind = None
            self.error_message = None
            self.error_details = None
            self.error_retryable = False
            self.error_reported = False

            self.auth_in_use = False

        self.stop_event.clear()

        with self.buffer_lock:
            self.buffer.clear()

        self._cleanup_temp_media()

        self.worker_thread = threading.Thread(
            target=self._worker,
            name="YouTubeSourceWorker",
            daemon=True,
        )

        self.worker_thread.start()

    # -------------------------------------------------
    # YouTube cookie-file authentication
    # -------------------------------------------------

    @staticmethod
    def check_cookie_auth(
        cookies_file,
    ):
        if not cookies_file:
            return {
                "ok": True,
                "authenticated": False,
                "message": "Authentication is disabled.",
                "details": "",
            }

        path = os.path.abspath(
            cookies_file
        )

        if not os.path.isfile(path):
            return {
                "ok": False,
                "authenticated": False,
                "message": (
                    "The selected cookies file "
                    "does not exist."
                ),
                "details": path,
            }

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as handle:
                lines = handle.readlines()

        except Exception as error:
            return {
                "ok": False,
                "authenticated": False,
                "message": (
                    "Zelvik could not read "
                    "the selected cookies file."
                ),
                "details": str(error),
            }

        youtube_cookie_count = 0

        auth_cookie_names = {
            "SID",
            "HSID",
            "SSID",
            "APISID",
            "SAPISID",
            "__Secure-1PAPISID",
            "__Secure-3PAPISID",
            "__Secure-1PSID",
            "__Secure-3PSID",
        }

        found_auth_names = set()

        for raw_line in lines:
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
            ):
                continue

            parts = line.split("\t")

            if len(parts) < 7:
                continue

            domain = parts[0].lower()
            name = parts[5]

            if (
                "youtube.com" in domain
                or "google.com" in domain
            ):
                youtube_cookie_count += 1

                if name in auth_cookie_names:
                    found_auth_names.add(
                        name
                    )

        if found_auth_names:
            return {
                "ok": True,
                "authenticated": True,
                "message": (
                    "Signed-in YouTube cookies were found."
                ),
                "details": (
                    f"Found {youtube_cookie_count} "
                    "YouTube/Google cookies "
                    f"and {len(found_auth_names)} "
                    "recognized sign-in cookies."
                ),
            }

        if youtube_cookie_count:
            return {
                "ok": True,
                "authenticated": False,
                "message": (
                    "YouTube cookies were found, but "
                    "Zelvik could not confirm a "
                    "signed-in session."
                ),
                "details": (
                    f"Found {youtube_cookie_count} "
                    "YouTube/Google cookies "
                    "but no recognized sign-in cookies."
                ),
            }

        return {
            "ok": True,
            "authenticated": False,
            "message": (
                "No YouTube or Google cookies "
                "were found in this file."
            ),
            "details": (
                "The file is readable, but it does "
                "not appear to contain YouTube "
                "authentication cookies."
            ),
        }

    # -------------------------------------------------
    # yt-dlp download
    # -------------------------------------------------

    def _download_progress_hook(
        self,
        status,
    ):
        """
        Stop a yt-dlp download if the source has been
        stopped from Zelvik.
        """

        if self.stop_event.is_set():
            raise yt_dlp.utils.DownloadCancelled(
                "YouTube download stopped."
            )

    def _download_media(
        self,
        use_auth=False,
    ):
        """
        Download YouTube audio using yt-dlp itself.

        yt-dlp handles:
        - mweb playback
        - PO-token generation
        - Deno/EJS challenge solving
        - YouTube HTTP/range requests

        FFmpeg only sees the finished local file.
        """

        self._cleanup_temp_media()

        if use_auth:
            self._set_status(
                "YouTube: Downloading stream "
                "with authentication..."
            )
        else:
            self._set_status(
                "YouTube: Preparing stream..."
            )

        self.temp_dir = tempfile.mkdtemp(
            prefix="zelvik_youtube_"
        )

        output_template = os.path.join(
            self.temp_dir,
            "media.%(ext)s",
        )

        ydl_options = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "cachedir": False,

            # Allow yt-dlp to retrieve the EJS solver
            # required for YouTube JS challenges.
            "remote_components": {
                "ejs:github",
            },

            # Use mweb so bgutil can generate a matching
            # GVS PO token without launching a browser.
            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "mweb",
                    ],
                },
            },

            # Download into Zelvik's temporary folder.
            "outtmpl": output_template,

            "progress_hooks": [
                self._download_progress_hook,
            ],
        }

        if (
            use_auth
            and self.cookies_file
        ):
            ydl_options[
                "cookiefile"
            ] = self.cookies_file

        with yt_dlp.YoutubeDL(
            ydl_options
        ) as ydl:
            info = ydl.extract_info(
                self.youtube_url,
                download=True,
            )

            if info is None:
                raise RuntimeError(
                    "yt-dlp returned no video information."
                )

            if "entries" in info:
                entries = [
                    entry
                    for entry in info["entries"]
                    if entry
                ]

                if not entries:
                    raise RuntimeError(
                        "No playable entries were found."
                    )

                info = entries[0]

            title = info.get(
                "title",
                "YouTube audio",
            )

            candidate_files = []

            requested_downloads = (
                info.get(
                    "requested_downloads"
                )
                or []
            )

            for download_info in requested_downloads:
                filepath = download_info.get(
                    "filepath"
                )

                if filepath:
                    candidate_files.append(
                        filepath
                    )

            prepared_filename = (
                ydl.prepare_filename(
                    info
                )
            )

            if prepared_filename:
                candidate_files.append(
                    prepared_filename
                )

        # First try filenames reported directly by yt-dlp.
        for candidate in candidate_files:
            if (
                candidate
                and os.path.isfile(
                    candidate
                )
            ):
                self.media_file = os.path.abspath(
                    candidate
                )

                return (
                    self.media_file,
                    title,
                )

        # Fallback: find the actual completed file in the
        # temporary directory.
        files = []

        for name in os.listdir(
            self.temp_dir
        ):
            path = os.path.join(
                self.temp_dir,
                name,
            )

            if not os.path.isfile(
                path
            ):
                continue

            if name.endswith(
                ".part"
            ):
                continue

            if name.endswith(
                ".ytdl"
            ):
                continue

            files.append(
                path
            )

        if not files:
            raise RuntimeError(
                "yt-dlp completed but no downloaded "
                "media file was found."
            )

        files.sort(
            key=lambda path: (
                os.path.getsize(
                    path
                )
            ),
            reverse=True,
        )

        self.media_file = os.path.abspath(
            files[0]
        )

        return (
            self.media_file,
            title,
        )

    # -------------------------------------------------
    # FFmpeg
    # -------------------------------------------------

    def _build_ffmpeg_command(
        self,
        media_file,
    ):
        command = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            media_file,
        ]

        if (
            self.start_time
            is not None
        ):
            command.extend(
                [
                    "-ss",
                    str(
                        self.start_time
                    ),
                ]
            )

        duration = None

        if (
            self.stop_time
            is not None
        ):
            if (
                self.start_time
                is not None
            ):
                duration = (
                    self.stop_time
                    - self.start_time
                )

            else:
                duration = (
                    self.stop_time
                )

        if (
            duration is not None
            and duration > 0
        ):
            command.extend(
                [
                    "-t",
                    str(duration),
                ]
            )

        command.extend(
            [
                "-vn",
                "-f",
                "s16le",
                "-ar",
                "48000",
                "-ac",
                "2",
                "pipe:1",
            ]
        )

        return command

    def _start_ffmpeg(
        self,
        media_file,
    ):
        self._cleanup_process()

        self.stderr_file = (
            tempfile.TemporaryFile()
        )

        command = (
            self._build_ffmpeg_command(
                media_file
            )
        )

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=self.stderr_file,
            stdin=subprocess.DEVNULL,
            bufsize=0,
            creationflags=(
                self._subprocess_creation_flags()
            ),
        )

    # -------------------------------------------------
    # Worker
    # -------------------------------------------------

    def _worker(self):
        retry_count = 0
        use_auth = False

        # ---------------------------------------------
        # Download using yt-dlp
        # ---------------------------------------------

        while not self.stop_event.is_set():
            try:
                (
                    media_file,
                    title,
                ) = self._download_media(
                    use_auth=use_auth
                )

            except yt_dlp.utils.DownloadCancelled:
                self._cleanup_temp_media()

                self._set_status(
                    "YouTube: Stopped"
                )

                self._mark_finished()

                return

            except Exception as error:
                self.last_error = str(
                    error
                )

                (
                    kind,
                    message,
                    retryable,
                ) = self._classify_error(
                    str(error),
                    default_retryable=True,
                )

                if (
                    kind == "authentication"
                    and not use_auth
                    and self.cookies_file
                    and os.path.isfile(
                        self.cookies_file
                    )
                ):
                    use_auth = True
                    self.auth_in_use = True
                    retry_count = 0

                    self._set_status(
                        "YouTube: Authentication "
                        "required — retrying with "
                        "saved cookies..."
                    )

                    if self._wait_or_stop(
                        0.5
                    ):
                        break

                    continue

                if (
                    kind == "authentication"
                    and not self.cookies_file
                ):
                    message = (
                        "This video requires YouTube "
                        "authentication. Import cookies.txt "
                        "in Zelvik and try again."
                    )

                    retryable = False

                if (
                    retryable
                    and retry_count
                    < self.max_retries
                ):
                    retry_count += 1

                    self._set_status(
                        "YouTube: Download failed — "
                        f"retrying "
                        f"{retry_count}/"
                        f"{self.max_retries}..."
                    )

                    if self._wait_or_stop(
                        1.5
                    ):
                        break

                    continue

                self._set_error(
                    kind=kind,
                    message=message,
                    details=str(error),
                    retryable=retryable,
                )

                print(
                    "YouTube download error: "
                    f"{error}"
                )

                self._cleanup_temp_media()

                self._mark_finished()

                return

            break

        if self.stop_event.is_set():
            self._cleanup_temp_media()

            self._set_status(
                "YouTube: Stopped"
            )

            self._mark_finished()

            return

        # ---------------------------------------------
        # Local playback
        # ---------------------------------------------

        retry_count = 0

        while not self.stop_event.is_set():
            if use_auth:
                self.auth_in_use = True

                self._set_status(
                    "YouTube: Playing "
                    f"(authenticated) — {title}"
                )
            else:
                self.auth_in_use = False

                self._set_status(
                    f"YouTube: Playing — {title}"
                )

            try:
                self._start_ffmpeg(
                    media_file
                )

            except Exception as error:
                self.last_error = str(
                    error
                )

                self._set_error(
                    kind="ffmpeg",
                    message=(
                        "FFmpeg could not start "
                        "YouTube playback."
                    ),
                    details=str(error),
                    retryable=False,
                )

                print(
                    "YouTube FFmpeg start error: "
                    f"{error}"
                )

                self._cleanup_temp_media()

                self._mark_finished()

                return

            while not self.stop_event.is_set():
                process = self.process

                if (
                    process is None
                    or process.stdout is None
                ):
                    break

                try:
                    data = (
                        process.stdout.read(
                            38400
                        )
                    )

                except Exception as error:
                    self.last_error = str(
                        error
                    )

                    print(
                        "YouTube PCM read error: "
                        f"{error}"
                    )

                    data = b""

                if data:
                    self._append_buffer(
                        data
                    )

                    continue

                break

            if self.stop_event.is_set():
                break

            (
                return_code,
                error_text,
            ) = self._finish_process()

            # -----------------------------------------
            # FFmpeg errors
            # -----------------------------------------

            if (
                return_code not in (
                    0,
                    None,
                )
            ):
                self.last_error = (
                    error_text.strip()
                )

                (
                    kind,
                    message,
                    retryable,
                ) = self._classify_error(
                    error_text
                )

                self._set_error(
                    kind=kind,
                    message=message,
                    details=error_text.strip(),
                    retryable=retryable,
                )

                print(
                    "YouTube FFmpeg error:"
                )

                if error_text:
                    print(
                        error_text.strip()
                    )

                self._cleanup_temp_media()

                self._mark_finished()

                return

            # -----------------------------------------
            # Loop
            # -----------------------------------------

            if self.loop:
                self._set_status(
                    "YouTube: Looping..."
                )

                continue

            # -----------------------------------------
            # Normal completion
            # -----------------------------------------

            self._set_status(
                "YouTube: Finished"
            )

            self._cleanup_temp_media()

            self._mark_finished()

            return

        self._cleanup_process()
        self._cleanup_temp_media()

        if self.stop_event.is_set():
            self._set_status(
                "YouTube: Stopped"
            )

        self._mark_finished()

    # -------------------------------------------------
    # Buffer
    # -------------------------------------------------

    def _append_buffer(
        self,
        data,
    ):
        while (
            not self.stop_event.is_set()
        ):
            with self.buffer_lock:
                if (
                    len(self.buffer)
                    < self.MAX_BUFFER_BYTES
                ):
                    self.buffer.extend(
                        data
                    )

                    return

            time.sleep(
                0.01
            )

    def read(
        self,
        size,
    ):
        with self.buffer_lock:
            available = len(
                self.buffer
            )

            if available:
                amount = min(
                    size,
                    available,
                )

                data = bytes(
                    self.buffer[
                        :amount
                    ]
                )

                del self.buffer[
                    :amount
                ]

                return data

        with self.state_lock:
            finished = (
                self.finished
            )

        if finished:
            return b""

        # Temporary starvation means silence for this
        # frame, not end-of-source.
        return (
            b"\x00"
            * size
        )

    # -------------------------------------------------
    # Process cleanup
    # -------------------------------------------------

    def _finish_process(self):
        process = self.process

        if process is None:
            return (
                None,
                "",
            )

        try:
            return_code = (
                process.wait(
                    timeout=2
                )
            )

        except subprocess.TimeoutExpired:
            try:
                process.kill()

            except Exception:
                pass

            try:
                return_code = (
                    process.wait(
                        timeout=1
                    )
                )

            except Exception:
                return_code = None

        error_text = (
            self._read_stderr()
        )

        self._cleanup_process()

        return (
            return_code,
            error_text,
        )

    def _read_stderr(self):
        if self.stderr_file is None:
            return ""

        try:
            self.stderr_file.flush()
            self.stderr_file.seek(0)

            raw = (
                self.stderr_file.read()
            )

            if isinstance(
                raw,
                bytes,
            ):
                return raw.decode(
                    "utf-8",
                    errors="replace",
                )

            return str(raw)

        except Exception:
            return ""

    def _cleanup_process(self):
        process = self.process

        self.process = None

        if process is not None:
            try:
                if (
                    process.poll()
                    is None
                ):
                    process.kill()

            except Exception:
                pass

            try:
                if (
                    process.stdout
                    is not None
                ):
                    process.stdout.close()

            except Exception:
                pass

            try:
                process.wait(
                    timeout=1
                )

            except Exception:
                pass

        stderr_file = (
            self.stderr_file
        )

        self.stderr_file = None

        if stderr_file is not None:
            try:
                stderr_file.close()

            except Exception:
                pass

    # -------------------------------------------------
    # Temporary media cleanup
    # -------------------------------------------------

    def _cleanup_temp_media(self):
        self.media_file = None

        temp_dir = (
            self.temp_dir
        )

        self.temp_dir = None

        if (
            temp_dir
            and os.path.isdir(
                temp_dir
            )
        ):
            try:
                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True,
                )

            except Exception:
                pass

    # -------------------------------------------------
    # Utility
    # -------------------------------------------------

    def _wait_or_stop(
        self,
        seconds,
    ):
        return self.stop_event.wait(
            seconds
        )

    def _mark_finished(self):
        with self.state_lock:
            self.finished = True

    # -------------------------------------------------
    # Stop
    # -------------------------------------------------

    def stop(self):
        self.stop_event.set()

        self._cleanup_process()

        with self.state_lock:
            self.finished = True

        with self.buffer_lock:
            self.buffer.clear()

        self._cleanup_temp_media()

        self._set_status(
            "YouTube: Stopped"
        )