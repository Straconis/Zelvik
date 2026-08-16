import json
import os
from copy import deepcopy


APP_DIRECTORY_NAME = "Zelvik"
SETTINGS_FILENAME = "settings.json"


DEFAULT_SETTINGS = {
    "discord": {
        "guild_id": "",
        "channel_id": "",
        "status_message": "Handling audio",
    },
    "audio": {
        "input_device_name": "",
        "input_volume": 100,
        "master_volume": 100,
    },
    "local": {
        "volume": 100,
    },
    "youtube": {
        "volume": 100,
        "loop": False,
        "cookies_origin": "",
    },
    "routing": {
        "application_name": "",
        "output_device_name": "",
    },
}


def get_settings_directory():
    """Return Zelvik's writable per-user settings directory."""

    local_app_data = os.environ.get("LOCALAPPDATA")

    if not local_app_data:
        local_app_data = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Local",
        )

    return os.path.join(
        local_app_data,
        APP_DIRECTORY_NAME,
    )


def get_settings_path():
    """Return the full path to Zelvik's settings.json file."""

    return os.path.join(
        get_settings_directory(),
        SETTINGS_FILENAME,
    )


def _merge_defaults(defaults, saved):
    """Recursively merge saved settings over Zelvik defaults."""

    result = deepcopy(defaults)

    if not isinstance(saved, dict):
        return result

    for key, value in saved.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _merge_defaults(
                result[key],
                value,
            )
        else:
            result[key] = value

    return result


def _write_settings(settings):
    """Write settings atomically."""

    settings_directory = get_settings_directory()

    os.makedirs(
        settings_directory,
        exist_ok=True,
    )

    settings_path = get_settings_path()
    temporary_path = settings_path + ".tmp"

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as settings_file:
        json.dump(
            settings,
            settings_file,
            indent=4,
            sort_keys=True,
        )
        settings_file.write("\n")

    os.replace(
        temporary_path,
        settings_path,
    )


def load_settings():
    """Load non-sensitive Zelvik settings."""

    settings_path = get_settings_path()

    if not os.path.isfile(settings_path):
        settings = deepcopy(DEFAULT_SETTINGS)
        _write_settings(settings)
        return settings

    try:
        with open(
            settings_path,
            "r",
            encoding="utf-8",
        ) as settings_file:
            saved_settings = json.load(settings_file)

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(
            "Unable to load Zelvik settings; "
            f"using defaults: {error}"
        )
        return deepcopy(DEFAULT_SETTINGS)

    return _merge_defaults(
        DEFAULT_SETTINGS,
        saved_settings,
    )


def save_settings(settings):
    """Persist a complete settings dictionary."""

    merged_settings = _merge_defaults(
        DEFAULT_SETTINGS,
        settings,
    )

    _write_settings(merged_settings)


class ZelvikSettings:
    """
    JSON-backed settings object compatible with the small QSettings API
    currently used by Zelvik's MainWindow.

    Supported calls:
        settings.value("audio/master_volume", 100, type=int)
        settings.setValue("audio/master_volume", 100)
        settings.sync()
    """

    def __init__(self):
        self._settings = load_settings()

    @staticmethod
    def _split_key(key):
        parts = [
            part
            for part in str(key).split("/")
            if part
        ]

        if not parts:
            raise ValueError(
                "Settings key cannot be empty."
            )

        return parts

    def value(
        self,
        key,
        default=None,
        type=None,
    ):
        """Return a setting using QSettings-style slash-separated keys."""

        parts = self._split_key(key)
        current = self._settings

        for part in parts:
            if not isinstance(current, dict):
                value = default
                break

            if part not in current:
                value = default
                break

            current = current[part]
        else:
            value = current

        if type is None:
            return value

        if value is None:
            return None

        try:
            if type is bool:
                if isinstance(value, bool):
                    return value

                if isinstance(value, str):
                    return value.strip().lower() in {
                        "1",
                        "true",
                        "yes",
                        "on",
                    }

                return bool(value)

            return type(value)

        except (
            TypeError,
            ValueError,
        ):
            return default

    def setValue(
        self,
        key,
        value,
    ):
        """Set and immediately persist a QSettings-style key."""

        parts = self._split_key(key)
        current = self._settings

        for part in parts[:-1]:
            child = current.get(part)

            if not isinstance(child, dict):
                child = {}
                current[part] = child

            current = child

        current[parts[-1]] = value

        self.sync()

    def sync(self):
        """Persist the current in-memory settings to settings.json."""

        save_settings(
            self._settings
        )

    def reload(self):
        """Reload settings.json from disk."""

        self._settings = load_settings()
