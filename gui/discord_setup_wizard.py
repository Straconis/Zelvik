import os
import webbrowser

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from bot.discord_setup import (
    build_bot_install_url,
    validate_discord_token,
)


DISCORD_DEVELOPER_URL = (
    "https://discord.com/developers/applications"
)


def _project_root():
    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


def _asset_path(filename):
    return os.path.join(
        _project_root(),
        "assets",
        "discord_setup",
        filename,
    )


class TokenValidationWorker(QThread):
    finished = Signal(object)

    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token

    def run(self):
        result = validate_discord_token(
            self.token
        )
        self.finished.emit(result)


class GuidePage(QWidget):
    def __init__(
        self,
        title,
        text,
        image_filename=None,
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 22px; "
            "font-weight: bold;"
        )
        layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            "font-size: 14px;"
        )
        layout.addWidget(text_label)

        if image_filename:
            image_label = QLabel()
            image_label.setAlignment(
                Qt.AlignCenter
            )
            image_label.setMinimumHeight(300)

            pixmap = QPixmap(
                _asset_path(image_filename)
            )

            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    820,
                    500,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                image_label.setPixmap(pixmap)
            else:
                image_label.setText(
                    "Screenshot unavailable:\n"
                    f"{image_filename}"
                )

            layout.addWidget(
                image_label,
                1,
            )

        layout.addStretch()


class DiscordSetupWizard(QDialog):
    token_saved = Signal(str)

    def __init__(
        self,
        save_token_callback=None,
        parent=None,
    ):
        super().__init__(parent)

        self.save_token_callback = (
            save_token_callback
        )

        self.validation_worker = None
        self.validated_token = None
        self.validated_bot_id = None
        self.validated_bot_name = None
        self.token_saved_in_wizard = False

        self.setWindowTitle(
            "Zelvik - Guided Discord Setup"
        )
        self.resize(940, 720)
        self.setMinimumSize(800, 620)

        self._build_ui()
        self._build_pages()
        self._update_navigation()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        root.setSpacing(12)

        self.stack = QStackedWidget()
        root.addWidget(
            self.stack,
            1,
        )

        navigation = QHBoxLayout()

        self.back_button = QPushButton(
            "Back"
        )
        self.back_button.clicked.connect(
            self._go_back
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )
        self.cancel_button.clicked.connect(
            self.reject
        )

        self.next_button = QPushButton(
            "Next"
        )
        self.next_button.clicked.connect(
            self._go_next
        )

        navigation.addWidget(
            self.back_button
        )
        navigation.addStretch()
        navigation.addWidget(
            self.cancel_button
        )
        navigation.addWidget(
            self.next_button
        )

        root.addLayout(navigation)

    def _build_pages(self):
        self.stack.addWidget(
            self._welcome_page()
        )

        self.stack.addWidget(
            GuidePage(
                "Create a Discord Application",
                (
                    "In the Discord Developer Portal, "
                    "click \"+ Create\" in the upper-right "
                    "corner."
                ),
                "01_create_application.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Build a Bot",
                (
                    "Choose \"Build a bot for your server "
                    "or community.\""
                ),
                "02_build_bot.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Name Your Bot",
                (
                    "Enter a name for your Discord bot. "
                    "You can simply call it Zelvik. Accept "
                    "Discord's terms and click Create."
                ),
                "03_create_app.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Generate the Bot Token",
                (
                    "Discord should open the Bot page. "
                    "Under Token, click Reset Token."
                ),
                "04_reset_token.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Confirm the Token Reset",
                (
                    "Discord will warn that resetting a "
                    "token invalidates the previous one. "
                    "For a new bot, this is expected. "
                    "Click \"Yes, do it!\""
                ),
                "05_confirm_reset_token.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Verify Your Discord Account",
                (
                    "Discord may require MFA or another "
                    "identity check. Complete this directly "
                    "in Discord. Zelvik never asks for or "
                    "receives your authentication code."
                ),
                "06_mfa_verification.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Copy Your Bot Token",
                (
                    "Discord will now display the new bot token. "
                    "Click Copy and keep the token available while "
                    "you finish the Discord configuration steps. "
                    "You will paste and test it in Zelvik after "
                    "permissions are configured."
                ),
                "07_copy_token_REFERENCE_ONLY.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Configure Installation",
                (
                    "Open Installation in the Developer "
                    "Portal. Disable User Install and leave "
                    "Guild Install enabled."
                ),
                "09_guild_install_only.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Add the Bot Scope",
                (
                    "Under Default Install Settings, keep "
                    "applications.commands and add the bot "
                    "scope."
                ),
                "10_select_bot_scope.png",
            )
        )

        self.permissions_page_index = (
            self.stack.count()
        )
        self.stack.addWidget(
            GuidePage(
                "Set Zelvik Permissions",
                (
                    "Under Default Install Settings, open "
                    "the Permissions dropdown and select "
                    "exactly:\n\n"
                    "• View Channels\n"
                    "• Connect\n"
                    "• Speak\n\n"
                    "Confirm all three permissions are "
                    "shown, then click Save Changes before "
                    "continuing."
                ),
                "11_permissions_configured.png",
            )
        )

        self.token_page_index = (
            self.stack.count()
        )
        self.stack.addWidget(
            self._token_page()
        )

        self.install_page_index = (
            self.stack.count()
        )
        self.stack.addWidget(
            self._install_page()
        )

        self.stack.addWidget(
            GuidePage(
                "Discord May Open the Desktop App",
                (
                    "Discord may hand the authorization "
                    "process to the Discord desktop app. "
                    "If you see this screen, click "
                    "Continue to Discord."
                ),
                "12_discord_app_launch.png",
            )
        )

        self.stack.addWidget(
            GuidePage(
                "Choose Your Discord Server",
                (
                    "Under Add to server, choose the Discord "
                    "server where you want to use Zelvik, "
                    "then continue through Discord's "
                    "authorization process. You need Manage "
                    "Server permission for that server."
                ),
                "13_select_server.png",
            )
        )

        self.finish_page_index = (
            self.stack.count()
        )
        self.stack.addWidget(
            self._finish_page()
        )

    def _welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel(
            "Set Up Discord"
        )
        title.setStyleSheet(
            "font-size: 26px; "
            "font-weight: bold;"
        )

        description = QLabel(
            "Zelvik needs its own Discord bot account so "
            "it can join your voice channel and play "
            "audio.\n\n"
            "This wizard will walk you through creating "
            "the bot, getting its token, securely "
            "connecting Zelvik, and adding the bot to "
            "your Discord server."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            "font-size: 15px;"
        )

        open_button = QPushButton(
            "Open Discord Developer Portal"
        )
        open_button.clicked.connect(
            self._open_developer_portal
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(open_button)
        layout.addStretch()

        return page

    def _token_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel(
            "Verify the Discord Bot"
        )
        title.setStyleSheet(
            "font-size: 22px; "
            "font-weight: bold;"
        )

        instructions = QLabel(
            "The Discord-side configuration is complete. "
            "Paste the bot token you copied earlier, test the "
            "connection, and then save the verified token to "
            "Windows Credential Manager.\n\n"
            "If the test fails, correct or replace the token "
            "right here and try again."
        )
        instructions.setWordWrap(True)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(
            QLineEdit.Password
        )
        self.token_input.setPlaceholderText(
            "Paste Discord bot token"
        )
        self.token_input.textChanged.connect(
            self._token_changed
        )

        controls = QHBoxLayout()

        paste_button = QPushButton(
            "Paste from Clipboard"
        )
        paste_button.clicked.connect(
            self._paste_token
        )

        self.show_token = QCheckBox(
            "Show token"
        )
        self.show_token.toggled.connect(
            self._toggle_token_visibility
        )

        controls.addWidget(paste_button)
        controls.addWidget(self.show_token)
        controls.addStretch()

        self.test_button = QPushButton(
            "Test Connection"
        )
        self.test_button.clicked.connect(
            self._test_token
        )

        self.save_token_button = QPushButton(
            "Save Verified Token"
        )
        self.save_token_button.setEnabled(False)
        self.save_token_button.clicked.connect(
            self._save_token_from_page
        )

        self.token_status = QLabel("")
        self.token_status.setWordWrap(True)

        security_note = QLabel(
            "Zelvik stores the token using Windows Credential "
            "Manager. The token is not written to Zelvik's "
            "settings files."
        )
        security_note.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(self.token_input)
        layout.addLayout(controls)
        layout.addWidget(self.test_button)
        layout.addWidget(self.save_token_button)
        layout.addWidget(self.token_status)
        layout.addWidget(security_note)
        layout.addStretch()

        return page

    def _install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel(
            "Add Zelvik to Your Server"
        )
        title.setStyleSheet(
            "font-size: 22px; "
            "font-weight: bold;"
        )

        text = QLabel(
            "The Discord configuration is complete and the "
            "bot token has been verified. Click below and "
            "Zelvik will open Discord's server installation "
            "screen with the required permissions already "
            "requested."
        )
        text.setWordWrap(True)

        self.install_button = QPushButton(
            "Add Zelvik to a Discord Server"
        )
        self.install_button.clicked.connect(
            self._open_install_url
        )

        layout.addWidget(title)
        layout.addWidget(text)
        layout.addWidget(
            self.install_button
        )
        layout.addStretch()

        return page

    def _finish_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel(
            "Discord Setup Complete"
        )
        title.setStyleSheet(
            "font-size: 26px; "
            "font-weight: bold;"
        )

        self.finish_text = QLabel(
            "Your Discord bot is configured and ready for "
            "Zelvik. The verified token has already been saved "
            "securely to Windows Credential Manager."
        )
        self.finish_text.setWordWrap(True)
        self.finish_text.setStyleSheet(
            "font-size: 15px;"
        )

        layout.addWidget(title)
        layout.addWidget(
            self.finish_text
        )
        layout.addStretch()

        return page

    def _open_developer_portal(self):
        webbrowser.open(
            DISCORD_DEVELOPER_URL
        )

    def _paste_token(self):
        clipboard = (
            QApplication.clipboard()
        )
        self.token_input.setText(
            clipboard.text().strip()
        )

    def _toggle_token_visibility(
        self,
        visible,
    ):
        self.token_input.setEchoMode(
            QLineEdit.Normal
            if visible
            else QLineEdit.Password
        )

    def _token_changed(self):
        current_token = (
            self.token_input.text().strip()
        )

        if (
            self.validated_token is not None
            and current_token != self.validated_token
        ):
            self.validated_token = None
            self.validated_bot_id = None
            self.validated_bot_name = None
            self.token_saved_in_wizard = False

            if hasattr(self, "save_token_button"):
                self.save_token_button.setEnabled(False)

            if hasattr(self, "token_status"):
                self.token_status.setText(
                    "Token changed. Test the connection again."
                )

        self._update_navigation()

    def _test_token(self):
        token = (
            self.token_input.text().strip()
        )

        if not token:
            self.token_status.setText(
                "Enter or paste a Discord bot token first."
            )
            return

        self.test_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.token_saved_in_wizard = False
        self.save_token_button.setEnabled(False)

        self.token_status.setText(
            "Testing connection to Discord..."
        )

        self.validation_worker = (
            TokenValidationWorker(
                token,
                self,
            )
        )

        self.validation_worker.finished.connect(
            self._token_validation_finished
        )

        self.validation_worker.start()

    def _token_validation_finished(
        self,
        result,
    ):
        self.test_button.setEnabled(True)

        if not result.valid:
            self.validated_token = None
            self.validated_bot_id = None
            self.validated_bot_name = None
            self.token_saved_in_wizard = False
            self.save_token_button.setEnabled(False)

            self.token_status.setText(
                "Connection failed.\n\n"
                f"{result.error}"
            )

            self._update_navigation()
            return

        self.validated_token = (
            self.token_input.text().strip()
        )
        self.validated_bot_id = (
            result.bot_id
        )
        self.validated_bot_name = (
            result.bot_name
        )

        self.token_saved_in_wizard = False
        self.save_token_button.setEnabled(True)

        self.token_status.setText(
            "Connected successfully.\n\n"
            f"Bot: {result.bot_name}\n\n"
            "Click Save Verified Token to continue."
        )

        self._update_navigation()

    def _save_token_from_page(self):
        if not self.validated_token:
            QMessageBox.warning(
                self,
                "Test the Token",
                "Test the Discord bot token successfully before saving it.",
            )
            return

        if not self._save_validated_token():
            return

        self.token_saved_in_wizard = True
        self.save_token_button.setEnabled(False)
        self.token_status.setText(
            "Connected successfully.\n\n"
            f"Bot: {self.validated_bot_name}\n\n"
            "Verified token saved securely to Windows Credential Manager."
        )
        self._update_navigation()

    def _save_validated_token(self):
        if not self.validated_token:
            return False

        if self.save_token_callback is None:
            return True

        try:
            self.save_token_callback(
                self.validated_token
            )

            self.token_saved.emit(
                self.validated_token
            )

            return True

        except Exception as error:
            QMessageBox.critical(
                self,
                "Could Not Save Token",
                (
                    "Zelvik verified the Discord token but "
                    "could not save it securely.\n\n"
                    f"{error}"
                ),
            )

            return False

    def _open_install_url(self):
        if not self.validated_bot_id:
            QMessageBox.warning(
                self,
                "Bot Not Verified",
                "Verify the Discord bot token first.",
            )
            return

        url = build_bot_install_url(
            self.validated_bot_id
        )

        webbrowser.open(url)

    def _go_back(self):
        index = (
            self.stack.currentIndex()
        )

        if index > 0:
            self.stack.setCurrentIndex(
                index - 1
            )
            self._update_navigation()

    def _go_next(self):
        index = (
            self.stack.currentIndex()
        )

        if index == self.token_page_index:
            if not self.validated_token:
                QMessageBox.warning(
                    self,
                    "Test the Token",
                    (
                        "Zelvik needs to successfully test "
                        "the Discord bot token before "
                        "continuing with Discord setup."
                    ),
                )
                return

            if not self.token_saved_in_wizard:
                QMessageBox.warning(
                    self,
                    "Save the Token",
                    (
                        "Click Save Verified Token before "
                        "continuing with Discord setup."
                    ),
                )
                return

        if index == self.finish_page_index:
            self.accept()
            return

        if index < self.stack.count() - 1:
            self.stack.setCurrentIndex(
                index + 1
            )
            self._update_navigation()

    def _update_navigation(self):
        index = (
            self.stack.currentIndex()
        )

        self.back_button.setEnabled(
            index > 0
        )

        if index == self.token_page_index:
            self.next_button.setEnabled(
                self.validated_token is not None
                and self.token_saved_in_wizard
            )
        else:
            self.next_button.setEnabled(True)

        if index == self.finish_page_index:
            self.next_button.setText(
                "Finish"
            )
            self.cancel_button.setVisible(
                False
            )
        else:
            self.next_button.setText(
                "Next"
            )
            self.cancel_button.setVisible(
                True
            )

        if index == self.install_page_index:
            self.install_button.setEnabled(
                self.validated_bot_id is not None
            )
