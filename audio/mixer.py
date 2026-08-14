import audioop
import threading

import discord


# Discord expects 20 ms frames:
#
# 48,000 samples/sec
# 0.020 sec
# 2 channels
# 2 bytes/sample
#
# = 3840 bytes
FRAME_SIZE = 3840


class AudioMixer(discord.AudioSource):
    def __init__(self):
        self.sources = []
        self.lock = threading.RLock()

        self.master_volume = 1.0

    # -------------------------------------------------
    # Sources
    # -------------------------------------------------

    def add_source(self, source):
        source.start()

        with self.lock:
            self.sources.append(source)

    def remove_source(self, source):
        if source is None:
            return

        with self.lock:
            if source in self.sources:
                self.sources.remove(source)

        try:
            source.stop()
        except Exception as error:
            print(
                f"Source stop error: {error}"
            )

    def stop_all(self):
        with self.lock:
            sources = list(self.sources)
            self.sources.clear()

        for source in sources:
            try:
                source.stop()
            except Exception as error:
                print(
                    f"Source stop error: {error}"
                )

    # -------------------------------------------------
    # Master volume
    # -------------------------------------------------

    def set_master_volume(self, volume):
        self.master_volume = max(
            0.0,
            float(volume),
        )

    # -------------------------------------------------
    # Discord AudioSource
    # -------------------------------------------------

    def read(self):
        with self.lock:
            active_sources = list(
                self.sources
            )

        # Discord still needs valid PCM frames
        # when nothing is playing.
        if not active_sources:
            return (
                b"\x00" * FRAME_SIZE
            )

        mixed = (
            b"\x00" * FRAME_SIZE
        )

        finished_sources = []

        for source in active_sources:
            try:
                data = source.read(
                    FRAME_SIZE
                )

            except Exception as error:
                print(
                    f"Audio source read error: "
                    f"{error}"
                )

                finished_sources.append(
                    source
                )

                continue

            if not data:
                finished_sources.append(
                    source
                )

                continue

            # Make every source exactly one
            # Discord frame long.
            if len(data) < FRAME_SIZE:
                data += (
                    b"\x00"
                    * (
                        FRAME_SIZE
                        - len(data)
                    )
                )

            elif len(data) > FRAME_SIZE:
                data = data[
                    :FRAME_SIZE
                ]

            # Per-source volume
            source_volume = getattr(
                source,
                "volume",
                1.0,
            )

            data = audioop.mul(
                data,
                2,
                source_volume,
            )

            # Mix source into final frame.
            mixed = audioop.add(
                mixed,
                data,
                2,
            )

        # Clean up completed sources.
        for source in finished_sources:
            with self.lock:
                if source in self.sources:
                    self.sources.remove(
                        source
                    )

            try:
                source.stop()
            except Exception:
                pass

        # Master volume
        if self.master_volume != 1.0:
            mixed = audioop.mul(
                mixed,
                2,
                self.master_volume,
            )

        return mixed

    def is_opus(self):
        return False

    def cleanup(self):
        self.stop_all()