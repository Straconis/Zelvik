import queue
import threading

import sounddevice as sd


class InputDeviceSource:
    def __init__(
        self,
        device_id,
        volume=1.0,
        samplerate=48000,
        channels=2,
    ):
        self.device_id = device_id
        self.volume = volume
        self.samplerate = samplerate
        self.channels = channels

        self.finished = False
        self.stream = None

        self.audio_queue = queue.Queue()
        self.buffer = bytearray()

        self.lock = threading.RLock()

    def _callback(
        self,
        indata,
        frames,
        time,
        status,
    ):
        if status:
            print(
                f"Input device status: {status}"
            )

        self.audio_queue.put(
            bytes(indata)
        )

    def start(self):
        with self.lock:
            if self.stream is not None:
                return

            self.finished = False

            self.stream = sd.RawInputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="int16",
                device=self.device_id,
                callback=self._callback,
            )

            self.stream.start()

            print(
                f"Started audio input device "
                f"{self.device_id}"
            )

    def read(self, size):
        if self.finished:
            return b""

        while len(self.buffer) < size:
            try:
                data = self.audio_queue.get(
                    timeout=0.05
                )
                self.buffer.extend(data)

            except queue.Empty:
                break

        if not self.buffer:
            return b"\x00" * size

        output = bytes(
            self.buffer[:size]
        )

        del self.buffer[:size]

        if len(output) < size:
            output += b"\x00" * (
                size - len(output)
            )

        return output

    def stop(self):
        with self.lock:
            self.finished = True

            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception as error:
                    print(
                        f"Audio input stop error: "
                        f"{error}"
                    )

                self.stream = None

            self.buffer.clear()

            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break