import asyncio
import threading

import discord


class DiscordClient:
    def __init__(self, token):
        self.token = token

        intents = discord.Intents.default()

        self.client = discord.Client(intents=intents)

        self.loop = None
        self.thread = None

        self.ready_event = threading.Event()

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

        self.loop.run_until_complete(
            self.client.start(self.token)
        )

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

    async def _join_channel(self, channel_id):
        channel = self.client.get_channel(channel_id)

        if channel is None:
            raise RuntimeError("Voice channel not found.")

        guild = channel.guild
        voice_client = guild.voice_client

        if voice_client:
            await voice_client.move_to(channel)
        else:
            await channel.connect()

    def join_channel(self, channel_id):
        if self.loop is None:
            return

        asyncio.run_coroutine_threadsafe(
            self._join_channel(channel_id),
            self.loop,
        )

    async def _leave_channel(self, guild_id):
        guild = self.client.get_guild(guild_id)

        if guild and guild.voice_client:
            await guild.voice_client.disconnect()

    def leave_channel(self, guild_id):
        if self.loop is None:
            return

        asyncio.run_coroutine_threadsafe(
            self._leave_channel(guild_id),
            self.loop,
        )

    async def _play_audio(self, guild_id, filename):
        guild = self.client.get_guild(guild_id)

        if guild is None:
            raise RuntimeError("Server not found.")

        voice_client = guild.voice_client

        if voice_client is None:
            raise RuntimeError(
                "The bot is not connected to a voice channel."
            )

        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(filename)

        voice_client.play(
            source,
            after=lambda error: print(
                f"Playback finished. Error: {error}"
                if error
                else "Playback finished."
            ),
        )

        print(f"Playing: {filename}")

    def play_audio(self, guild_id, filename):
        if self.loop is None:
            return

        future = asyncio.run_coroutine_threadsafe(
            self._play_audio(guild_id, filename),
            self.loop,
        )

        return future

    def stop_audio(self, guild_id):
        if self.loop is None:
            return

        async def _stop():
            guild = self.client.get_guild(guild_id)

            if guild and guild.voice_client:
                guild.voice_client.stop()

        return asyncio.run_coroutine_threadsafe(
            _stop(),
            self.loop,
        )