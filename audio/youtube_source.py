import subprocess
import threading

import yt_dlp


class YouTubeSource:
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

        self.process = None
        self.finished = False
        self.lock = threading.RLock()

        self.stream_url = None
        self.http_headers = {}
        self.title = None

    def _resolve(self):
        print(
            f"Resolving YouTube URL: "
            f"{self.youtube_url}"
        )

        options = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                self.youtube_url,
                download=False,
            )

        if not info:
            raise RuntimeError(
                "yt-dlp returned no video information."
            )

        self.title = info.get(
            "title",
            "YouTube Audio",
        )

        self.stream_url = info.get("url")

        if not self.stream_url:
            raise RuntimeError(
                "yt-dlp did not return a playable URL."
            )

        self.http_headers = info.get(
            "http_headers",
            {},
        )

        print(
            f"YouTube resolved: {self.title}"
        )

    def start(self):
        with self.lock:
            if self.process is not None:
                return

            self.finished = False

            self._resolve()
            self._start_ffmpeg()

    def _build_header_string(self):
        header_lines = []

        for key, value in self.http_headers.items():
            header_lines.append(
                f"{key}: {value}"
            )

        if not header_lines:
            return None

        return "\r\n".join(
            header_lines
        ) + "\r\n"

    def _start_ffmpeg(self):
        command = [
            "ffmpeg",
            "-loglevel",
            "warning",
        ]

        header_string = (
            self._build_header_string()
        )

        if header_string:
            command.extend(
                [
                    "-headers",
                    header_string,
                ]
            )

        if (
            self.start_time is not None
            and self.start_time > 0
        ):
            command.extend(
                [
                    "-ss",
                    str(self.start_time),
                ]
            )

        command.extend(
            [
                "-i",
                self.stream_url,
            ]
        )

        if self.stop_time is not None:
            start = (
                self.start_time
                if self.start_time is not None
                else 0
            )

            duration = (
                self.stop_time - start
            )

            if duration > 0:
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

        print(
            f"Starting FFmpeg for: "
            f"{self.title}"
        )

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=None,
            bufsize=0,
        )

    def read(self, size):
        with self.lock:
            if self.finished:
                return b""

            if self.process is None:
                self.start()

            data = self.process.stdout.read(
                size
            )

            if data:
                return data

            return_code = (
                self.process.poll()
            )

            if return_code is not None:
                print(
                    f"YouTube FFmpeg exited "
                    f"with code {return_code}"
                )

            if self.loop:
                print(
                    "Restarting YouTube loop..."
                )

                self._kill_process()

                self.stream_url = None
                self.http_headers = {}

                self._resolve()
                self._start_ffmpeg()

                return (
                    self.process.stdout.read(
                        size
                    )
                )

            self.finished = True
            self._kill_process()

            return b""

    def _kill_process(self):
        if self.process is None:
            return

        try:
            self.process.kill()
        except Exception:
            pass

        try:
            self.process.wait(
                timeout=2
            )
        except Exception:
            pass

        self.process = None

    def stop(self):
        with self.lock:
            self.finished = True
            self._kill_process()