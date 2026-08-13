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


discord_client = DiscordClient(TOKEN)
discord_client.start()


app = QApplication(sys.argv)

window = MainWindow(discord_client)
window.show()

sys.exit(app.exec())