import audioop
import threading

import discord


# Discord expects 20 ms of:
# 48,000 Hz
# stereo
# 16-bit PCM
#
# 48000 samples/sec
# * 0.020 sec
# * 2 channels
# * 2 bytes/sample
# = 3840 bytes
FRAME_SIZE = 3840


class AudioMixer(discord.AudioSource):
    def __init__(self):
        self.sources = []
        self.lock = threading.Lock()

    def add_source(self, source):
        source.start()

        with self.lock:
            self.sources.append(source)

    def remove_source(self, source):
        with self.lock:
            if source in self.sources:
                source.stop()
                self.sources.remove(source)

    def stop_all(self):
        with self.lock:
            sources = list(self.sources)
            self.sources.clear()

        for source in sources:
            source.stop()

    def read(self):
        # Take a snapshot so we're not holding the mixer
        # lock while reading from FFmpeg processes.
        with self.lock:
            active_sources = list(self.sources)

        # Discord still needs audio frames even when nothing
        # is currently making sound.
        if not active_sources:
            return b"\x00" * FRAME_SIZE

        mixed = b"\x00" * FRAME_SIZE
        finished_sources = []

        for source in active_sources:
            data = source.read(FRAME_SIZE)

            if not data:
                finished_sources.append(source)
                continue

            # FFmpeg pipes are allowed to return less data than
            # requested. Pad short reads with silence so every
            # buffer passed into audioop.add() is exactly the
            # same length.
            if len(data) < FRAME_SIZE:
                data += b"\x00" * (
                    FRAME_SIZE - len(data)
                )

            # Defensive measure: if we somehow receive more
            # than one frame, only mix the current frame.
            elif len(data) > FRAME_SIZE:
                data = data[:FRAME_SIZE]

            # Apply this source's individual volume.
            data = audioop.mul(
                data,
                2,
                source.volume,
            )

            # Mix it into the final Discord frame.
            mixed = audioop.add(
                mixed,
                data,
                2,
            )

        # Remove sounds that reached EOF.
        if finished_sources:
            with self.lock:
                for source in finished_sources:
                    if source in self.sources:
                        self.sources.remove(source)

        return mixed

    def is_opus(self):
        return False

    def cleanup(self):
        self.stop_all()