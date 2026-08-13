from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self, discord_client):
        super().__init__()

        self.discord = discord_client
        self.selected_audio_file = None

        self.setWindowTitle("Dark Between Audio")
        self.resize(700, 500)

        self.guild_label = QLabel("Server")
        self.guild_combo = QComboBox()

        self.channel_label = QLabel("Voice Channel")
        self.channel_combo = QComboBox()

        self.status_label = QLabel("Discord: Connecting...")

        self.join_button = QPushButton("Join Channel")
        self.leave_button = QPushButton("Leave Channel")

        self.file_label = QLabel("No sound selected")

        self.select_sound_button = QPushButton(
            "Select Test Sound"
        )

        self.play_button = QPushButton(
            "Play Sound"
        )

        self.stop_button = QPushButton(
            "Stop Sound"
        )

        self.soundboard_label = QLabel(
            "Soundboard prototype"
        )

        discord_buttons = QHBoxLayout()
        discord_buttons.addWidget(self.join_button)
        discord_buttons.addWidget(self.leave_button)

        sound_buttons = QHBoxLayout()
        sound_buttons.addWidget(self.select_sound_button)
        sound_buttons.addWidget(self.play_button)
        sound_buttons.addWidget(self.stop_button)

        layout = QVBoxLayout()

        layout.addWidget(self.status_label)

        layout.addWidget(self.guild_label)
        layout.addWidget(self.guild_combo)

        layout.addWidget(self.channel_label)
        layout.addWidget(self.channel_combo)

        layout.addLayout(discord_buttons)

        layout.addStretch()

        layout.addWidget(self.soundboard_label)
        layout.addWidget(self.file_label)
        layout.addLayout(sound_buttons)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.guild_combo.currentIndexChanged.connect(
            self.guild_changed
        )

        self.join_button.clicked.connect(
            self.join_channel
        )

        self.leave_button.clicked.connect(
            self.leave_channel
        )

        self.select_sound_button.clicked.connect(
            self.select_sound
        )

        self.play_button.clicked.connect(
            self.play_sound
        )

        self.stop_button.clicked.connect(
            self.stop_sound
        )

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_discord)
        self.timer.start(500)

        self.guilds_loaded = False

    def check_discord(self):
        if not self.discord.client.is_ready():
            return

        self.status_label.setText(
            f"Discord: Connected as {self.discord.client.user}"
        )

        if not self.guilds_loaded:
            self.load_guilds()
            self.guilds_loaded = True

    def load_guilds(self):
        self.guild_combo.clear()

        for guild in self.discord.get_guilds():
            self.guild_combo.addItem(
                guild["name"],
                guild["id"],
            )

    def guild_changed(self):
        guild_id = self.guild_combo.currentData()

        self.channel_combo.clear()

        if guild_id is None:
            return

        channels = self.discord.get_voice_channels(
            guild_id
        )

        for channel in channels:
            self.channel_combo.addItem(
                channel["name"],
                channel["id"],
            )

    def join_channel(self):
        channel_id = self.channel_combo.currentData()

        if channel_id is None:
            return

        self.discord.join_channel(channel_id)

    def leave_channel(self):
        guild_id = self.guild_combo.currentData()

        if guild_id is None:
            return

        self.discord.leave_channel(guild_id)

    def select_sound(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;All Files (*)",
        )

        if not filename:
            return

        self.selected_audio_file = filename
        self.file_label.setText(filename)

    def play_sound(self):
        if not self.selected_audio_file:
            self.file_label.setText(
                "Select an audio file first."
            )
            return

        guild_id = self.guild_combo.currentData()

        if guild_id is None:
            return

        self.discord.play_audio(
            guild_id,
            self.selected_audio_file,
        )

    def stop_sound(self):
        guild_id = self.guild_combo.currentData()

        if guild_id is None:
            return

        self.discord.stop_audio(guild_id)