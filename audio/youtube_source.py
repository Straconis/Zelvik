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
    ):
        self.youtube_url = youtube_url

        self.volume = volume
        self.loop = loop

        self.start_time = start_time
        self.stop_time = stop_time

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
    # yt-dlp resolution
    # -------------------------------------------------

    def _resolve_stream(self):
        self._set_status(
            "YouTube: Resolving stream..."
        )

        ydl_options = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "cachedir": False,
        }

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

        while not self.stop_event.is_set():
            try:
                (
                    stream_url,
                    headers,
                    title,
                ) = self._resolve_stream()

            except Exception as error:
                self.last_error = str(
                    error
                )

                if (
                    retry_count
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

                self._set_status(
                    "YouTube: Failed to resolve stream."
                )

                print(
                    "YouTube resolve error: "
                    f"{error}"
                )

                self._mark_finished()

                return

            if self.stop_event.is_set():
                break

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

                self._set_status(
                    "YouTube: FFmpeg failed to start."
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

                self._set_status(
                    "YouTube: Failed — "
                    "403 after 3 retries."
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

                self._set_status(
                    "YouTube: Playback failed."
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