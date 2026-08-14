import os

import keyring
from dotenv import load_dotenv


# ---------------------------------------------------------
# Zelvik configuration
# ---------------------------------------------------------

APP_NAME = "DarkBetweenAudio"

TOKEN_SERVICE = (
    "Zelvik"
)

TOKEN_USERNAME = (
    "discord_bot_token"
)


# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

def load_environment():
    """
    Load development configuration from .env.

    This keeps the existing development workflow working:

        DISCORD_TOKEN=your_token_here

    For packaged EXE users, the token will normally come
    from Windows Credential Manager instead.
    """

    load_dotenv()


# ---------------------------------------------------------
# Discord token
# ---------------------------------------------------------

def get_discord_token():
    """
    Return the configured Discord bot token.

    Priority:

    1. DISCORD_TOKEN from .env / environment
    2. Windows Credential Manager

    This means developers can continue using .env while
    packaged users can use the GUI setup dialog.
    """

    load_environment()

    environment_token = os.getenv(
        "DISCORD_TOKEN"
    )

    if environment_token:
        environment_token = (
            environment_token.strip()
        )

        if environment_token:
            return environment_token

    try:
        saved_token = keyring.get_password(
            TOKEN_SERVICE,
            TOKEN_USERNAME,
        )

    except Exception as error:
        print(
            "Unable to read Discord token "
            "from Windows Credential Manager: "
            f"{error}"
        )

        return None

    if saved_token:
        saved_token = saved_token.strip()

        if saved_token:
            return saved_token

    return None


def save_discord_token(token):
    """
    Save the Discord bot token to Windows Credential
    Manager.

    Raises ValueError when an empty token is supplied.

    Raises RuntimeError when Windows Credential Manager
    cannot save the token.
    """

    if token is None:
        raise ValueError(
            "Discord bot token cannot be empty."
        )

    token = token.strip()

    if not token:
        raise ValueError(
            "Discord bot token cannot be empty."
        )

    try:
        keyring.set_password(
            TOKEN_SERVICE,
            TOKEN_USERNAME,
            token,
        )

    except Exception as error:
        raise RuntimeError(
            "Unable to save the Discord bot token "
            "to Windows Credential Manager."
        ) from error


def clear_discord_token():
    """
    Remove the saved Discord token from Windows
    Credential Manager.

    If no stored token exists, nothing happens.

    This does not modify DISCORD_TOKEN in .env.
    """

    try:
        keyring.delete_password(
            TOKEN_SERVICE,
            TOKEN_USERNAME,
        )

    except keyring.errors.PasswordDeleteError:
        # No saved credential exists.
        pass

    except Exception as error:
        raise RuntimeError(
            "Unable to remove the Discord bot token "
            "from Windows Credential Manager."
        ) from error


def has_environment_token():
    """
    Return True when DISCORD_TOKEN is being supplied
    through .env or the current environment.

    Useful later when the GUI needs to explain that
    changing the saved credential will not override an
    existing development .env token.
    """

    load_environment()

    token = os.getenv(
        "DISCORD_TOKEN"
    )

    if token is None:
        return False

    return bool(
        token.strip()
    )