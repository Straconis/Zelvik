import asyncio
import threading

import discord
import sounddevice as sd

from audio.input_source import InputDeviceSource
from audio.mixer import AudioMixer
from audio.source import AudioSource
from audio.youtube_source import YouTubeSource


class DiscordClient:
    def __init__(self, token):
        self.token = token

        intents = discord.Intents.default()

        self.client = discord.Client(
            intents=intents
        )

        self.loop = None
        self.thread = None

        self.ready_event = (
            threading.Event()
        )

        # One mixer per Discord server.
        self.mixers = {}

        # Source handles allow individual
        # sources to be stopped/controlled.
        #
        # guild_id:
        # {
        #     "input": source,
        #     "youtube": source,
        #     "local": [source, ...]
        # }
        self.active_sources = {}

        @self.client.event
        async def on_ready():
            print(
                f"Discord connected as "
                f"{self.client.user}"
            )

            self.ready_event.set()

    # -------------------------------------------------
    # Discord thread
    # -------------------------------------------------

    def start(self):
        self.thread = threading.Thread(
            target=self._run_bot,
            daemon=True,
        )

        self.thread.start()

    def _run_bot(self):
        self.loop = (
            asyncio.new_event_loop()
        )

        asyncio.set_event_loop(
            self.loop
        )

        try:
            self.loop.run_until_complete(
                self.client.start(
                    self.token
                )
            )

        finally:
            self.loop.close()

    def wait_until_ready(
        self,
        timeout=10,
    ):
        return self.ready_event.wait(
            timeout
        )

    # -------------------------------------------------
    # Servers / channels
    # -------------------------------------------------

    def get_guilds(self):
        if not self.client.is_ready():
            return []

        return [
            {
                "id": guild.id,
                "name": guild.name,
            }
            for guild
            in self.client.guilds
        ]

    def get_voice_channels(
        self,
        guild_id,
    ):
        guild = self.client.get_guild(
            guild_id
        )

        if guild is None:
            return []

        return [
            {
                "id": channel.id,
                "name": channel.name,
            }
            for channel
            in guild.voice_channels
        ]

    # -------------------------------------------------
    # Audio-device discovery
    # -------------------------------------------------

    def get_audio_input_devices(self):
        devices = sd.query_devices()

        # Prefer Windows WASAPI because it gives us
        # a cleaner modern Windows device path.
        #
        # Fall back to MME / DirectSound if needed.
        priorities = {
            "Windows WASAPI": 0,
            "MME": 1,
            "Windows DirectSound": 2,
            "Windows WDM-KS": 3,
        }

        candidates = []

        for device_id, device in enumerate(
            devices
        ):
            if (
                device["max_input_channels"]
                <= 0
            ):
                continue

            try:
                host_api = (
                    sd.query_hostapis(
                        device["hostapi"]
                    )["name"]
                )
            except Exception:
                host_api = "Unknown"

            candidates.append(
                {
                    "id": device_id,
                    "name": device["name"],
                    "channels": device[
                        "max_input_channels"
                    ],
                    "samplerate": device[
                        "default_samplerate"
                    ],
                    "host_api": host_api,
                    "priority": priorities.get(
                        host_api,
                        99,
                    ),
                }
            )

        candidates.sort(
            key=lambda item: (
                item["name"].lower(),
                item["priority"],
            )
        )

        # Remove duplicate versions of the same
        # physical/virtual device.
        deduplicated = {}

        for device in candidates:
            key = (
                device["name"]
                .strip()
                .lower()
            )

            existing = (
                deduplicated.get(key)
            )

            if (
                existing is None
                or device["priority"]
                < existing["priority"]
            ):
                deduplicated[key] = device

        results = list(
            deduplicated.values()
        )

        results.sort(
            key=lambda item:
            item["name"].lower()
        )

        return results

    # -------------------------------------------------
    # Voice connection
    # -------------------------------------------------

    async def _join_channel(
        self,
        channel_id,
    ):
        channel = (
            self.client.get_channel(
                channel_id
            )
        )

        if channel is None:
            raise RuntimeError(
                "Voice channel not found."
            )

        guild = channel.guild

        voice_client = (
            guild.voice_client
        )

        if voice_client:
            if (
                voice_client.channel.id
                != channel.id
            ):
                await voice_client.move_to(
                    channel
                )

        else:
            await channel.connect()

        print(
            f"Joined voice channel: "
            f"{channel.name}"
        )

    def join_channel(
        self,
        channel_id,
    ):
        if self.loop is None:
            return None

        return (
            asyncio.run_coroutine_threadsafe(
                self._join_channel(
                    channel_id
                ),
                self.loop,
            )
        )

    async def _leave_channel(
        self,
        guild_id,
    ):
        guild = self.client.get_guild(
            guild_id
        )

        if guild is None:
            return

        self._stop_all_sources(
            guild_id
        )

        mixer = self.mixers.pop(
            guild_id,
            None,
        )

        if mixer:
            mixer.stop_all()

        if guild.voice_client:
            await (
                guild.voice_client
                .disconnect()
            )

        print(
            f"Left voice channel: "
            f"{guild.name}"
        )

    def leave_channel(
        self,
        guild_id,
    ):
        if self.loop is None:
            return None

        return (
            asyncio.run_coroutine_threadsafe(
                self._leave_channel(
                    guild_id
                ),
                self.loop,
            )
        )

    # -------------------------------------------------
    # Mixer
    # -------------------------------------------------

    def _get_mixer(
        self,
        guild_id,
    ):
        if guild_id not in self.mixers:
            self.mixers[
                guild_id
            ] = AudioMixer()

        return self.mixers[
            guild_id
        ]

    def _get_source_state(
        self,
        guild_id,
    ):
        if (
            guild_id
            not in self.active_sources
        ):
            self.active_sources[
                guild_id
            ] = {
                "input": None,
                "youtube": None,
                "local": [],
            }

        return self.active_sources[
            guild_id
        ]

    async def _start_mixer(
        self,
        guild_id,
    ):
        guild = self.client.get_guild(
            guild_id
        )

        if guild is None:
            raise RuntimeError(
                "Server not found."
            )

        voice_client = (
            guild.voice_client
        )

        if voice_client is None:
            raise RuntimeError(
                "The bot must join a voice "
                "channel first."
            )

        mixer = self._get_mixer(
            guild_id
        )

        if not voice_client.is_playing():
            voice_client.play(
                mixer,
                after=lambda error: print(
                    (
                        "Mixer stopped with "
                        f"error: {error}"
                    )
                    if error
                    else "Mixer stopped."
                ),
            )

    # -------------------------------------------------
    # External audio input
    # -------------------------------------------------

    async def _start_audio_input(
        self,
        guild_id,
        device_id,
        volume=1.0,
    ):
        await self._start_mixer(
            guild_id
        )

        mixer = self._get_mixer(
            guild_id
        )

        state = self._get_source_state(
            guild_id
        )

        # Only allow one external input
        # source at a time.
        old_source = state["input"]

        if old_source:
            mixer.remove_source(
                old_source
            )

        source = InputDeviceSource(
            device_id=device_id,
            volume=volume,
        )

        mixer.add_source(
            source
        )

        state["input"] = source

        print(
            f"External input started: "
            f"{device_id}"
        )

        return source

    def start_audio_input(
        self,
        guild_id,
        device_id,
        volume=1.0,
    ):
        if self.loop is None:
            return None

        return (
            asyncio.run_coroutine_threadsafe(
                self._start_audio_input(
                    guild_id,
                    device_id,
                    volume,
                ),
                self.loop,
            )
        )

    def stop_audio_input(
        self,
        guild_id,
    ):
        state = self._get_source_state(
            guild_id
        )

        source = state["input"]

        if source is None:
            return

        mixer = self.mixers.get(
            guild_id
        )

        if mixer:
            mixer.remove_source(
                source
            )

        state["input"] = None

        print(
            "External input stopped."
        )

    def set_input_volume(
        self,
        guild_id,
        volume,
    ):
        state = self._get_source_state(
            guild_id
        )

        source = state["input"]

        if source:
            source.volume = max(
                0.0,
                float(volume),
            )

    # -------------------------------------------------
    # YouTube
    # -------------------------------------------------

    async def _play_youtube(
        self,
        guild_id,
        youtube_url,
        volume=1.0,
        loop=False,
        start_time=None,
        stop_time=None,
    ):
        await self._start_mixer(
            guild_id
        )

        mixer = self._get_mixer(
            guild_id
        )

        state = self._get_source_state(
            guild_id
        )

        # One YouTube stream at a time.
        old_source = state[
            "youtube"
        ]

        if old_source:
            mixer.remove_source(
                old_source
            )

        source = YouTubeSource(
            youtube_url=youtube_url,
            volume=volume,
            loop=loop,
            start_time=start_time,
            stop_time=stop_time,
        )

        mixer.add_source(
            source
        )

        state["youtube"] = source

        print(
            f"YouTube source started: "
            f"{youtube_url}"
        )

        return source

    def play_youtube(
        self,
        guild_id,
        youtube_url,
        volume=1.0,
        loop=False,
        start_time=None,
        stop_time=None,
    ):
        if self.loop is None:
            return None

        return (
            asyncio.run_coroutine_threadsafe(
                self._play_youtube(
                    guild_id,
                    youtube_url,
                    volume,
                    loop,
                    start_time,
                    stop_time,
                ),
                self.loop,
            )
        )

    def stop_youtube(
        self,
        guild_id,
    ):
        state = self._get_source_state(
            guild_id
        )

        source = state[
            "youtube"
        ]

        if source is None:
            return

        mixer = self.mixers.get(
            guild_id
        )

        if mixer:
            mixer.remove_source(
                source
            )

        state["youtube"] = None

        print(
            "YouTube stopped."
        )

    def set_youtube_volume(
        self,
        guild_id,
        volume,
    ):
        state = self._get_source_state(
            guild_id
        )

        source = state[
            "youtube"
        ]

        if source:
            source.volume = max(
                0.0,
                float(volume),
            )

    # -------------------------------------------------
    # Local files
    # -------------------------------------------------

    async def _play_mixed_audio(
        self,
        guild_id,
        filename,
        volume=1.0,
        loop=False,
    ):
        await self._start_mixer(
            guild_id
        )

        mixer = self._get_mixer(
            guild_id
        )

        state = self._get_source_state(
            guild_id
        )

        source = AudioSource(
            filename=filename,
            volume=volume,
            loop=loop,
        )

        mixer.add_source(
            source
        )

        state["local"].append(
            source
        )

        print(
            f"Local audio started: "
            f"{filename}"
        )

        return source

    def play_mixed_audio(
        self,
        guild_id,
        filename,
        volume=1.0,
        loop=False,
    ):
        if self.loop is None:
            return None

        return (
            asyncio.run_coroutine_threadsafe(
                self._play_mixed_audio(
                    guild_id,
                    filename,
                    volume,
                    loop,
                ),
                self.loop,
            )
        )

    def stop_local_audio(
        self,
        guild_id,
    ):
        state = self._get_source_state(
            guild_id
        )

        mixer = self.mixers.get(
            guild_id
        )

        sources = list(
            state["local"]
        )

        state["local"].clear()

        if mixer:
            for source in sources:
                mixer.remove_source(
                    source
                )

        print(
            "Local audio stopped."
        )

    def set_local_volume(
        self,
        guild_id,
        volume,
    ):
        state = self._get_source_state(
            guild_id
        )

        volume = max(
            0.0,
            float(volume),
        )

        for source in state[
            "local"
        ]:
            source.volume = volume

    # -------------------------------------------------
    # Master controls
    # -------------------------------------------------

    def set_master_volume(
        self,
        guild_id,
        volume,
    ):
        mixer = self._get_mixer(
            guild_id
        )

        mixer.set_master_volume(
            volume
        )

    def _stop_all_sources(
        self,
        guild_id,
    ):
        state = (
            self.active_sources.get(
                guild_id
            )
        )

        if state is None:
            return

        state["input"] = None
        state["youtube"] = None
        state["local"].clear()

    def stop_all_audio(
        self,
        guild_id,
    ):
        mixer = self.mixers.get(
            guild_id
        )

        if mixer:
            mixer.stop_all()

        self._stop_all_sources(
            guild_id
        )

        print(
            "Stopped all audio."
        )

    # -------------------------------------------------
    # Shutdown
    # -------------------------------------------------

    async def _shutdown(self):
        print(
            "Shutting down Discord client..."
        )

        for mixer in list(
            self.mixers.values()
        ):
            try:
                mixer.stop_all()
            except Exception as error:
                print(
                    "Mixer shutdown error: "
                    f"{error}"
                )

        self.mixers.clear()
        self.active_sources.clear()

        for voice_client in list(
            self.client.voice_clients
        ):
            try:
                await (
                    voice_client
                    .disconnect()
                )

            except Exception as error:
                print(
                    "Voice disconnect error: "
                    f"{error}"
                )

        if not self.client.is_closed():
            await self.client.close()

        print(
            "Discord client shut down."
        )

    def shutdown(self):
        if self.loop is None:
            return

        if self.loop.is_closed():
            return

        future = (
            asyncio.run_coroutine_threadsafe(
                self._shutdown(),
                self.loop,
            )
        )

        try:
            future.result(
                timeout=5
            )

        except Exception as error:
            print(
                f"Shutdown warning: "
                f"{error}"
            )

        if self.thread:
            self.thread.join(
                timeout=5
            )