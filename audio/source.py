import os
import subprocess
import threading


class AudioSource:
    def __init__(
        self,
        filename,
        volume=1.0,
        loop=False,
    ):
        self.filename = filename
        self.volume = volume
        self.loop = loop

        self.process = None
        self.lock = threading.RLock()
        self.finished = False

    # -------------------------------------------------
    # FFmpeg process options
    # -------------------------------------------------

    def _subprocess_creation_flags(self):
        """
        Prevent FFmpeg from opening its own console window
        when Zelvik is packaged as a Windows
        --windowed executable.
        """

        if os.name == "nt":
            return subprocess.CREATE_NO_WINDOW

        return 0

    # -------------------------------------------------
    # Start
    # -------------------------------------------------

    def start(self):
        with self.lock:
            self._start_process()

    def _start_process(self):
        command = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "quiet",
            "-i",
            self.filename,
            "-f",
            "s16le",
            "-ar",
            "48000",
            "-ac",
            "2",
            "pipe:1",
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            bufsize=0,
            creationflags=(
                self._subprocess_creation_flags()
            ),
        )

        self.finished = False

    # -------------------------------------------------
    # Read
    # -------------------------------------------------

    def read(
        self,
        size,
    ):
        with self.lock:
            if self.finished:
                return b""

            if self.process is None:
                self._start_process()

            data = self.process.stdout.read(
                size
            )

            if data:
                return data

            if self.loop:
                self.stop()
                self._start_process()

                return self.process.stdout.read(
                    size
                )

            self.finished = True

            return b""

    # -------------------------------------------------
    # Stop
    # -------------------------------------------------

    def stop(self):
        with self.lock:
            if self.process:
                try:
                    self.process.kill()

                except Exception:
                    pass

                try:
                    self.process.wait(
                        timeout=1
                    )

                except Exception:
                    pass

                try:
                    if (
                        self.process.stdout
                        is not None
                    ):
                        self.process.stdout.close()

                except Exception:
                    pass

                self.process = None

            self.finished = True