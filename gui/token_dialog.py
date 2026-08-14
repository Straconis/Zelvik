from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from config import save_discord_token


class TokenDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.saved_token = None

        self.setWindowTitle(
            "Dark Between Audio - Discord Bot Setup"
        )

        self.setMinimumWidth(
            520
        )

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        self.title_label = QLabel(
            "Discord Bot Setup"
        )

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.instructions_label = QLabel(
            "Paste your Discord bot token below.\n\n"
            "The token will be stored in Windows "
            "Credential Manager and will not be written "
            "into the application folder."
        )

        self.instructions_label.setWordWrap(
            True
        )

        # -------------------------------------------------
        # Token input
        # -------------------------------------------------

        self.token_label = QLabel(
            "Discord Bot Token"
        )

        self.token_input = QLineEdit()

        self.token_input.setEchoMode(
            QLineEdit.Password
        )

        self.token_input.setPlaceholderText(
            "Paste your Discord bot token here"
        )

        # -------------------------------------------------
        # Show token checkbox
        # -------------------------------------------------

        self.show_token_checkbox = QCheckBox(
            "Show token"
        )

        self.show_token_checkbox.toggled.connect(
            self.toggle_token_visibility
        )

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------

        self.save_button = QPushButton(
            "Save & Connect"
        )

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.save_button.clicked.connect(
            self.save_token
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        button_layout.addWidget(
            self.save_button
        )

        button_layout.addWidget(
            self.cancel_button
        )

        # -------------------------------------------------
        # Main layout
        # -------------------------------------------------

        layout = QVBoxLayout()

        layout.addWidget(
            self.title_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.instructions_label
        )

        layout.addSpacing(
            15
        )

        layout.addWidget(
            self.token_label
        )

        layout.addWidget(
            self.token_input
        )

        layout.addWidget(
            self.show_token_checkbox
        )

        layout.addSpacing(
            15
        )

        layout.addLayout(
            button_layout
        )

        self.setLayout(
            layout
        )

    # -------------------------------------------------
    # Token visibility
    # -------------------------------------------------

    def toggle_token_visibility(
        self,
        checked,
    ):
        if checked:
            self.token_input.setEchoMode(
                QLineEdit.Normal
            )

        else:
            self.token_input.setEchoMode(
                QLineEdit.Password
            )

    # -------------------------------------------------
    # Save token
    # -------------------------------------------------

    def save_token(self):
        token = (
            self.token_input.text()
            .strip()
        )

        if not token:
            QMessageBox.warning(
                self,
                "Missing Token",
                "Please paste your Discord bot token.",
            )

            return

        try:
            save_discord_token(
                token
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to Save Token",
                (
                    "Dark Between Audio could not save "
                    "the Discord bot token.\n\n"
                    f"{error}"
                ),
            )

            return

        self.saved_token = token

        QMessageBox.information(
            self,
            "Token Saved",
            (
                "Your Discord bot token has been saved "
                "to Windows Credential Manager."
            ),
        )

        self.accept()