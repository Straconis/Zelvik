from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
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
        self.resize(840, 820)

        # -------------------------------------------------
        # Discord
        # -------------------------------------------------

        self.status_label = QLabel(
            "Discord: Connecting..."
        )

        self.guild_label = QLabel("Server")
        self.guild_combo = QComboBox()

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
        # YouTube
        # -------------------------------------------------

        self.youtube_section_label = QLabel(
            "YouTube"
        )

        self.youtube_url_label = QLabel(
            "YouTube URL"
        )

        self.youtube_url_input = QLineEdit()

        self.youtube_url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=..."
        )

        self.youtube_start_label = QLabel(
            "Start"
        )

        self.youtube_start_input = QLineEdit()

        self.youtube_start_input.setPlaceholderText(
            "00:00"
        )

        self.youtube_stop_label = QLabel(
            "Stop"
        )

        self.youtube_stop_input = QLineEdit()

        self.youtube_stop_input.setPlaceholderText(
            "Optional"
        )

        self.youtube_loop_checkbox = QCheckBox(
            "Loop"
        )

        self.youtube_volume_label = QLabel(
            "Volume: 100%"
        )

        self.youtube_volume_slider = QSlider(
            Qt.Horizontal
        )

        self.youtube_volume_slider.setMinimum(0)
        self.youtube_volume_slider.setMaximum(200)

        saved_youtube_volume = self.settings.value(
            "youtube/volume",
            100,
            type=int,
        )

        self.youtube_volume_slider.setValue(
            saved_youtube_volume
        )

        self.youtube_volume_label.setText(
            f"Volume: {saved_youtube_volume}%"
        )

        self.youtube_play_button = QPushButton(
            "Play YouTube"
        )

        self.youtube_stop_button = QPushButton(
            "Stop All Audio"
        )

        self.youtube_status_label = QLabel(
            ""
        )

        # -------------------------------------------------
        # Local file player
        # -------------------------------------------------

        self.local_section_label = QLabel(
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

        youtube_time_layout = QHBoxLayout()

        youtube_time_layout.addWidget(
            self.youtube_start_label
        )

        youtube_time_layout.addWidget(
            self.youtube_start_input
        )

        youtube_time_layout.addWidget(
            self.youtube_stop_label
        )

        youtube_time_layout.addWidget(
            self.youtube_stop_input
        )

        youtube_time_layout.addWidget(
            self.youtube_loop_checkbox
        )

        youtube_volume_layout = QHBoxLayout()

        youtube_volume_layout.addWidget(
            self.youtube_volume_label
        )

        youtube_volume_layout.addWidget(
            self.youtube_volume_slider
        )

        youtube_buttons = QHBoxLayout()

        youtube_buttons.addWidget(
            self.youtube_play_button
        )

        youtube_buttons.addWidget(
            self.youtube_stop_button
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

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

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

        # YouTube
        layout.addWidget(
            self.youtube_section_label
        )

        layout.addWidget(
            self.youtube_url_label
        )

        layout.addWidget(
            self.youtube_url_input
        )

        layout.addLayout(
            youtube_time_layout
        )

        layout.addLayout(
            youtube_volume_layout
        )

        layout.addLayout(
            youtube_buttons
        )

        layout.addWidget(
            self.youtube_status_label
        )

        layout.addSpacing(20)

        # Local file playback
        layout.addWidget(
            self.local_section_label
        )

        layout.addWidget(
            self.file_label
        )

        layout.addLayout(
            file_buttons
        )

        layout.addStretch()

        # Exit
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

        self.youtube_volume_slider.valueChanged.connect(
            self.youtube_volume_changed
        )

        self.youtube_play_button.clicked.connect(
            self.play_youtube
        )

        self.youtube_stop_button.clicked.connect(
            self.stop_all_audio
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
    # Discord status
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
    # Discord server/channel
    # -------------------------------------------------

    def load_guilds(self):
        self.guild_combo.clear()

        for guild in self.discord.get_guilds():
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
    # External audio
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

        if guild_id is None or device_id is None:
            return

        self.save_audio_device()

        self.discord.start_audio_input(
            guild_id,
            device_id,
            volume=1.0,
        )

    # -------------------------------------------------
    # YouTube
    # -------------------------------------------------

    def youtube_volume_changed(
        self,
        value,
    ):
        self.youtube_volume_label.setText(
            f"Volume: {value}%"
        )

        self.settings.setValue(
            "youtube/volume",
            value,
        )

        self.settings.sync()

    def parse_timestamp(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            return None

        try:
            parts = value.split(":")

            if len(parts) == 1:
                return int(parts[0])

            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])

                return (
                    minutes * 60
                    + seconds
                )

            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])

                return (
                    hours * 3600
                    + minutes * 60
                    + seconds
                )

        except ValueError:
            return None

        return None

    def play_youtube(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            self.youtube_status_label.setText(
                "Select a Discord server first."
            )
            return

        youtube_url = (
            self.youtube_url_input.text().strip()
        )

        if not youtube_url:
            self.youtube_status_label.setText(
                "Enter a YouTube URL."
            )
            return

        start_text = (
            self.youtube_start_input.text()
        )

        stop_text = (
            self.youtube_stop_input.text()
        )

        start_time = self.parse_timestamp(
            start_text
        )

        stop_time = self.parse_timestamp(
            stop_text
        )

        if (
            start_text.strip()
            and start_time is None
        ):
            self.youtube_status_label.setText(
                "Invalid start timestamp."
            )
            return

        if (
            stop_text.strip()
            and stop_time is None
        ):
            self.youtube_status_label.setText(
                "Invalid stop timestamp."
            )
            return

        if (
            start_time is not None
            and stop_time is not None
            and stop_time <= start_time
        ):
            self.youtube_status_label.setText(
                "Stop time must be after start time."
            )
            return

        loop = (
            self.youtube_loop_checkbox.isChecked()
        )

        volume = (
            self.youtube_volume_slider.value()
            / 100.0
        )

        self.youtube_status_label.setText(
            "Starting YouTube playback..."
        )

        self.discord.play_youtube(
            guild_id,
            youtube_url,
            volume=volume,
            loop=loop,
            start_time=start_time,
            stop_time=stop_time,
        )

    # -------------------------------------------------
    # Local files
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
    # Stop all
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

        self.youtube_status_label.setText(
            "Stopped."
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

        QApplication.processEvents()

        self.discord.shutdown()

        event.accept()