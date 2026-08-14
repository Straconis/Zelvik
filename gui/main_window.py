from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import (
    QApplication,
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

        self.settings = QSettings(
            "DarkBetween",
            "DarkBetweenAudio",
        )

        self.selected_audio_file = None
        self.guilds_loaded = False
        self.audio_devices_loaded = False
        self.shutting_down = False

        self.setWindowTitle("Dark Between Audio")
        self.resize(760, 620)

        # -------------------------------------------------
        # Discord status
        # -------------------------------------------------

        self.status_label = QLabel(
            "Discord: Connecting..."
        )

        # -------------------------------------------------
        # Server selection
        # -------------------------------------------------

        self.guild_label = QLabel("Server")
        self.guild_combo = QComboBox()

        # -------------------------------------------------
        # Voice channel selection
        # -------------------------------------------------

        self.channel_label = QLabel(
            "Voice Channel"
        )

        self.channel_combo = QComboBox()

        self.join_button = QPushButton(
            "Join Channel"
        )

        self.leave_button = QPushButton(
            "Leave Channel"
        )

        # -------------------------------------------------
        # External audio input
        # -------------------------------------------------

        self.input_section_label = QLabel(
            "External Audio Input"
        )

        self.input_device_label = QLabel(
            "Input Device"
        )

        self.input_device_combo = QComboBox()

        self.start_input_button = QPushButton(
            "Start Input"
        )

        self.stop_input_button = QPushButton(
            "Stop All Audio"
        )

        # -------------------------------------------------
        # Local file player
        # -------------------------------------------------

        self.soundboard_label = QLabel(
            "Local File Playback"
        )

        self.file_label = QLabel(
            "No sound selected"
        )

        self.select_sound_button = QPushButton(
            "Select Sound"
        )

        self.play_button = QPushButton(
            "Play Sound"
        )

        self.stop_button = QPushButton(
            "Stop All Audio"
        )

        # -------------------------------------------------
        # Exit
        # -------------------------------------------------

        self.exit_button = QPushButton(
            "Exit"
        )

        # -------------------------------------------------
        # Layouts
        # -------------------------------------------------

        discord_buttons = QHBoxLayout()

        discord_buttons.addWidget(
            self.join_button
        )

        discord_buttons.addWidget(
            self.leave_button
        )

        input_buttons = QHBoxLayout()

        input_buttons.addWidget(
            self.start_input_button
        )

        input_buttons.addWidget(
            self.stop_input_button
        )

        file_buttons = QHBoxLayout()

        file_buttons.addWidget(
            self.select_sound_button
        )

        file_buttons.addWidget(
            self.play_button
        )

        file_buttons.addWidget(
            self.stop_button
        )

        exit_layout = QHBoxLayout()

        exit_layout.addStretch()

        exit_layout.addWidget(
            self.exit_button
        )

        layout = QVBoxLayout()

        # Discord
        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.guild_label
        )

        layout.addWidget(
            self.guild_combo
        )

        layout.addWidget(
            self.channel_label
        )

        layout.addWidget(
            self.channel_combo
        )

        layout.addLayout(
            discord_buttons
        )

        layout.addSpacing(20)

        # External input
        layout.addWidget(
            self.input_section_label
        )

        layout.addWidget(
            self.input_device_label
        )

        layout.addWidget(
            self.input_device_combo
        )

        layout.addLayout(
            input_buttons
        )

        layout.addSpacing(20)

        # Local file playback
        layout.addWidget(
            self.soundboard_label
        )

        layout.addWidget(
            self.file_label
        )

        layout.addLayout(
            file_buttons
        )

        layout.addStretch()

        layout.addLayout(
            exit_layout
        )

        container = QWidget()

        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )

        # -------------------------------------------------
        # Signals
        # -------------------------------------------------

        self.guild_combo.currentIndexChanged.connect(
            self.guild_changed
        )

        self.join_button.clicked.connect(
            self.join_channel
        )

        self.leave_button.clicked.connect(
            self.leave_channel
        )

        self.start_input_button.clicked.connect(
            self.start_audio_input
        )

        self.stop_input_button.clicked.connect(
            self.stop_all_audio
        )

        self.input_device_combo.currentIndexChanged.connect(
            self.save_audio_device
        )

        self.select_sound_button.clicked.connect(
            self.select_sound
        )

        self.play_button.clicked.connect(
            self.play_sound
        )

        self.stop_button.clicked.connect(
            self.stop_all_audio
        )

        self.exit_button.clicked.connect(
            self.close
        )

        # -------------------------------------------------
        # Poll Discord status
        # -------------------------------------------------

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.check_discord
        )

        self.timer.start(500)

    # -------------------------------------------------
    # Discord connection/status
    # -------------------------------------------------

    def check_discord(self):
        if self.shutting_down:
            return

        if not self.discord.client.is_ready():
            return

        self.status_label.setText(
            f"Discord: Connected as "
            f"{self.discord.client.user}"
        )

        if not self.guilds_loaded:
            self.load_guilds()
            self.guilds_loaded = True

        if not self.audio_devices_loaded:
            self.load_audio_devices()
            self.audio_devices_loaded = True

    # -------------------------------------------------
    # Discord server/channel loading
    # -------------------------------------------------

    def load_guilds(self):
        self.guild_combo.clear()

        guilds = self.discord.get_guilds()

        for guild in guilds:
            self.guild_combo.addItem(
                guild["name"],
                guild["id"],
            )

    def guild_changed(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        self.channel_combo.clear()

        if guild_id is None:
            return

        channels = (
            self.discord.get_voice_channels(
                guild_id
            )
        )

        for channel in channels:
            self.channel_combo.addItem(
                channel["name"],
                channel["id"],
            )

    # -------------------------------------------------
    # Discord voice controls
    # -------------------------------------------------

    def join_channel(self):
        channel_id = (
            self.channel_combo.currentData()
        )

        if channel_id is None:
            return

        self.discord.join_channel(
            channel_id
        )

    def leave_channel(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.leave_channel(
            guild_id
        )

    # -------------------------------------------------
    # External audio devices
    # -------------------------------------------------

    def load_audio_devices(self):
        self.input_device_combo.blockSignals(
            True
        )

        self.input_device_combo.clear()

        devices = (
            self.discord.get_audio_input_devices()
        )

        saved_device_name = (
            self.settings.value(
                "audio/input_device_name",
                "",
                type=str,
            )
        )

        saved_index = -1

        for device in devices:
            display_name = (
                f"{device['name']} "
                f"({device['channels']} ch)"
            )

            self.input_device_combo.addItem(
                display_name,
                device["id"],
            )

            if display_name == saved_device_name:
                saved_index = (
                    self.input_device_combo.count()
                    - 1
                )

        if saved_index >= 0:
            self.input_device_combo.setCurrentIndex(
                saved_index
            )

        self.input_device_combo.blockSignals(
            False
        )

    def save_audio_device(self):
        device_name = (
            self.input_device_combo.currentText()
        )

        if not device_name:
            return

        self.settings.setValue(
            "audio/input_device_name",
            device_name,
        )

        self.settings.sync()

    def start_audio_input(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        device_id = (
            self.input_device_combo.currentData()
        )

        if guild_id is None:
            return

        if device_id is None:
            return

        # Save the selected input before starting.
        self.save_audio_device()

        self.discord.start_audio_input(
            guild_id,
            device_id,
            volume=1.0,
        )

    # -------------------------------------------------
    # Local file player
    # -------------------------------------------------

    def select_sound(self):
        filename, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Select Audio File",
                "",
                (
                    "Audio Files "
                    "(*.mp3 *.wav *.ogg *.flac);;"
                    "All Files (*)"
                ),
            )
        )

        if not filename:
            return

        self.selected_audio_file = filename

        self.file_label.setText(
            filename
        )

    def play_sound(self):
        if not self.selected_audio_file:
            self.file_label.setText(
                "Select an audio file first."
            )
            return

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.play_mixed_audio(
            guild_id,
            self.selected_audio_file,
            volume=1.0,
            loop=False,
        )

    # -------------------------------------------------
    # Stop all mixer audio
    # -------------------------------------------------

    def stop_all_audio(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.stop_all_audio(
            guild_id
        )

    # -------------------------------------------------
    # Shutdown
    # -------------------------------------------------

    def closeEvent(self, event):
        if self.shutting_down:
            event.accept()
            return

        self.shutting_down = True

        self.timer.stop()

        self.status_label.setText(
            "Discord: Shutting down..."
        )

        self.join_button.setEnabled(
            False
        )

        self.leave_button.setEnabled(
            False
        )

        self.start_input_button.setEnabled(
            False
        )

        self.stop_input_button.setEnabled(
            False
        )

        self.input_device_combo.setEnabled(
            False
        )

        self.select_sound_button.setEnabled(
            False
        )

        self.play_button.setEnabled(
            False
        )

        self.stop_button.setEnabled(
            False
        )

        self.exit_button.setEnabled(
            False
        )

        QApplication.processEvents()

        self.discord.shutdown()

        event.accept()