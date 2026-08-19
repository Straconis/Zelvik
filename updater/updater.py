import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

ZELVIK_MUTEX_NAME = r"Local\Zelvik.SingleInstance"

ERROR_FILE_NOT_FOUND = 2
WAIT_SECONDS = 1
MAX_WAIT_SECONDS = 30

TEMP_MODE_ARGUMENT = "--temp-updater"


# ---------------------------------------------------------
# Message box helper
# ---------------------------------------------------------

def show_message(message, title="Zelvik Updater", error=False):
    """
    Display a native Windows message box.
    """

    icon = 0x10 if error else 0x40

    ctypes.windll.user32.MessageBoxW(
        None,
        message,
        title,
        icon,
    )


# ---------------------------------------------------------
# Zelvik running check
# ---------------------------------------------------------

def is_zelvik_running():
    """
    Check whether Zelvik's single-instance mutex exists.
    """

    kernel32 = ctypes.windll.kernel32

    SYNCHRONIZE = 0x00100000

    handle = kernel32.OpenMutexW(
        SYNCHRONIZE,
        False,
        ZELVIK_MUTEX_NAME,
    )

    if handle:
        kernel32.CloseHandle(
            handle
        )

        return True

    return False


# ---------------------------------------------------------
# Wait for Zelvik to close
# ---------------------------------------------------------

def wait_for_zelvik():
    """
    Wait for the running Zelvik instance to release its mutex.
    """

    waited = 0

    while is_zelvik_running():
        if waited >= MAX_WAIT_SECONDS:
            return False

        time.sleep(
            WAIT_SECONDS
        )

        waited += WAIT_SECONDS

    return True


# ---------------------------------------------------------
# Run installer
# ---------------------------------------------------------

def run_installer(installer_path):
    """
    Run the Inno Setup installer silently and wait for it
    to finish.
    """

    result = subprocess.run(
        [
            installer_path,
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
        ],
        check=False,
    )

    return result.returncode


# ---------------------------------------------------------
# Relaunch Zelvik
# ---------------------------------------------------------

def relaunch_zelvik(zelvik_path):
    """
    Start the newly updated Zelvik executable.
    """

    subprocess.Popen(
        [zelvik_path],
        cwd=os.path.dirname(
            zelvik_path
        ),
    )


# ---------------------------------------------------------
# Temporary updater handoff
# ---------------------------------------------------------

def launch_temporary_updater(
    installer_path,
    zelvik_path,
):
    """
    Copy the updater to a temporary location and launch
    that copy.

    This allows the installer to replace the installed
    ZelvikUpdater.exe while the update is running.
    """

    current_executable = os.path.abspath(
        sys.executable
    )

    temp_directory = os.path.join(
        tempfile.gettempdir(),
        "ZelvikUpdater",
    )

    os.makedirs(
        temp_directory,
        exist_ok=True,
    )

    temp_updater_path = os.path.join(
        temp_directory,
        f"ZelvikUpdater-{uuid.uuid4().hex}.exe",
    )

    shutil.copy2(
        current_executable,
        temp_updater_path,
    )

    subprocess.Popen(
        [
            temp_updater_path,
            TEMP_MODE_ARGUMENT,
            installer_path,
            zelvik_path,
        ],
        cwd=temp_directory,
    )


# ---------------------------------------------------------
# Perform update
# ---------------------------------------------------------

def perform_update(
    installer_path,
    zelvik_path,
):
    """
    Perform the actual update from the temporary updater.
    """

    if not os.path.isfile(
        installer_path
    ):
        show_message(
            f"Update installer not found:\n\n"
            f"{installer_path}",
            error=True,
        )

        return ERROR_FILE_NOT_FOUND

    if not wait_for_zelvik():
        show_message(
            "Zelvik did not close within 30 seconds.\n\n"
            "The update has been cancelled.",
            error=True,
        )

        return 1

    installer_result = run_installer(
        installer_path
    )

    if installer_result != 0:
        show_message(
            f"The Zelvik update installer failed.\n\n"
            f"Installer exit code: "
            f"{installer_result}",
            error=True,
        )

        return installer_result

    if not os.path.isfile(
        zelvik_path
    ):
        show_message(
            "The update completed, but Zelvik could not "
            "be found afterward.",
            error=True,
        )

        return ERROR_FILE_NOT_FOUND

    try:
        relaunch_zelvik(
            zelvik_path
        )

    except Exception as error:
        show_message(
            f"The update completed, but Zelvik could not "
            f"be restarted.\n\n"
            f"{error}",
            error=True,
        )

        return 1

    return 0


# ---------------------------------------------------------
# Main updater
# ---------------------------------------------------------

def main():
    # -----------------------------------------------------
    # Temporary updater mode
    # -----------------------------------------------------

    if (
        len(sys.argv) == 4
        and sys.argv[1] == TEMP_MODE_ARGUMENT
    ):
        installer_path = os.path.abspath(
            sys.argv[2]
        )

        zelvik_path = os.path.abspath(
            sys.argv[3]
        )

        return perform_update(
            installer_path,
            zelvik_path,
        )

    # -----------------------------------------------------
    # Installed updater mode
    # -----------------------------------------------------

    if len(sys.argv) != 3:
        show_message(
            "The updater was started without the required "
            "update information.",
            error=True,
        )

        return 1

    installer_path = os.path.abspath(
        sys.argv[1]
    )

    zelvik_path = os.path.abspath(
        sys.argv[2]
    )

    if not os.path.isfile(
        installer_path
    ):
        show_message(
            f"Update installer not found:\n\n"
            f"{installer_path}",
            error=True,
        )

        return ERROR_FILE_NOT_FOUND

    try:
        launch_temporary_updater(
            installer_path,
            zelvik_path,
        )

    except Exception as error:
        show_message(
            f"The Zelvik updater could not prepare the "
            f"update.\n\n"
            f"{error}",
            error=True,
        )

        return 1

    # The installed updater exits here.
    # The temporary updater now owns the update process.
    return 0


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    sys.exit(
        main()
    )