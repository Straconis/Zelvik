import ctypes
import os
import sys

import discord
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
)

from bot.discord_client import DiscordClient
from config import get_discord_token
from gui.main_window import MainWindow
from gui.token_dialog import TokenDialog


# ---------------------------------------------------------
# Single-instance protection
# ---------------------------------------------------------

ZELVIK_MUTEX_NAME = r"Local\Zelvik.SingleInstance"
_zelvik_mutex = None


def acquire_single_instance():
    """
    Prevent more than one instance of Zelvik from running.

    Returns True if this process owns the mutex.
    Returns False if another Zelvik instance is already running.
    """

    global _zelvik_mutex

    kernel32 = ctypes.windll.kernel32

    _zelvik_mutex = kernel32.CreateMutexW(
        None,
        False,
        ZELVIK_MUTEX_NAME,
    )

    if not _zelvik_mutex:
        # If Windows could not create the mutex for some
        # unexpected reason, allow Zelvik to continue rather
        # than preventing the application from starting.
        return True

    ERROR_ALREADY_EXISTS = 183

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(
            _zelvik_mutex
        )

        _zelvik_mutex = None

        ctypes.windll.user32.MessageBoxW(
            None,
            "Zelvik is already running.",
            "Zelvik",
            0x40,
        )

        return False

    return True


# ---------------------------------------------------------
# Resource path helper
# ---------------------------------------------------------

def resource_path(relative_path):
    """
    Return the absolute path to a resource.

    Works both from source and from a PyInstaller bundle.
    """

    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(
            os.path.dirname(__file__)
        )

    return os.path.join(
        base_path,
        relative_path,
    )


# ---------------------------------------------------------
# Load Discord Opus library
# ---------------------------------------------------------

def load_opus():
    """
    Load the Opus DLL required by discord.py for PCM audio.

    When running from source, discord.py can normally find
    its bundled DLL.

    When running from a PyInstaller executable, we bundle
    the x64 Opus DLL ourselves and explicitly load it.
    """

    if discord.opus.is_loaded():
        return

    possible_paths = [
        # PyInstaller bundled location
        resource_path(
            os.path.join(
                "discord",
                "bin",
                "libopus-0.x64.dll",
            )
        ),

        # Development/source location
        resource_path(
            os.path.join(
                ".venv",
                "Lib",
                "site-packages",
                "discord",
                "bin",
                "libopus-0.x64.dll",
            )
        ),
    ]

    for opus_path in possible_paths:
        if not os.path.exists(opus_path):
            continue

        try:
            discord.opus.load_opus(
                opus_path
            )

            print(
                f"Loaded Opus library: "
                f"{opus_path}"
            )

            return

        except Exception as error:
            print(
                f"Unable to load Opus from "
                f"{opus_path}: {error}"
            )

    # Last attempt: let discord.py / the operating system
    # try finding the library normally.
    try:
        discord.opus.load_opus(
            "libopus-0.x64.dll"
        )

        print(
            "Loaded Opus library using "
            "system DLL search."
        )

        return

    except Exception as error:
        print(
            "WARNING: Discord Opus library "
            "could not be loaded."
        )

        print(
            f"Opus error: {error}"
        )


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
    # -----------------------------------------------------
    # Prevent multiple Zelvik instances
    # -----------------------------------------------------

    if not acquire_single_instance():
        return 0

    # -----------------------------------------------------
    # Load Opus
    # -----------------------------------------------------

    # Opus must be loaded before Discord tries to play
    # our PCM mixer.
    load_opus()

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Zelvik"
    )

    app.setOrganizationName(
        "DarkBetween"
    )

    app.setStyleSheet(
        DARK_STYLESHEET
    )

    # -----------------------------------------------------
    # Application icon
    # -----------------------------------------------------

    icon_path = resource_path(
        os.path.join(
            "assets",
            "zelvik.ico",
        )
    )

    if os.path.exists(
        icon_path
    ):
        app.setWindowIcon(
            QIcon(icon_path)
        )

    # -----------------------------------------------------
    # Load Discord token
    # -----------------------------------------------------

    token = get_discord_token()

    if not token:
        token_dialog = TokenDialog()

        result = token_dialog.exec()

        if result != QDialog.Accepted:
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