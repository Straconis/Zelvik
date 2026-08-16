import os
import shutil

from PySide6.QtCore import (
    Qt,
    QTimer,
)

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QGroupBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import has_environment_token
from gui.token_dialog import TokenDialog
from audio.windows_routing import WindowsRoutingManager
from settings import ZelvikSettings


class MainWindow(QMainWindow):
    def __init__(
        self,
        discord_client,
    ):
        super().__init__()

        self.discord = discord_client
        self.windows_routing = WindowsRoutingManager()

        self.settings = ZelvikSettings()

        self.selected_audio_file = None

        self.guilds_loaded = False
        self.audio_devices_loaded = False
        self.shutting_down = False
        self.last_youtube_status = None
        self.discord_status_applied = False

        self.setWindowTitle(
            "Zelvik v1.2.0"
        )

        self.resize(
            760,
            860,
        )

        self.setMinimumSize(
            680,
            520,
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

        self.change_token_button = QPushButton(
            "Change Discord Token"
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

        self.input_device_combo = QComboBox()

        saved_input_volume = self.settings.value(
            "audio/input_volume",
            100,
            type=int,
        )

        self.input_volume_label = QLabel(
            f"Volume: {saved_input_volume}%"
        )

        self.input_volume_slider = QSlider(
            Qt.Horizontal
        )

        self.input_volume_slider.setRange(
            0,
            200,
        )

        self.input_volume_slider.setValue(
            saved_input_volume
        )

        self.start_input_button = QPushButton(
            "Start Input"
        )

        self.stop_input_button = QPushButton(
            "Stop Input"
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

        saved_loop = self.settings.value(
            "youtube/loop",
            False,
            type=bool,
        )

        self.youtube_loop_checkbox.setChecked(
            saved_loop
        )

        saved_youtube_volume = self.settings.value(
            "youtube/volume",
            100,
            type=int,
        )

        self.youtube_volume_label = QLabel(
            f"Volume: {saved_youtube_volume}%"
        )

        self.youtube_volume_slider = QSlider(
            Qt.Horizontal
        )

        self.youtube_volume_slider.setRange(
            0,
            200,
        )

        self.youtube_volume_slider.setValue(
            saved_youtube_volume
        )

        self.youtube_play_button = QPushButton(
            "Play YouTube"
        )

        self.youtube_stop_button = QPushButton(
            "Stop YouTube"
        )

        self.youtube_status_label = QLabel(
            "YouTube: Stopped"
        )

        self.youtube_status_label.setWordWrap(
            True
        )

        self.youtube_activity_label = QLabel(
            "YouTube Activity"
        )

        self.youtube_activity_log = QPlainTextEdit()

        self.youtube_activity_log.setReadOnly(
            True
        )

        self.youtube_activity_log.setMaximumBlockCount(
            50
        )

        self.youtube_activity_log.setMinimumHeight(
            90
        )

        self.youtube_activity_log.setMaximumHeight(
            140
        )

        self.youtube_activity_log.setPlaceholderText(
            "YouTube playback activity will appear here."
        )

        self.youtube_auth_label = QLabel(
            "YouTube Authentication"
        )

        self.youtube_auth_file_label = QLabel(
            "No cookies.txt selected"
        )

        self.youtube_auth_file_label.setWordWrap(
            True
        )

        self.youtube_auth_select_button = QPushButton(
            "Import cookies.txt"
        )

        self.youtube_auth_check_button = QPushButton(
            "Check Authentication"
        )

        self.youtube_auth_disable_button = QPushButton(
            "Disable Authentication"
        )

        self.youtube_cookies_origin = self.settings.value(
            "youtube/cookies_origin",
            "",
            type=str,
        )

        self.youtube_cookies_file = (
            self._managed_youtube_cookies_path()
        )

        if os.path.isfile(
            self.youtube_cookies_file
        ):
            origin_text = (
                self.youtube_cookies_origin
                or "Unknown (imported before origin tracking)"
            )

            self.youtube_auth_file_label.setText(
                "Original file: "
                f"{origin_text}\n"
                "Managed copy: "
                f"{self.youtube_cookies_file}"
            )

            self.youtube_auth_status_label = QLabel(
                "Authentication: Available — not currently in use"
            )

        else:
            self.youtube_cookies_file = ""

            self.youtube_auth_status_label = QLabel(
                "Authentication: Disabled"
            )

        self.youtube_auth_status_label.setWordWrap(
            True
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

        self.file_label.setWordWrap(
            True
        )

        self.select_sound_button = QPushButton(
            "Select Sound"
        )

        self.play_button = QPushButton(
            "Play Sound"
        )

        self.stop_local_button = QPushButton(
            "Stop Local Audio"
        )

        saved_local_volume = self.settings.value(
            "local/volume",
            100,
            type=int,
        )

        self.local_volume_label = QLabel(
            f"Volume: {saved_local_volume}%"
        )

        self.local_volume_slider = QSlider(
            Qt.Horizontal
        )

        self.local_volume_slider.setRange(
            0,
            200,
        )

        self.local_volume_slider.setValue(
            saved_local_volume
        )

        self.local_status_label = QLabel(
            "Local Audio: Stopped"
        )

        # =================================================
        # Zelvik readiness status
        # =================================================

        self.readiness_section_label = QLabel(
            "Zelvik Status"
        )

        self.discord_ready_label = QLabel()
        self.channel_ready_label = QLabel()
        self.routing_ready_label = QLabel()
        self.source_ready_label = QLabel()
        self.good_to_go_label = QLabel()

        # =================================================
        # Windows audio routing
        # =================================================

        self.routing_section_label = QLabel(
            "Windows Audio Routing"
        )

        self.routing_application_label = QLabel(
            "Application"
        )

        self.routing_application_combo = QComboBox()

        self.routing_output_label = QLabel(
            "Output Device"
        )

        self.routing_output_combo = QComboBox()

        self.routing_refresh_button = QPushButton(
            "Refresh Applications / Devices"
        )

        self.routing_toggle_button = QPushButton(
            "Enable Routing"
        )

        self.routing_toggle_button.setCheckable(
            True
        )

        self.routing_toggle_button.setEnabled(
            False
        )

        self.routing_settings_button = QPushButton(
            "Open Windows Sound Settings"
        )

        self.routing_status_label = QLabel(
            "Routing: Loading..."
        )

        self.routing_status_label.setWordWrap(
            True
        )

        # =================================================
        # Master
        # =================================================

        self.master_section_label = QLabel(
            "Master Output"
        )

        saved_master_volume = self.settings.value(
            "audio/master_volume",
            100,
            type=int,
        )

        self.master_volume_label = QLabel(
            f"Master: {saved_master_volume}%"
        )

        self.master_volume_slider = QSlider(
            Qt.Horizontal
        )

        self.master_volume_slider.setRange(
            0,
            150,
        )

        self.master_volume_slider.setValue(
            saved_master_volume
        )

        self.stop_all_button = QPushButton(
            "STOP ALL AUDIO"
        )

        self.settings_button = QPushButton(
            "Settings"
        )

        saved_discord_status = self.settings.value(
            "discord/status_message",
            "Handling audio",
            type=str,
        )

        self.discord_status_input = QLineEdit()
        self.discord_status_input.setText(
            saved_discord_status
        )
        self.discord_status_input.setPlaceholderText(
            "Handling audio"
        )

        self.discord_status_apply_button = QPushButton(
            "Apply Status"
        )
        self.discord_status_apply_button.setEnabled(
            True
        )

        self.exit_button = QPushButton(
            "Exit"
        )

        self._build_settings_dialog()

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

        input_volume_layout = QHBoxLayout()

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

        local_volume_layout = QHBoxLayout()

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

        master_volume_layout = QHBoxLayout()

        master_volume_layout.addWidget(
            self.master_volume_label
        )

        master_volume_layout.addWidget(
            self.master_volume_slider
        )

        bottom_buttons = QHBoxLayout()

        bottom_buttons.addWidget(
            self.settings_button
        )

        bottom_buttons.addStretch()

        bottom_buttons.addWidget(
            self.stop_all_button
        )

        bottom_buttons.addWidget(
            self.exit_button
        )

        # =================================================
        # Main layout
        # =================================================

        layout = QVBoxLayout()

        # Connection summary
        layout.addWidget(
            self.status_label
        )

        layout.addWidget(
            self.voice_status_label
        )

        readiness_lights = QHBoxLayout()

        readiness_lights.addWidget(
            self.discord_ready_label
        )
        readiness_lights.addWidget(
            self.channel_ready_label
        )
        readiness_lights.addWidget(
            self.routing_ready_label
        )
        readiness_lights.addWidget(
            self.source_ready_label
        )
        readiness_lights.addStretch()
        readiness_lights.addWidget(
            self.good_to_go_label
        )

        layout.addLayout(
            readiness_lights
        )

        layout.addSpacing(
            12
        )

        # Discord session controls
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

        layout.addSpacing(
            16
        )

        # External input: device selection now lives in Settings.
        layout.addWidget(
            self.input_section_label
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

        layout.addSpacing(
            16
        )

        # YouTube session controls
        layout.addWidget(
            self.youtube_section_label
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

        layout.addSpacing(
            16
        )

        # Local audio
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

        layout.addSpacing(
            16
        )

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

        content_widget = QWidget()
        content_widget.setLayout(
            layout
        )

        scroll_area = QScrollArea(
            self
        )
        scroll_area.setWidgetResizable(
            True
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        scroll_area.setWidget(
            content_widget
        )

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )
        root_layout.addWidget(
            scroll_area
        )

        root_container = QWidget()
        root_container.setLayout(
            root_layout
        )

        self.setCentralWidget(
            root_container
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

        self.change_token_button.clicked.connect(
            self.change_discord_token
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

        self.youtube_auth_select_button.clicked.connect(
            self.select_youtube_cookies
        )

        self.youtube_auth_check_button.clicked.connect(
            self.check_youtube_authentication
        )

        self.youtube_auth_disable_button.clicked.connect(
            self.disable_youtube_authentication
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

        self.routing_refresh_button.clicked.connect(
            self.refresh_windows_routing
        )

        self.routing_application_combo.currentIndexChanged.connect(
            self.windows_routing_selection_changed
        )

        self.routing_output_combo.currentIndexChanged.connect(
            self.windows_routing_selection_changed
        )

        self.routing_settings_button.clicked.connect(
            self.open_windows_sound_settings
        )

        self.routing_toggle_button.clicked.connect(
            self.toggle_windows_routing
        )

        self.master_volume_slider.valueChanged.connect(
            self.master_volume_changed
        )

        self.stop_all_button.clicked.connect(
            self.stop_all_audio
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        self.discord_status_apply_button.clicked.connect(
            self.apply_discord_status
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

        self.refresh_windows_routing()

    # =================================================
    # Settings window
    # =================================================

    def _build_settings_dialog(self):
        self.settings_dialog = QDialog(
            self
        )
        self.settings_dialog.setWindowTitle(
            "Zelvik Settings"
        )
        self.settings_dialog.resize(
            860,
            680,
        )
        self.settings_dialog.setMinimumSize(
            820,
            560,
        )

        dialog_layout = QVBoxLayout(
            self.settings_dialog
        )
        dialog_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(
            True
        )
        settings_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        settings_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        dialog_layout.addWidget(
            settings_scroll
        )

        settings_content = QWidget()
        settings_content.setMinimumWidth(
            0
        )
        settings_scroll.setWidget(
            settings_content
        )

        settings_layout = QVBoxLayout(
            settings_content
        )
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(
            16,
            12,
            24,
            12,
        )

        # -------------------------------------------------
        # Discord
        # -------------------------------------------------
        discord_group = QGroupBox(
            "Discord"
        )
        discord_layout = QVBoxLayout()

        credentials_note = QLabel(
            "Bot credentials are stored securely "
            "in Windows Credential Manager."
        )
        credentials_note.setWordWrap(
            True
        )
        discord_layout.addWidget(
            credentials_note
        )
        discord_layout.addWidget(
            self.change_token_button
        )

        discord_status_label = QLabel(
            "Status / activity"
        )
        discord_layout.addWidget(
            discord_status_label
        )
        discord_layout.addWidget(
            self.discord_status_input
        )
        discord_layout.addWidget(
            self.discord_status_apply_button
        )

        discord_group.setLayout(
            discord_layout
        )
        settings_layout.addWidget(
            discord_group
        )

        # -------------------------------------------------
        # External audio input
        # -------------------------------------------------
        input_group = QGroupBox(
            "External Audio Input"
        )
        input_layout = QVBoxLayout()
        input_layout.addWidget(
            QLabel("Input device")
        )
        input_layout.addWidget(
            self.input_device_combo
        )
        input_group.setLayout(
            input_layout
        )
        settings_layout.addWidget(
            input_group
        )

        # -------------------------------------------------
        # YouTube authentication
        # -------------------------------------------------
        youtube_group = QGroupBox(
            "YouTube Authentication"
        )
        youtube_layout = QVBoxLayout()

        youtube_layout.addWidget(
            self.youtube_auth_status_label
        )

        youtube_buttons_top = QHBoxLayout()
        youtube_buttons_top.addWidget(
            self.youtube_auth_select_button
        )
        youtube_buttons_top.addWidget(
            self.youtube_auth_check_button
        )
        youtube_layout.addLayout(
            youtube_buttons_top
        )

        youtube_buttons_bottom = QHBoxLayout()
        youtube_buttons_bottom.addWidget(
            self.youtube_auth_disable_button
        )

        self.youtube_auth_details_button = QPushButton(
            "Show Details"
        )
        self.youtube_auth_details_button.setCheckable(
            True
        )
        self.youtube_auth_details_button.setMaximumWidth(
            120
        )
        self.youtube_auth_details_button.toggled.connect(
            self.toggle_youtube_auth_details
        )

        youtube_buttons_bottom.addWidget(
            self.youtube_auth_details_button
        )
        youtube_buttons_bottom.addStretch()
        youtube_layout.addLayout(
            youtube_buttons_bottom
        )

        self.youtube_auth_file_label.setVisible(
            False
        )
        youtube_layout.addWidget(
            self.youtube_auth_file_label
        )

        youtube_group.setLayout(
            youtube_layout
        )
        settings_layout.addWidget(
            youtube_group
        )

        # -------------------------------------------------
        # Windows audio routing
        # -------------------------------------------------
        routing_group = QGroupBox(
            "Windows Audio Routing"
        )
        routing_layout = QVBoxLayout()

        routing_hint = QLabel(
            "⚠  <b>Can't find your application?</b><br>"
            "Open the application, play some audio through it, "
            "then click <b>Refresh Applications / Devices</b>."
        )
        routing_hint.setWordWrap(
            True
        )
        routing_hint.setStyleSheet(
            "QLabel {"
            "  border: 1px solid palette(mid);"
            "  border-radius: 4px;"
            "  padding: 8px;"
            "}"
        )
        routing_layout.addWidget(
            routing_hint
        )

        routing_layout.addWidget(
            QLabel("Application")
        )
        routing_layout.addWidget(
            self.routing_application_combo
        )

        routing_layout.addWidget(
            QLabel("Output device")
        )
        routing_layout.addWidget(
            self.routing_output_combo
        )

        routing_layout.addWidget(
            self.routing_refresh_button
        )
        routing_layout.addWidget(
            self.routing_toggle_button
        )
        routing_layout.addWidget(
            self.routing_settings_button
        )
        routing_layout.addWidget(
            self.routing_status_label
        )

        routing_group.setLayout(
            routing_layout
        )
        settings_layout.addWidget(
            routing_group
        )

        settings_layout.addStretch()

        close_row = QHBoxLayout()
        close_row.addStretch()

        close_settings_button = QPushButton(
            "Close"
        )
        close_settings_button.setMinimumWidth(
            100
        )
        close_settings_button.clicked.connect(
            self.settings_dialog.close
        )
        close_row.addWidget(
            close_settings_button
        )
        settings_layout.addLayout(
            close_row
        )


    def toggle_youtube_auth_details(
        self,
        checked,
    ):
        self.youtube_auth_file_label.setVisible(
            checked
        )
        self.youtube_auth_details_button.setText(
            "Hide Details"
            if checked
            else "Show Details"
        )

    def open_settings(self):
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def apply_discord_status(
        self,
        checked=False,
        show_message=True,
        save=True,
    ):
        activity_text = (
            self.discord_status_input.text()
            .strip()
        )

        if save:
            self.settings.setValue(
                "discord/status_message",
                activity_text,
            )

        if not self.discord.client.is_ready():
            if show_message:
                QMessageBox.information(
                    self,
                    "Discord Status Saved",
                    (
                        "The status was saved and will be "
                        "applied when Zelvik connects to Discord."
                    ),
                )

            return

        self.discord.set_status(
            activity_text
        )

        if show_message:
            QMessageBox.information(
                self,
                "Discord Status Updated",
                (
                    "Zelvik's Discord activity was updated to:\n\n"
                    + (
                        activity_text
                        if activity_text
                        else "(no activity)"
                    )
                ),
            )

    # =================================================
    # Voice connection helpers
    # =================================================

    def is_voice_connected(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return False

        guild = self.discord.client.get_guild(
            guild_id
        )

        if guild is None:
            return False

        voice_client = (
            guild.voice_client
        )

        if voice_client is None:
            return False

        try:
            return voice_client.is_connected()

        except Exception:
            return False

    def require_voice_connection(
        self,
        source_name,
        status_label=None,
    ):
        """
        Return True when Discord voice is connected.

        Otherwise show a GUI warning and update the
        requested source status label.
        """

        if self.is_voice_connected():
            return True

        if status_label is not None:
            status_label.setText(
                f"{source_name}: "
                "Join a voice channel first."
            )

        self.voice_status_label.setText(
            "Voice: Not connected"
        )

        QMessageBox.warning(
            self,
            "Voice Channel Required",
            (
                "Zelvik is not connected "
                "to a Discord voice channel.\n\n"
                "Select a voice channel and click "
                "\"Join Channel\" before starting audio."
            ),
        )

        return False

    # =================================================
    # Discord status
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

        if not self.discord_status_applied:
            self.apply_discord_status(
                show_message=False,
                save=False,
            )
            self.discord_status_applied = True

        if not self.guilds_loaded:
            self.load_guilds()

            self.guilds_loaded = True

        if not self.audio_devices_loaded:
            self.load_audio_devices()

            self.audio_devices_loaded = True

        self.update_voice_status()
        self.update_youtube_status()
        self.update_readiness_status()

    def update_voice_status(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            self.voice_status_label.setText(
                "Voice: Not connected"
            )

            return

        guild = (
            self.discord.client.get_guild(
                guild_id
            )
        )

        if (
            guild is not None
            and guild.voice_client is not None
            and guild.voice_client.channel
            is not None
        ):
            self.voice_status_label.setText(
                "Voice: Connected to "
                f"{guild.voice_client.channel.name}"
            )

        else:
            self.voice_status_label.setText(
                "Voice: Not connected"
            )

    def update_youtube_status(self):
        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is None:
            return

        state = (
            self.discord.active_sources.get(
                guild_id
            )
        )

        if not state:
            return

        source = state.get(
            "youtube"
        )

        if source is None:
            return

        status = getattr(
            source,
            "status_text",
            None,
        )

        if status:
            self.youtube_status_label.setText(
                status
            )

            if (
                status
                != self.last_youtube_status
            ):
                self.last_youtube_status = status

                self.youtube_activity_log.appendPlainText(
                    status
                )

                scroll_bar = (
                    self.youtube_activity_log
                    .verticalScrollBar()
                )

                scroll_bar.setValue(
                    scroll_bar.maximum()
                )

        get_error_state = getattr(
            source,
            "get_error_state",
            None,
        )

        if get_error_state is None:
            return

        error_state = (
            get_error_state()
        )

        if not error_state:
            return

        if error_state.get(
            "reported",
            False,
        ):
            return

        mark_error_reported = getattr(
            source,
            "mark_error_reported",
            None,
        )

        if mark_error_reported is not None:
            mark_error_reported()

        message_box = QMessageBox(
            self
        )

        message_box.setIcon(
            QMessageBox.Critical
        )

        message_box.setWindowTitle(
            "YouTube Playback Failed"
        )

        message_box.setText(
            error_state.get(
                "message",
                "Zelvik could not play this YouTube video.",
            )
        )

        if error_state.get(
            "retryable",
            False,
        ):
            message_box.setInformativeText(
                "This error may be temporary. "
                "Trying the video again may succeed."
            )

        else:
            message_box.setInformativeText(
                "Retrying without changing anything "
                "is unlikely to resolve this error."
            )

        details = error_state.get(
            "details"
        )

        if details:
            message_box.setDetailedText(
                str(details)
            )

        message_box.exec()

    # =================================================
    # Discord server / channel
    # =================================================

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
            QMessageBox.warning(
                self,
                "No Voice Channel Selected",
                (
                    "Select a Discord voice channel "
                    "before clicking Join Channel."
                ),
            )

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
    # Discord token
    # =================================================

    def change_discord_token(self):
        if has_environment_token():
            QMessageBox.warning(
                self,
                "Token Controlled by .env",
                (
                    "Zelvik is currently "
                    "using DISCORD_TOKEN from your .env "
                    "file or environment.\n\n"
                    "A token saved through this dialog "
                    "would not override that value.\n\n"
                    "Remove or update DISCORD_TOKEN in "
                    ".env before using the saved Windows "
                    "Credential Manager token."
                ),
            )

            return

        dialog = TokenDialog(
            self
        )

        result = dialog.exec()

        if result != TokenDialog.Accepted:
            return

        QMessageBox.information(
            self,
            "Discord Token Changed",
            (
                "The new Discord bot token has been saved "
                "to Windows Credential Manager.\n\n"
                "Restart Zelvik to connect "
                "using the new token."
            ),
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
        if not self.require_voice_connection(
            "Input",
            self.input_status_label,
        ):
            return

        guild_id = (
            self.guild_combo.currentData()
        )

        device_id = (
            self.input_device_combo.currentData()
        )

        if device_id is None:
            self.input_status_label.setText(
                "Input: Select an input device."
            )

            QMessageBox.warning(
                self,
                "No Input Device Selected",
                (
                    "Select an audio input device "
                    "before starting external audio."
                ),
            )

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
            "Input: Starting..."
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

    def _managed_youtube_cookies_path(
        self,
    ):
        local_app_data = os.environ.get(
            "LOCALAPPDATA"
        )

        if not local_app_data:
            local_app_data = os.path.join(
                os.path.expanduser("~"),
                "AppData",
                "Local",
            )

        auth_dir = os.path.join(
            local_app_data,
            "Zelvik",
            "auth",
        )

        return os.path.join(
            auth_dir,
            "youtube_cookies.txt",
        )

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
        if not self.require_voice_connection(
            "YouTube",
            self.youtube_status_label,
        ):
            return

        guild_id = (
            self.guild_combo.currentData()
        )

        url = (
            self.youtube_url_input.text()
            .strip()
        )

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
                "YouTube: Stop must be after start."
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

        self.last_youtube_status = (
            "YouTube: Starting..."
        )

        self.youtube_activity_log.appendPlainText(
            "YouTube: Starting..."
        )

        self.discord.play_youtube(
            guild_id,
            url,
            volume=volume,
            loop=loop,
            start_time=start_time,
            stop_time=stop_time,
            cookies_file=(
                self.youtube_cookies_file
                if (
                    self.youtube_cookies_file
                    and os.path.isfile(
                        self.youtube_cookies_file
                    )
                )
                else None
            ),
        )

    def select_youtube_cookies(
        self,
    ):
        filename, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Import YouTube cookies.txt",
                "",
                (
                    "Cookie Files (*.txt);;"
                    "All Files (*)"
                ),
            )
        )

        if not filename:
            return

        managed_path = (
            self._managed_youtube_cookies_path()
        )

        try:
            os.makedirs(
                os.path.dirname(
                    managed_path
                ),
                exist_ok=True,
            )

            shutil.copy2(
                filename,
                managed_path,
            )

        except Exception as error:
            message_box = QMessageBox(
                self
            )

            message_box.setIcon(
                QMessageBox.Critical
            )

            message_box.setWindowTitle(
                "YouTube Authentication"
            )

            message_box.setText(
                "Zelvik could not import cookies.txt."
            )

            message_box.setDetailedText(
                str(error)
            )

            message_box.exec()

            self.youtube_activity_log.appendPlainText(
                "YouTube: Authentication cookies verified and available."
            )

            return

        self.youtube_cookies_file = (
            managed_path
        )

        self.youtube_cookies_origin = (
            os.path.abspath(
                filename
            )
        )

        self.settings.setValue(
            "youtube/cookies_file",
            managed_path,
        )

        self.settings.setValue(
            "youtube/cookies_origin",
            self.youtube_cookies_origin,
        )

        self.youtube_auth_file_label.setText(
            "Original file: "
            f"{self.youtube_cookies_origin}\n"
            "Managed copy: "
            f"{managed_path}"
        )

        self.youtube_auth_status_label.setText(
            "Authentication: Available — checking..."
        )

        self.youtube_activity_log.appendPlainText(
            "YouTube: Imported authentication cookies "
            "into Zelvik-managed storage."
        )

        self.check_youtube_authentication()

    def check_youtube_authentication(
        self,
    ):
        if not self.youtube_cookies_file:
            self.youtube_auth_status_label.setText(
                "Authentication: Disabled"
            )

            return

        self.youtube_auth_status_label.setText(
            "Authentication: Checking cookies.txt..."
        )

        QApplication.processEvents()

        result = (
            self.discord.check_youtube_auth(
                self.youtube_cookies_file
            )
        )

        if result.get(
            "authenticated",
            False,
        ):
            self.youtube_auth_status_label.setText(
                "Authentication: Available"
            )

            message_box = QMessageBox(
                self
            )

            message_box.setIcon(
                QMessageBox.Information
            )

            message_box.setWindowTitle(
                "YouTube Authentication"
            )

            message_box.setText(
                "YouTube authentication is ready."
            )

            message_box.setInformativeText(
                "Zelvik imported signed-in YouTube cookies "
                "into its managed authentication storage."
            )

            details = result.get(
                "details"
            )

            if details:
                message_box.setDetailedText(
                    str(details)
                )

            message_box.exec()

            return

        self.youtube_auth_status_label.setText(
            "Authentication: Cookies loaded, sign-in not confirmed"
        )

        message_box = QMessageBox(
            self
        )

        if result.get(
            "ok",
            False,
        ):
            message_box.setIcon(
                QMessageBox.Warning
            )
        else:
            message_box.setIcon(
                QMessageBox.Critical
            )

        message_box.setWindowTitle(
            "YouTube Authentication"
        )

        message_box.setText(
            result.get(
                "message",
                "YouTube authentication check failed.",
            )
        )

        details = result.get(
            "details"
        )

        if details:
            message_box.setDetailedText(
                str(details)
            )

        message_box.exec()

    def disable_youtube_authentication(
        self,
    ):
        managed_path = (
            self._managed_youtube_cookies_path()
        )

        try:
            if os.path.isfile(
                managed_path
            ):
                os.remove(
                    managed_path
                )

        except Exception as error:
            message_box = QMessageBox(
                self
            )

            message_box.setIcon(
                QMessageBox.Warning
            )

            message_box.setWindowTitle(
                "YouTube Authentication"
            )

            message_box.setText(
                "Authentication was disabled, but Zelvik "
                "could not delete the managed cookies file."
            )

            message_box.setDetailedText(
                str(error)
            )

            message_box.exec()

        self.youtube_cookies_file = ""
        self.youtube_cookies_origin = ""

        self.settings.setValue(
            "youtube/cookies_file",
            "",
        )

        self.settings.setValue(
            "youtube/cookies_origin",
            "",
        )

        self.youtube_auth_file_label.setText(
            "No managed cookies imported"
        )

        self.youtube_auth_status_label.setText(
            "Authentication: Disabled"
        )

        self.youtube_activity_log.appendPlainText(
            "YouTube: Authentication disabled and "
            "managed cookies removed."
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

        self.last_youtube_status = (
            "YouTube: Stopped"
        )

        self.youtube_activity_log.appendPlainText(
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

        self.selected_audio_file = filename

        self.file_label.setText(
            filename
        )

    def play_sound(self):
        if not self.require_voice_connection(
            "Local Audio",
            self.local_status_label,
        ):
            return

        guild_id = (
            self.guild_combo.currentData()
        )

        if not self.selected_audio_file:
            self.local_status_label.setText(
                "Local Audio: Select a file first."
            )

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
    # Windows audio routing
    # =================================================

    def refresh_windows_routing(
        self,
    ):
        self.routing_application_combo.blockSignals(
            True
        )

        self.routing_output_combo.blockSignals(
            True
        )

        saved_application = str(
            self.settings.value(
                "routing/application_name",
                "",
            )
        )

        saved_output = str(
            self.settings.value(
                "routing/output_device_name",
                "",
            )
        )

        self.routing_application_combo.clear()
        self.routing_output_combo.clear()

        applications = (
            self.windows_routing
            .get_running_applications()
        )

        for application in applications:
            self.routing_application_combo.addItem(
                application["name"],
                application["name"],
            )

        outputs = (
            self.windows_routing
            .get_output_devices()
        )

        for output in outputs:
            display_name = (
                f"{output['name']} "
                f"[{output['host_api']}]"
            )

            self.routing_output_combo.addItem(
                display_name,
                output["name"],
            )

        app_index = (
            self.routing_application_combo
            .findData(saved_application)
        )

        if app_index >= 0:
            self.routing_application_combo.setCurrentIndex(
                app_index
            )

        output_index = (
            self.routing_output_combo
            .findData(saved_output)
        )

        if output_index >= 0:
            self.routing_output_combo.setCurrentIndex(
                output_index
            )

        self.routing_application_combo.blockSignals(
            False
        )

        self.routing_output_combo.blockSignals(
            False
        )

        self.update_windows_routing_status()

    def windows_routing_selection_changed(
        self,
    ):
        application_name = (
            self.routing_application_combo
            .currentData()
        )

        output_device_name = (
            self.routing_output_combo
            .currentData()
        )

        self.settings.setValue(
            "routing/application_name",
            application_name or "",
        )

        self.settings.setValue(
            "routing/output_device_name",
            output_device_name or "",
        )

        self.update_windows_routing_status()

    def update_windows_routing_status(
        self,
    ):
        application_name = (
            self.routing_application_combo
            .currentData()
        )

        output_device_name = (
            self.routing_output_combo
            .currentData()
        )

        result = (
            self.windows_routing
            .get_route_status(
                application_name,
                output_device_name,
            )
        )

        is_ready = (
            result.get("state") == "ready"
        )

        backend_ready = (
            self.windows_routing
            .routing_backend_available()
        )

        routed = False

        if is_ready and backend_ready:
            routed = (
                self.windows_routing
                .route_matches(
                    application_name,
                    output_device_name,
                )
            )

        self.routing_toggle_button.setEnabled(
            is_ready and backend_ready
        )

        self.routing_toggle_button.blockSignals(
            True
        )

        self.routing_toggle_button.setChecked(
            routed
        )

        self.routing_toggle_button.setText(
            "Disable Routing"
            if routed
            else "Enable Routing"
        )

        self.routing_toggle_button.blockSignals(
            False
        )

        if routed:
            self.routing_status_label.setText(
                "Routing: Active — "
                f"{application_name} → {output_device_name}"
            )
        elif not backend_ready:
            self.routing_status_label.setText(
                "Routing: Automatic routing backend unavailable. "
                "Use Windows Sound Settings."
            )
        else:
            self.routing_status_label.setText(
                "Routing: "
                + result.get(
                    "message",
                    "Unknown status",
                )
            )

        self.update_readiness_status()

    def toggle_windows_routing(
        self,
        checked,
    ):
        application_name = (
            self.routing_application_combo
            .currentData()
        )

        output_device_name = (
            self.routing_output_combo
            .currentData()
        )

        if checked:
            self.routing_status_label.setText(
                "Routing: Applying route..."
            )

            QApplication.processEvents()

            result = (
                self.windows_routing
                .enable_route(
                    application_name,
                    output_device_name,
                )
            )

        else:
            self.routing_status_label.setText(
                "Routing: Restoring Windows default..."
            )

            QApplication.processEvents()

            result = (
                self.windows_routing
                .disable_route(
                    application_name
                )
            )

        if not result.get("ok"):
            # Restore the control to the verified Windows state if the
            # requested operation failed.
            actual_routed = (
                self.windows_routing
                .route_matches(
                    application_name,
                    output_device_name,
                )
            )

            self.routing_toggle_button.blockSignals(
                True
            )

            self.routing_toggle_button.setChecked(
                actual_routed
            )

            self.routing_toggle_button.setText(
                "Disable Routing"
                if actual_routed
                else "Enable Routing"
            )

            self.routing_toggle_button.blockSignals(
                False
            )

            QMessageBox.warning(
                self,
                "Windows Audio Routing",
                (
                    "Zelvik could not change the Windows "
                    "application audio route.\n\n"
                    + result.get(
                        "message",
                        "Unknown routing error.",
                    )
                    + "\n\nUse Open Windows Sound Settings "
                    "for the manual fallback."
                ),
            )

        # Re-read Windows rather than assuming the click succeeded.
        self.update_windows_routing_status()
        self.update_readiness_status()

    def _status_text(
        self,
        state,
        title,
        detail,
    ):
        indicator = {
            "green": "🟢",
            "yellow": "🟡",
            "red": "🔴",
        }.get(
            state,
            "🟡",
        )

        return (
            f"{indicator} {title}"
            + (
                f" — {detail}"
                if detail
                else ""
            )
        )

    def update_readiness_status(
        self,
    ):
        # Discord connection: use discord.py's actual client state.
        discord_connected = bool(
            self.discord.client.is_ready()
        )

        # Voice connection: reuse MainWindow's existing helper.
        channel_joined = (
            self.is_voice_connected()
        )

        voice_channel_name = None

        guild_id = (
            self.guild_combo.currentData()
        )

        if guild_id is not None:
            guild = (
                self.discord.client.get_guild(
                    guild_id
                )
            )

            if (
                guild is not None
                and guild.voice_client is not None
                and guild.voice_client.channel
                is not None
            ):
                voice_channel_name = (
                    guild.voice_client.channel.name
                )

        application_name = (
            self.routing_application_combo
            .currentData()
        )

        output_device_name = (
            self.routing_output_combo
            .currentData()
        )

        route_state = {
            "persisted": False,
            "active": False,
            "active_device_name": None,
            "has_session": False,
        }

        if (
            application_name
            and output_device_name
            and self.windows_routing
            .routing_backend_available()
        ):
            route_state = (
                self.windows_routing
                .get_route_state(
                    application_name,
                    output_device_name,
                )
            )

        routed = bool(
            route_state.get(
                "persisted",
                False,
            )
        )

        active_route = bool(
            route_state.get(
                "active",
                False,
            )
        )

        # Keep the routing controls/status synchronized with the
        # actual persisted Windows route without requiring Refresh.
        self.routing_toggle_button.blockSignals(
            True
        )

        self.routing_toggle_button.setChecked(
            routed
        )

        self.routing_toggle_button.setText(
            "Disable Routing"
            if routed
            else "Enable Routing"
        )

        self.routing_toggle_button.blockSignals(
            False
        )

        if routed:
            if active_route:
                self.routing_status_label.setText(
                    "Routing: Active — "
                    f"{application_name} → {output_device_name}"
                )

            elif route_state.get(
                "has_session",
                False,
            ):
                current_device = (
                    route_state.get(
                        "active_device_name"
                    )
                    or "another output device"
                )

                self.routing_status_label.setText(
                    "Routing: Saved — "
                    f"{application_name} → {output_device_name}. "
                    "Current audio session is still on "
                    f"{current_device}; restart playback or "
                    "the application to bind the new route."
                )

            else:
                self.routing_status_label.setText(
                    "Routing: Saved — "
                    f"{application_name} → {output_device_name}. "
                    "Waiting for the application to create "
                    "an audio session."
                )

        # Determine which Zelvik source paths are actually active.
        input_active = False
        youtube_active = False
        local_active = False

        if guild_id is not None:
            state = (
                self.discord.active_sources.get(
                    guild_id
                )
            )

            if state:
                input_active = (
                    state.get("input")
                    is not None
                )

                youtube_source = state.get(
                    "youtube"
                )

                if youtube_source is not None:
                    youtube_finished = bool(
                        getattr(
                            youtube_source,
                            "finished",
                            False,
                        )
                    )

                    youtube_active = (
                        not youtube_finished
                    )

                local_sources = state.get(
                    "local",
                    []
                )

                local_active = bool(
                    local_sources
                )

        any_source_active = (
            input_active
            or youtube_active
            or local_active
        )

        # Windows app routing matters while using external input,
        # and while Zelvik is idle so the user can verify the route
        # before starting a source. It becomes irrelevant only when
        # YouTube or local playback is the active source.
        routing_required = (
            input_active
            or not any_source_active
        )

        if input_active:
            source_detail = "External input active"

        elif youtube_active:
            source_detail = "YouTube playback active"

        elif local_active:
            source_detail = "Local playback active"

        else:
            source_detail = "No audio source active"

        self.discord_ready_label.setText(
            "🟢 Discord"
            if discord_connected
            else "🟡 Discord"
        )
        self.discord_ready_label.setToolTip(
            f"Connected as {self.discord.client.user}"
            if discord_connected
            else "Waiting for Discord connection"
        )

        self.channel_ready_label.setText(
            "🟢 Voice"
            if channel_joined
            else "🟡 Voice"
        )
        self.channel_ready_label.setToolTip(
            voice_channel_name
            if channel_joined
            else "No voice channel joined"
        )

        if routing_required:
            if routed and active_route:
                routing_light_state = "green"
                routing_detail = (
                    f"{application_name} → {output_device_name}"
                )

            elif routed:
                routing_light_state = "yellow"

                if route_state.get(
                    "has_session",
                    False,
                ):
                    routing_detail = (
                        "Route saved; restart playback/app "
                        "to activate"
                    )
                else:
                    routing_detail = (
                        "Route saved; waiting for audio session"
                    )

            else:
                routing_light_state = "yellow"
                routing_detail = "Required for external input"

            self.routing_ready_label.setText(
                "🟢 Routing"
                if routing_light_state == "green"
                else "🟡 Routing"
            )
            self.routing_ready_label.setToolTip(
                routing_detail
            )

        else:
            # Routing is irrelevant for YouTube/local sources because
            # Zelvik itself is already feeding those into Discord.
            self.routing_ready_label.setText(
                "⚪ Routing"
            )
            self.routing_ready_label.setToolTip(
                "Not required for current source"
            )

        self.source_ready_label.setText(
            "🟢 Source"
            if any_source_active
            else "🟡 Source"
        )
        self.source_ready_label.setToolTip(
            source_detail
        )

        routing_ok = (
            active_route
            if routing_required
            else True
        )

        all_ready = (
            discord_connected
            and channel_joined
            and any_source_active
            and routing_ok
        )

        self.good_to_go_label.setText(
            "🟢 READY"
            if all_ready
            else "🟡 NOT READY"
        )
        self.good_to_go_label.setToolTip(
            "All checks passed"
            if all_ready
            else "Waiting for all required checks"
        )

    def open_windows_sound_settings(
        self,
    ):
        if (
            self.windows_routing
            .open_windows_sound_settings()
        ):
            self.routing_status_label.setText(
                "Routing: Opened Windows sound settings "
                "for manual fallback."
            )

            return

        QMessageBox.warning(
            self,
            "Windows Audio Routing",
            (
                "Zelvik could not open Windows sound settings.\n\n"
                "Open Settings > System > Sound and use the "
                "per-app volume/output controls manually."
            ),
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