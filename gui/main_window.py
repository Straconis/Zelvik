from PySide6.QtCore import (
    QSettings,
    Qt,
    QTimer,
)

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
    def __init__(
        self,
        discord_client,
    ):
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

        self.setWindowTitle(
            "Dark Between Audio v1.0"
        )

        self.resize(
            850,
            900,
        )

        # =================================================
        # Discord
        # =================================================

        self.status_label = QLabel(
            "Discord: Connecting..."
        )

        self.guild_label = QLabel(
            "Server"
        )

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

        self.voice_status_label = QLabel(
            "Voice: Not connected"
        )

        # =================================================
        # External input
        # =================================================

        self.input_section_label = QLabel(
            "External Audio Input"
        )

        self.input_device_label = QLabel(
            "Input Device"
        )

        self.input_device_combo = (
            QComboBox()
        )

        self.input_volume_label = QLabel(
            "Volume: 100%"
        )

        self.input_volume_slider = (
            QSlider(
                Qt.Horizontal
            )
        )

        self.input_volume_slider.setRange(
            0,
            200,
        )

        saved_input_volume = (
            self.settings.value(
                "audio/input_volume",
                100,
                type=int,
            )
        )

        self.input_volume_slider.setValue(
            saved_input_volume
        )

        self.input_volume_label.setText(
            f"Volume: "
            f"{saved_input_volume}%"
        )

        self.start_input_button = (
            QPushButton(
                "Start Input"
            )
        )

        self.stop_input_button = (
            QPushButton(
                "Stop Input"
            )
        )

        self.input_status_label = QLabel(
            "Input: Stopped"
        )

        # =================================================
        # YouTube
        # =================================================

        self.youtube_section_label = QLabel(
            "YouTube"
        )

        self.youtube_url_label = QLabel(
            "YouTube URL"
        )

        self.youtube_url_input = (
            QLineEdit()
        )

        self.youtube_url_input.setPlaceholderText(
            "https://www.youtube.com/watch?v=..."
        )

        self.youtube_start_label = QLabel(
            "Start"
        )

        self.youtube_start_input = (
            QLineEdit()
        )

        self.youtube_start_input.setPlaceholderText(
            "00:00"
        )

        self.youtube_stop_label = QLabel(
            "Stop"
        )

        self.youtube_stop_input = (
            QLineEdit()
        )

        self.youtube_stop_input.setPlaceholderText(
            "Optional"
        )

        self.youtube_loop_checkbox = (
            QCheckBox(
                "Loop"
            )
        )

        saved_loop = (
            self.settings.value(
                "youtube/loop",
                False,
                type=bool,
            )
        )

        self.youtube_loop_checkbox.setChecked(
            saved_loop
        )

        self.youtube_volume_slider = (
            QSlider(
                Qt.Horizontal
            )
        )

        self.youtube_volume_slider.setRange(
            0,
            200,
        )

        saved_youtube_volume = (
            self.settings.value(
                "youtube/volume",
                100,
                type=int,
            )
        )

        self.youtube_volume_slider.setValue(
            saved_youtube_volume
        )

        self.youtube_volume_label = QLabel(
            f"Volume: "
            f"{saved_youtube_volume}%"
        )

        self.youtube_play_button = (
            QPushButton(
                "Play YouTube"
            )
        )

        self.youtube_stop_button = (
            QPushButton(
                "Stop YouTube"
            )
        )

        self.youtube_status_label = QLabel(
            "YouTube: Stopped"
        )

        # =================================================
        # Local files
        # =================================================

        self.local_section_label = QLabel(
            "Local File Playback"
        )

        self.file_label = QLabel(
            "No sound selected"
        )

        self.select_sound_button = (
            QPushButton(
                "Select Sound"
            )
        )

        self.play_button = QPushButton(
            "Play Sound"
        )

        self.stop_local_button = (
            QPushButton(
                "Stop Local Audio"
            )
        )

        self.local_volume_slider = (
            QSlider(
                Qt.Horizontal
            )
        )

        self.local_volume_slider.setRange(
            0,
            200,
        )

        saved_local_volume = (
            self.settings.value(
                "local/volume",
                100,
                type=int,
            )
        )

        self.local_volume_slider.setValue(
            saved_local_volume
        )

        self.local_volume_label = QLabel(
            f"Volume: "
            f"{saved_local_volume}%"
        )

        self.local_status_label = QLabel(
            "Local Audio: Stopped"
        )

        # =================================================
        # Master
        # =================================================

        self.master_section_label = QLabel(
            "Master Output"
        )

        self.master_volume_slider = (
            QSlider(
                Qt.Horizontal
            )
        )

        self.master_volume_slider.setRange(
            0,
            150,
        )

        saved_master_volume = (
            self.settings.value(
                "audio/master_volume",
                100,
                type=int,
            )
        )

        self.master_volume_slider.setValue(
            saved_master_volume
        )

        self.master_volume_label = QLabel(
            f"Master: "
            f"{saved_master_volume}%"
        )

        self.stop_all_button = QPushButton(
            "STOP ALL AUDIO"
        )

        self.exit_button = QPushButton(
            "Exit"
        )

        # =================================================
        # Layouts
        # =================================================

        discord_buttons = QHBoxLayout()

        discord_buttons.addWidget(
            self.join_button
        )

        discord_buttons.addWidget(
            self.leave_button
        )

        input_volume_layout = (
            QHBoxLayout()
        )

        input_volume_layout.addWidget(
            self.input_volume_label
        )

        input_volume_layout.addWidget(
            self.input_volume_slider
        )

        input_buttons = QHBoxLayout()

        input_buttons.addWidget(
            self.start_input_button
        )

        input_buttons.addWidget(
            self.stop_input_button
        )

        youtube_times = QHBoxLayout()

        youtube_times.addWidget(
            self.youtube_start_label
        )

        youtube_times.addWidget(
            self.youtube_start_input
        )

        youtube_times.addWidget(
            self.youtube_stop_label
        )

        youtube_times.addWidget(
            self.youtube_stop_input
        )

        youtube_times.addWidget(
            self.youtube_loop_checkbox
        )

        youtube_volume_layout = (
            QHBoxLayout()
        )

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

        local_volume_layout = (
            QHBoxLayout()
        )

        local_volume_layout.addWidget(
            self.local_volume_label
        )

        local_volume_layout.addWidget(
            self.local_volume_slider
        )

        local_buttons = QHBoxLayout()

        local_buttons.addWidget(
            self.select_sound_button
        )

        local_buttons.addWidget(
            self.play_button
        )

        local_buttons.addWidget(
            self.stop_local_button
        )

        master_volume_layout = (
            QHBoxLayout()
        )

        master_volume_layout.addWidget(
            self.master_volume_label
        )

        master_volume_layout.addWidget(
            self.master_volume_slider
        )

        bottom_buttons = QHBoxLayout()

        bottom_buttons.addWidget(
            self.stop_all_button
        )

        bottom_buttons.addStretch()

        bottom_buttons.addWidget(
            self.exit_button
        )

        # =================================================
        # Main layout
        # =================================================

        layout = QVBoxLayout()

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

        layout.addWidget(
            self.voice_status_label
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
            input_volume_layout
        )

        layout.addLayout(
            input_buttons
        )

        layout.addWidget(
            self.input_status_label
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
            youtube_times
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

        # Local
        layout.addWidget(
            self.local_section_label
        )

        layout.addWidget(
            self.file_label
        )

        layout.addLayout(
            local_volume_layout
        )

        layout.addLayout(
            local_buttons
        )

        layout.addWidget(
            self.local_status_label
        )

        layout.addSpacing(20)

        # Master
        layout.addWidget(
            self.master_section_label
        )

        layout.addLayout(
            master_volume_layout
        )

        layout.addStretch()

        layout.addLayout(
            bottom_buttons
        )

        container = QWidget()

        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )

        # =================================================
        # Signals
        # =================================================

        self.guild_combo.currentIndexChanged.connect(
            self.guild_changed
        )

        self.channel_combo.currentIndexChanged.connect(
            self.save_channel
        )

        self.join_button.clicked.connect(
            self.join_channel
        )

        self.leave_button.clicked.connect(
            self.leave_channel
        )

        self.input_device_combo.currentIndexChanged.connect(
            self.save_audio_device
        )

        self.start_input_button.clicked.connect(
            self.start_audio_input
        )

        self.stop_input_button.clicked.connect(
            self.stop_audio_input
        )

        self.input_volume_slider.valueChanged.connect(
            self.input_volume_changed
        )

        self.youtube_volume_slider.valueChanged.connect(
            self.youtube_volume_changed
        )

        self.youtube_loop_checkbox.toggled.connect(
            self.save_youtube_loop
        )

        self.youtube_play_button.clicked.connect(
            self.play_youtube
        )

        self.youtube_stop_button.clicked.connect(
            self.stop_youtube
        )

        self.select_sound_button.clicked.connect(
            self.select_sound
        )

        self.play_button.clicked.connect(
            self.play_sound
        )

        self.stop_local_button.clicked.connect(
            self.stop_local_audio
        )

        self.local_volume_slider.valueChanged.connect(
            self.local_volume_changed
        )

        self.master_volume_slider.valueChanged.connect(
            self.master_volume_changed
        )

        self.stop_all_button.clicked.connect(
            self.stop_all_audio
        )

        self.exit_button.clicked.connect(
            self.close
        )

        # =================================================
        # Timer
        # =================================================

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.check_discord
        )

        self.timer.start(
            500
        )

    # =================================================
    # Discord
    # =================================================

    def check_discord(self):
        if self.shutting_down:
            return

        if not self.discord.client.is_ready():
            return

        self.status_label.setText(
            "Discord: Connected as "
            f"{self.discord.client.user}"
        )

        if not self.guilds_loaded:
            self.load_guilds()

            self.guilds_loaded = True

        if not self.audio_devices_loaded:
            self.load_audio_devices()

            self.audio_devices_loaded = True

    def load_guilds(self):
        self.guild_combo.blockSignals(
            True
        )

        self.guild_combo.clear()

        saved_guild = str(
            self.settings.value(
                "discord/guild_id",
                "",
            )
        )

        saved_index = -1

        for guild in self.discord.get_guilds():
            self.guild_combo.addItem(
                guild["name"],
                guild["id"],
            )

            if (
                str(guild["id"])
                == saved_guild
            ):
                saved_index = (
                    self.guild_combo.count()
                    - 1
                )

        if saved_index >= 0:
            self.guild_combo.setCurrentIndex(
                saved_index
            )

        self.guild_combo.blockSignals(
            False
        )

        self.guild_changed()

    def guild_changed(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        self.channel_combo.blockSignals(
            True
        )

        self.channel_combo.clear()

        if guild_id is None:
            self.channel_combo.blockSignals(
                False
            )
            return

        self.settings.setValue(
            "discord/guild_id",
            str(guild_id),
        )

        saved_channel = str(
            self.settings.value(
                "discord/channel_id",
                "",
            )
        )

        saved_index = -1

        for channel in (
            self.discord.get_voice_channels(
                guild_id
            )
        ):
            self.channel_combo.addItem(
                channel["name"],
                channel["id"],
            )

            if (
                str(channel["id"])
                == saved_channel
            ):
                saved_index = (
                    self.channel_combo.count()
                    - 1
                )

        if saved_index >= 0:
            self.channel_combo.setCurrentIndex(
                saved_index
            )

        self.channel_combo.blockSignals(
            False
        )

    def save_channel(self):
        channel_id = (
            self.channel_combo.currentData()
        )

        if channel_id is not None:
            self.settings.setValue(
                "discord/channel_id",
                str(channel_id),
            )

    def join_channel(self):
        channel_id = (
            self.channel_combo.currentData()
        )

        if channel_id is None:
            return

        self.save_channel()

        self.discord.join_channel(
            channel_id
        )

        self.voice_status_label.setText(
            "Voice: Joining "
            f"{self.channel_combo.currentText()}..."
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

        self.voice_status_label.setText(
            "Voice: Disconnected"
        )

        self.input_status_label.setText(
            "Input: Stopped"
        )

        self.youtube_status_label.setText(
            "YouTube: Stopped"
        )

        self.local_status_label.setText(
            "Local Audio: Stopped"
        )

    # =================================================
    # Audio devices
    # =================================================

    def load_audio_devices(self):
        self.input_device_combo.blockSignals(
            True
        )

        self.input_device_combo.clear()

        saved_name = str(
            self.settings.value(
                "audio/input_device_name",
                "",
            )
        )

        saved_index = -1

        for device in (
            self.discord.get_audio_input_devices()
        ):
            display_name = (
                f"{device['name']} "
                f"[{device['host_api']}]"
            )

            self.input_device_combo.addItem(
                display_name,
                device["id"],
            )

            if display_name == saved_name:
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
        name = (
            self.input_device_combo.currentText()
        )

        if not name:
            return

        self.settings.setValue(
            "audio/input_device_name",
            name,
        )

    # =================================================
    # External input
    # =================================================

    def start_audio_input(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        device_id = (
            self.input_device_combo.currentData()
        )

        if (
            guild_id is None
            or device_id is None
        ):
            return

        volume = (
            self.input_volume_slider.value()
            / 100.0
        )

        self.save_audio_device()

        self.discord.start_audio_input(
            guild_id,
            device_id,
            volume=volume,
        )

        self.input_status_label.setText(
            "Input: Active"
        )

    def stop_audio_input(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.stop_audio_input(
            guild_id
        )

        self.input_status_label.setText(
            "Input: Stopped"
        )

    def input_volume_changed(
        self,
        value,
    ):
        self.input_volume_label.setText(
            f"Volume: {value}%"
        )

        self.settings.setValue(
            "audio/input_volume",
            value,
        )

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is not None:
            self.discord.set_input_volume(
                guild_id,
                value / 100.0,
            )

    # =================================================
    # YouTube
    # =================================================

    def save_youtube_loop(
        self,
        checked,
    ):
        self.settings.setValue(
            "youtube/loop",
            checked,
        )

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

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is not None:
            self.discord.set_youtube_volume(
                guild_id,
                value / 100.0,
            )

    def parse_timestamp(
        self,
        text,
    ):
        text = text.strip()

        if not text:
            return None

        try:
            parts = text.split(":")

            if len(parts) == 1:
                return int(
                    parts[0]
                )

            if len(parts) == 2:
                return (
                    int(parts[0]) * 60
                    + int(parts[1])
                )

            if len(parts) == 3:
                return (
                    int(parts[0]) * 3600
                    + int(parts[1]) * 60
                    + int(parts[2])
                )

        except ValueError:
            return None

        return None

    def play_youtube(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        url = (
            self.youtube_url_input.text()
            .strip()
        )

        if guild_id is None:
            self.youtube_status_label.setText(
                "YouTube: Join a server first."
            )
            return

        if not url:
            self.youtube_status_label.setText(
                "YouTube: Enter a URL."
            )
            return

        start_text = (
            self.youtube_start_input.text()
        )

        stop_text = (
            self.youtube_stop_input.text()
        )

        start_time = (
            self.parse_timestamp(
                start_text
            )
        )

        stop_time = (
            self.parse_timestamp(
                stop_text
            )
        )

        if (
            start_text.strip()
            and start_time is None
        ):
            self.youtube_status_label.setText(
                "YouTube: Invalid start time."
            )
            return

        if (
            stop_text.strip()
            and stop_time is None
        ):
            self.youtube_status_label.setText(
                "YouTube: Invalid stop time."
            )
            return

        if (
            start_time is not None
            and stop_time is not None
            and stop_time <= start_time
        ):
            self.youtube_status_label.setText(
                "YouTube: Stop must be "
                "after start."
            )
            return

        volume = (
            self.youtube_volume_slider.value()
            / 100.0
        )

        loop = (
            self.youtube_loop_checkbox
            .isChecked()
        )

        self.youtube_status_label.setText(
            "YouTube: Starting..."
        )

        self.discord.play_youtube(
            guild_id,
            url,
            volume=volume,
            loop=loop,
            start_time=start_time,
            stop_time=stop_time,
        )

    def stop_youtube(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.stop_youtube(
            guild_id
        )

        self.youtube_status_label.setText(
            "YouTube: Stopped"
        )

    # =================================================
    # Local files
    # =================================================

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

        self.selected_audio_file = (
            filename
        )

        self.file_label.setText(
            filename
        )

    def play_sound(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if not self.selected_audio_file:
            self.local_status_label.setText(
                "Local Audio: "
                "Select a file first."
            )
            return

        if guild_id is None:
            return

        volume = (
            self.local_volume_slider.value()
            / 100.0
        )

        self.discord.play_mixed_audio(
            guild_id,
            self.selected_audio_file,
            volume=volume,
            loop=False,
        )

        self.local_status_label.setText(
            "Local Audio: Playing"
        )

    def stop_local_audio(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.stop_local_audio(
            guild_id
        )

        self.local_status_label.setText(
            "Local Audio: Stopped"
        )

    def local_volume_changed(
        self,
        value,
    ):
        self.local_volume_label.setText(
            f"Volume: {value}%"
        )

        self.settings.setValue(
            "local/volume",
            value,
        )

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is not None:
            self.discord.set_local_volume(
                guild_id,
                value / 100.0,
            )

    # =================================================
    # Master
    # =================================================

    def master_volume_changed(
        self,
        value,
    ):
        self.master_volume_label.setText(
            f"Master: {value}%"
        )

        self.settings.setValue(
            "audio/master_volume",
            value,
        )

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is not None:
            self.discord.set_master_volume(
                guild_id,
                value / 100.0,
            )

    def stop_all_audio(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        self.discord.stop_all_audio(
            guild_id
        )

        self.input_status_label.setText(
            "Input: Stopped"
        )

        self.youtube_status_label.setText(
            "YouTube: Stopped"
        )

        self.local_status_label.setText(
            "Local Audio: Stopped"
        )

    # =================================================
    # Shutdown
    # =================================================

    def closeEvent(
        self,
        event,
    ):
        if self.shutting_down:
            event.accept()
            return

        self.shutting_down = True

        self.timer.stop()

        self.status_label.setText(
            "Discord: Shutting down..."
        )

        self.settings.sync()

        QApplication.processEvents()

        self.discord.shutdown()

        event.accept()