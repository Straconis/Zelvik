import asyncio
import threading

import discord
import sounddevice as sd

from audio.mixer import AudioMixer
from audio.source import AudioSource
from audio.input_source import InputDeviceSource


class DiscordClient:
    def __init__(self, token):
        self.token = token

        intents = discord.Intents.default()
        self.client = discord.Client(intents=intents)

        self.loop = None
        self.thread = None

        self.ready_event = threading.Event()

        # One mixer per Discord server
        self.mixers = {}

        @self.client.event
        async def on_ready():
            print(f"Discord connected as {self.client.user}")
            self.ready_event.set()

    def start(self):
        self.thread = threading.Thread(
            target=self._run_bot,
            daemon=True,
        )
        self.thread.start()

    def _run_bot(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(
                self.client.start(self.token)
            )
        finally:
            self.loop.close()

    def wait_until_ready(self, timeout=10):
        return self.ready_event.wait(timeout)

    def get_guilds(self):
        if not self.client.is_ready():
            return []

        return [
            {
                "id": guild.id,
                "name": guild.name,
            }
            for guild in self.client.guilds
        ]

    def get_voice_channels(self, guild_id):
        guild = self.client.get_guild(guild_id)

        if guild is None:
            return []

        return [
            {
                "id": channel.id,
                "name": channel.name,
            }
            for channel in guild.voice_channels
        ]

    def get_audio_input_devices(self):
        devices = sd.query_devices()

        inputs = []

        for device_id, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                inputs.append(
                    {
                        "id": device_id,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "samplerate": device["default_samplerate"],
                    }
                )

        return inputs

    async def _join_channel(self, channel_id):
        channel = self.client.get_channel(channel_id)

        if channel is None:
            raise RuntimeError("Voice channel not found.")

        guild = channel.guild
        voice_client = guild.voice_client

        if voice_client:
            if voice_client.channel.id != channel.id:
                await voice_client.move_to(channel)
        else:
            await channel.connect()

        print(f"Joined voice channel: {channel.name}")

    def join_channel(self, channel_id):
        if self.loop is None:
            return None

        return asyncio.run_coroutine_threadsafe(
            self._join_channel(channel_id),
            self.loop,
        )

    async def _leave_channel(self, guild_id):
        guild = self.client.get_guild(guild_id)

        if guild is None:
            return

        mixer = self.mixers.pop(guild_id, None)

        if mixer:
            mixer.stop_all()

        if guild.voice_client:
            await guild.voice_client.disconnect()

        print(
            f"Left voice channel for server: "
            f"{guild.name}"
        )

    def leave_channel(self, guild_id):
        if self.loop is None:
            return None

        return asyncio.run_coroutine_threadsafe(
            self._leave_channel(guild_id),
            self.loop,
        )

    def _get_mixer(self, guild_id):
        if guild_id not in self.mixers:
            self.mixers[guild_id] = AudioMixer()

        return self.mixers[guild_id]

    async def _start_mixer(self, guild_id):
        guild = self.client.get_guild(guild_id)

        if guild is None:
            raise RuntimeError("Server not found.")

        voice_client = guild.voice_client

        if voice_client is None:
            raise RuntimeError(
                "The bot is not connected to a voice channel."
            )

        mixer = self._get_mixer(guild_id)

        if not voice_client.is_playing():
            voice_client.play(
                mixer,
                after=lambda error: print(
                    f"Mixer stopped with error: {error}"
                    if error
                    else "Mixer stopped."
                ),
            )

    async def _play_mixed_audio(
        self,
        guild_id,
        filename,
        volume=1.0,
        loop=False,
    ):
        await self._start_mixer(guild_id)

        mixer = self._get_mixer(guild_id)

        source = AudioSource(
            filename=filename,
            volume=volume,
            loop=loop,
        )

        mixer.add_source(source)

        print(
            f"Added local file to mixer: {filename} "
            f"(volume={volume}, loop={loop})"
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

        return asyncio.run_coroutine_threadsafe(
            self._play_mixed_audio(
                guild_id,
                filename,
                volume,
                loop,
            ),
            self.loop,
        )

    async def _start_audio_input(
        self,
        guild_id,
        device_id,
        volume=1.0,
    ):
        await self._start_mixer(guild_id)

        mixer = self._get_mixer(guild_id)

        source = InputDeviceSource(
            device_id=device_id,
            volume=volume,
        )

        mixer.add_source(source)

        print(
            f"Added input device {device_id} "
            f"to mixer (volume={volume})"
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

        return asyncio.run_coroutine_threadsafe(
            self._start_audio_input(
                guild_id,
                device_id,
                volume,
            ),
            self.loop,
        )

    def stop_all_audio(self, guild_id):
        mixer = self.mixers.get(guild_id)

        if mixer:
            mixer.stop_all()
            print("Stopped all audio.")

    async def _shutdown(self):
        print("Shutting down Discord client...")

        for mixer in list(self.mixers.values()):
            try:
                mixer.stop_all()
            except Exception as error:
                print(
                    f"Mixer shutdown error: {error}"
                )

        self.mixers.clear()

        for voice_client in list(
            self.client.voice_clients
        ):
            try:
                await voice_client.disconnect()
            except Exception as error:
                print(
                    f"Voice disconnect error: {error}"
                )

        if not self.client.is_closed():
            await self.client.close()

        print("Discord client shut down.")

    def shutdown(self):
        if self.loop is None:
            return

        if self.loop.is_closed():
            return

        future = asyncio.run_coroutine_threadsafe(
            self._shutdown(),
            self.loop,
        )

        try:
            future.result(timeout=5)
        except Exception as error:
            print(
                f"Shutdown warning: {error}"
            )

        if self.thread:
            self.thread.join(timeout=5)