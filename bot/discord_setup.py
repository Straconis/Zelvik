import asyncio
from dataclasses import dataclass

import discord


@dataclass
class DiscordTokenValidation:
    valid: bool
    bot_name: str = ""
    bot_id: int | None = None
    error: str = ""


async def _validate_token_async(token):
    """
    Attempt a temporary Discord login using the supplied token.

    The temporary client is closed immediately after Discord
    confirms the bot identity.
    """

    token = (token or "").strip()

    if not token:
        return DiscordTokenValidation(
            valid=False,
            error="Enter a Discord bot token first.",
        )

    intents = discord.Intents.none()

    client = discord.Client(
        intents=intents,
    )

    try:
        await asyncio.wait_for(
            client.login(token),
            timeout=15,
        )

        if client.user is None:
            return DiscordTokenValidation(
                valid=False,
                error=(
                    "Discord accepted the connection, "
                    "but the bot identity could not be read."
                ),
            )

        return DiscordTokenValidation(
            valid=True,
            bot_name=str(client.user),
            bot_id=client.user.id,
        )

    except discord.LoginFailure:
        return DiscordTokenValidation(
            valid=False,
            error=(
                "Discord rejected this token. "
                "Make sure you copied the Bot Token "
                "and try again."
            ),
        )

    except asyncio.TimeoutError:
        return DiscordTokenValidation(
            valid=False,
            error=(
                "Discord did not respond in time. "
                "Check your internet connection and "
                "try again."
            ),
        )

    except Exception as error:
        return DiscordTokenValidation(
            valid=False,
            error=(
                "Zelvik could not verify the token.\n\n"
                f"{type(error).__name__}: {error}"
            ),
        )

    finally:
        if not client.is_closed():
            await client.close()


def validate_discord_token(token):
    """
    Synchronously validate a Discord bot token.

    This is intended to run from a worker thread so the
    PySide6 GUI remains responsive during authentication.
    """

    return asyncio.run(
        _validate_token_async(token)
    )


def _zelvik_permissions_value():
    """
    Return the Discord permissions integer required by Zelvik.

    Required permissions:
        View Channels
        Connect
        Speak
    """

    permissions = discord.Permissions.none()

    permissions.view_channel = True
    permissions.connect = True
    permissions.speak = True

    return permissions.value


def build_bot_install_url(bot_id):
    """
    Build the Discord authorization URL used to install
    Zelvik into a server.

    Scopes:
        bot
        applications.commands

    Permissions:
        View Channels
        Connect
        Speak
    """

    permissions = _zelvik_permissions_value()

    return (
        "https://discord.com/oauth2/authorize"
        f"?client_id={bot_id}"
        "&scope=bot%20applications.commands"
        f"&permissions={permissions}"
    )