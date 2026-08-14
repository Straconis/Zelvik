import subprocess
import threading


class AudioSource:
    def __init__(self, filename, volume=1.0, loop=False):
        self.filename = filename
        self.volume = volume
        self.loop = loop

        self.process = None
        self.lock = threading.RLock()
        self.finished = False

    def start(self):
        with self.lock:
            self._start_process()

    def _start_process(self):
        command = [
            "ffmpeg",
            "-loglevel", "quiet",
            "-i", self.filename,
            "-f", "s16le",
            "-ar", "48000",
            "-ac", "2",
            "pipe:1",
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

        self.finished = False

    def read(self, size):
        with self.lock:
            if self.finished:
                return b""

            if self.process is None:
                self._start_process()

            data = self.process.stdout.read(size)

            if data:
                return data

            if self.loop:
                self.stop()
                self._start_process()
                return self.process.stdout.read(size)

            self.finished = True
            return b""

    def stop(self):
        with self.lock:
            if self.process:
                try:
                    self.process.kill()
                except Exception:
                    pass

                self.process = None

            self.finished = True