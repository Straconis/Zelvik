import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


GITHUB_OWNER = "straconis"
GITHUB_REPO = "dark-between-audio"

LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

INSTALLER_NAME_PREFIX = "Zelvik-"
INSTALLER_NAME_SUFFIX = "-Setup.exe"


# ---------------------------------------------------------
# Version handling
# ---------------------------------------------------------

def normalize_version(version):
    """
    Convert versions such as:

        v1.5.0
        1.5.0

    into:

        (1, 5, 0)
    """

    version = version.strip()

    if version.lower().startswith("v"):
        version = version[1:]

    parts = version.split(".")

    numbers = []

    for part in parts:
        try:
            numbers.append(
                int(part)
            )

        except ValueError:
            numbers.append(
                0
            )

    while len(numbers) < 3:
        numbers.append(
            0
        )

    return tuple(
        numbers[:3]
    )


# ---------------------------------------------------------
# GitHub release lookup
# ---------------------------------------------------------

def get_latest_release():
    """
    Retrieve the latest published GitHub release.

    Raises an exception if GitHub cannot be reached or
    returns invalid release data.
    """

    request = urllib.request.Request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Zelvik-Updater",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            data = response.read()

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"GitHub returned HTTP {error.code}."
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Could not connect to GitHub: "
            f"{error.reason}"
        ) from error

    except TimeoutError as error:
        raise RuntimeError(
            "The GitHub update check timed out."
        ) from error

    try:
        return json.loads(
            data.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as error:
        raise RuntimeError(
            "GitHub returned invalid release information."
        ) from error


# ---------------------------------------------------------
# Installer asset lookup
# ---------------------------------------------------------

def find_installer_asset(release):
    """
    Find the Zelvik installer attached to the release.
    """

    assets = release.get(
        "assets",
        []
    )

    for asset in assets:
        name = asset.get(
            "name",
            ""
        )

        if (
            name.startswith(
                INSTALLER_NAME_PREFIX
            )
            and name.endswith(
                INSTALLER_NAME_SUFFIX
            )
        ):
            return asset

    return None


# ---------------------------------------------------------
# Update check
# ---------------------------------------------------------

def check_for_update(current_version):
    """
    Check GitHub for a newer Zelvik release.

    Returns a dictionary describing the result.

    status values:

        current
        update_available
        missing_installer
    """

    release = get_latest_release()

    latest_version = release.get(
        "tag_name",
        ""
    )

    if not latest_version:
        raise RuntimeError(
            "The latest GitHub release does not "
            "contain a version tag."
        )

    if (
        normalize_version(
            latest_version
        )
        <= normalize_version(
            current_version
        )
    ):
        return {
            "status": "current",
            "current_version": current_version,
            "latest_version": latest_version,
        }

    asset = find_installer_asset(
        release
    )

    if not asset:
        return {
            "status": "missing_installer",
            "current_version": current_version,
            "latest_version": latest_version,
        }

    download_url = asset.get(
        "browser_download_url"
    )

    if not download_url:
        return {
            "status": "missing_installer",
            "current_version": current_version,
            "latest_version": latest_version,
        }

    return {
        "status": "update_available",
        "current_version": current_version,
        "latest_version": latest_version,
        "installer_name": asset.get(
            "name"
        ),
        "installer_url": download_url,
    }


# ---------------------------------------------------------
# Download installer
# ---------------------------------------------------------

def download_installer(update):
    """
    Download the release installer into the user's
    temporary directory.
    """

    download_directory = os.path.join(
        tempfile.gettempdir(),
        "ZelvikUpdate",
    )

    os.makedirs(
        download_directory,
        exist_ok=True,
    )

    installer_path = os.path.join(
        download_directory,
        update["installer_name"],
    )

    request = urllib.request.Request(
        update["installer_url"],
        headers={
            "User-Agent": "Zelvik-Updater",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=60,
    ) as response:

        with open(
            installer_path,
            "wb",
        ) as output_file:

            while True:
                chunk = response.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                output_file.write(
                    chunk
                )

    return installer_path


# ---------------------------------------------------------
# Launch external updater
# ---------------------------------------------------------

def launch_updater(installer_path):
    """
    Launch the installed ZelvikUpdater.exe.

    When running as an installed PyInstaller application,
    sys.executable points to Zelvik.exe.
    """

    app_directory = os.path.dirname(
        sys.executable
    )

    updater_path = os.path.join(
        app_directory,
        "ZelvikUpdater.exe",
    )

    zelvik_path = os.path.join(
        app_directory,
        "Zelvik.exe",
    )

    if not os.path.isfile(
        updater_path
    ):
        raise RuntimeError(
            "ZelvikUpdater.exe could not be found."
        )

    if not os.path.isfile(
        zelvik_path
    ):
        raise RuntimeError(
            "Zelvik.exe could not be found."
        )

    subprocess.Popen(
        [
            updater_path,
            installer_path,
            zelvik_path,
        ],
        cwd=app_directory,
    )