import os
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
            "private video",
            "video is private",
            "removed by the uploader",
            "has been removed",
            "not available",
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
                "message": "The selected cookies file does not exist.",
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
                "message": "Zelvik could not read the selected cookies file.",
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
                "message": "Signed-in YouTube cookies were found.",
                "details": (
                    f"Found {youtube_cookie_count} YouTube/Google cookies "
                    f"and {len(found_auth_names)} recognized sign-in cookies."
                ),
            }

        if youtube_cookie_count:
            return {
                "ok": True,
                "authenticated": False,
                "message": (
                    "YouTube cookies were found, but Zelvik could not "
                    "confirm a signed-in session."
                ),
                "details": (
                    f"Found {youtube_cookie_count} YouTube/Google cookies "
                    "but no recognized sign-in cookies."
                ),
            }

        return {
            "ok": True,
            "authenticated": False,
            "message": "No YouTube or Google cookies were found in this file.",
            "details": (
                "The file is readable, but it does not appear to contain "
                "YouTube authentication cookies."
            ),
        }

    # -------------------------------------------------
    # yt-dlp resolution
    # -------------------------------------------------

    def _resolve_stream(
        self,
        use_auth=False,
    ):
        if use_auth:
            self._set_status(
                "YouTube: Resolving stream with authentication..."
            )
        else:
            self._set_status(
                "YouTube: Resolving stream..."
            )

        ydl_options = {
            "format": "bestaudio*/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "cachedir": False,
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
                download=False,
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

        stream_url = info.get(
            "url"
        )

        if not stream_url:
            formats = info.get(
                "formats",
                [],
            )

            audio_formats = []

            for fmt in formats:
                url = fmt.get(
                    "url"
                )

                acodec = fmt.get(
                    "acodec"
                )

                vcodec = fmt.get(
                    "vcodec"
                )

                if not url:
                    continue

                if (
                    acodec
                    and acodec != "none"
                    and (
                        not vcodec
                        or vcodec == "none"
                    )
                ):
                    audio_formats.append(
                        fmt
                    )

            if not audio_formats:
                raise RuntimeError(
                    "No playable audio format was found."
                )

            audio_formats.sort(
                key=lambda fmt: (
                    fmt.get("abr") or 0,
                    fmt.get("tbr") or 0,
                ),
                reverse=True,
            )

            selected_format = (
                audio_formats[0]
            )

            stream_url = (
                selected_format["url"]
            )

            headers = (
                selected_format.get(
                    "http_headers",
                    {},
                )
            )

        else:
            headers = info.get(
                "http_headers",
                {},
            )

        title = info.get(
            "title",
            "YouTube audio",
        )

        return (
            stream_url,
            headers,
            title,
        )

    # -------------------------------------------------
    # FFmpeg
    # -------------------------------------------------

    def _build_ffmpeg_command(
        self,
        stream_url,
        headers,
    ):
        command = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
        ]

        if headers:
            header_lines = []

            for key, value in headers.items():
                if value is None:
                    continue

                header_lines.append(
                    f"{key}: {value}"
                )

            if header_lines:
                header_string = (
                    "\r\n".join(
                        header_lines
                    )
                    + "\r\n"
                )

                command.extend(
                    [
                        "-headers",
                        header_string,
                    ]
                )

        command.extend(
            [
                "-i",
                stream_url,
            ]
        )

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
        stream_url,
        headers,
    ):
        self._cleanup_process()

        self.stderr_file = (
            tempfile.TemporaryFile()
        )

        command = (
            self._build_ffmpeg_command(
                stream_url,
                headers,
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

        while not self.stop_event.is_set():
            try:
                (
                    stream_url,
                    headers,
                    title,
                ) = self._resolve_stream(
                    use_auth=use_auth
                )

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
                        "YouTube: Authentication required — "
                        "retrying with saved cookies..."
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
                        "This video requires YouTube authentication. "
                        "Import cookies.txt in Zelvik and try again."
                    )
                    retryable = False

                if (
                    retryable
                    and retry_count
                    < self.max_retries
                ):
                    retry_count += 1

                    self._set_status(
                        "YouTube: Resolve failed — "
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
                    "YouTube resolve error: "
                    f"{error}"
                )

                self._mark_finished()

                return

            if self.stop_event.is_set():
                break

            if use_auth:
                self.auth_in_use = True

                self._set_status(
                    f"YouTube: Playing (authenticated) — {title}"
                )
            else:
                self.auth_in_use = False

                self._set_status(
                    f"YouTube: Playing — {title}"
                )

            try:
                self._start_ffmpeg(
                    stream_url,
                    headers,
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

            error_lower = (
                error_text.lower()
            )

            is_403 = (
                "403" in error_lower
                or "forbidden" in error_lower
                or (
                    "access denied"
                    in error_lower
                )
            )

            # -----------------------------------------
            # 403 recovery
            # -----------------------------------------

            if is_403:
                self.last_error = (
                    error_text.strip()
                )

                if (
                    retry_count
                    < self.max_retries
                ):
                    retry_count += 1

                    self._set_status(
                        "YouTube: 403 received — "
                        "refreshing stream "
                        f"{retry_count}/"
                        f"{self.max_retries}..."
                    )

                    print(
                        "YouTube media URL returned "
                        "HTTP 403. Discarding URL and "
                        "re-resolving original video."
                    )

                    if self._wait_or_stop(
                        1.0
                    ):
                        break

                    continue

                self._set_error(
                    kind="http_403",
                    message=(
                        "YouTube denied access to the media "
                        "stream after multiple retries."
                    ),
                    details=error_text.strip(),
                    retryable=True,
                )

                print(
                    "YouTube playback failed after "
                    "all 403 retries."
                )

                if error_text:
                    print(
                        error_text.strip()
                    )

                self._mark_finished()

                return

            # -----------------------------------------
            # Other FFmpeg errors
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

                self._mark_finished()

                return

            # -----------------------------------------
            # Normal completion
            # -----------------------------------------

            if self.loop:
                retry_count = 0

                self._set_status(
                    "YouTube: Looping..."
                )

                continue

            self._set_status(
                "YouTube: Finished"
            )

            self._mark_finished()

            return

        self._cleanup_process()

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

        self._set_status(
            "YouTube: Stopped"
        )