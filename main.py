import os
import sys

from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

from bot.discord_client import DiscordClient
from gui.main_window import MainWindow


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN was not found in .env"
    )


def main():
    # Start Discord client
    discord_client = DiscordClient(TOKEN)
    discord_client.start()

    # Start Qt application
    app = QApplication(sys.argv)

    # Dark theme
    app.setStyleSheet("""
    QWidget {
        background-color: #1e1e1e;
        color: #e6e6e6;
        font-size: 13px;
    }

    QMainWindow {
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
    """)

    window = MainWindow(discord_client)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()