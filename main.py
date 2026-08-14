import sys

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
)

from bot.discord_client import DiscordClient
from config import get_discord_token
from gui.main_window import MainWindow
from gui.token_dialog import TokenDialog


# ---------------------------------------------------------
# Application stylesheet
# ---------------------------------------------------------

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #e6e6e6;
    font-size: 13px;
}

QMainWindow {
    background-color: #1e1e1e;
}

QDialog {
    background-color: #1e1e1e;
}

QLabel {
    color: #e6e6e6;
}

QComboBox {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 6px;
    border-radius: 4px;
    min-height: 22px;
}

QComboBox:hover {
    border: 1px solid #777777;
}

QComboBox QAbstractItemView {
    background-color: #2b2b2b;
    color: #ffffff;
    selection-background-color: #444444;
    selection-color: #ffffff;
}

QPushButton {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 8px 14px;
    border-radius: 5px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #444444;
    border: 1px solid #777777;
}

QPushButton:pressed {
    background-color: #222222;
}

QPushButton:disabled {
    background-color: #242424;
    color: #777777;
    border: 1px solid #333333;
}

QLineEdit {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 6px;
    border-radius: 4px;
}

QLineEdit:focus {
    border: 1px solid #777777;
}

QCheckBox {
    color: #e6e6e6;
    spacing: 6px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #333333;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    width: 14px;
    margin: -4px 0;
    background: #888888;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #aaaaaa;
}

QMessageBox {
    background-color: #1e1e1e;
}

QMessageBox QLabel {
    color: #e6e6e6;
}
"""


# ---------------------------------------------------------
# Main application
# ---------------------------------------------------------

def main():
    # Qt must exist before we can show the first-run
    # Discord token dialog.
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Dark Between Audio"
    )

    app.setOrganizationName(
        "DarkBetween"
    )

    app.setStyleSheet(
        DARK_STYLESHEET
    )

    # -----------------------------------------------------
    # Load Discord token
    # -----------------------------------------------------

    token = get_discord_token()

    # No .env token and no saved Windows credential.
    # Show the first-run setup dialog.
    if not token:
        token_dialog = TokenDialog()

        result = token_dialog.exec()

        if result != QDialog.Accepted:
            # User cancelled setup.
            return 0

        token = token_dialog.saved_token

        if not token:
            return 0

    # -----------------------------------------------------
    # Start Discord
    # -----------------------------------------------------

    discord_client = DiscordClient(
        token
    )

    discord_client.start()

    # -----------------------------------------------------
    # Main window
    # -----------------------------------------------------

    window = MainWindow(
        discord_client
    )

    window.show()

    return app.exec()


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    sys.exit(
        main()
    )