import os
import subprocess

import sounddevice as sd
import re

try:
    import winappaudiorouter as war
except ImportError:
    war = None


class WindowsRoutingManager:
    """
    Priority 3 routing helper.

    Phase 1 intentionally focuses on discovery, persistence-friendly
    identifiers, routing status, and the Windows-settings fallback.
    The actual per-app route write will be added after discovery is
    verified on both Windows 10 and Windows 11.
    """

    def __init__(self):
        self._last_error = None

    @property
    def last_error(self):
        return self._last_error

    def is_supported(self):
        return os.name == "nt"

    def get_output_devices(self):
        """
        Return active output-capable devices known to PortAudio.

        sounddevice already ships with Zelvik and gives us a lightweight
        cross-check against what Windows exposes to normal applications.
        """
        if not self.is_supported():
            return []

        devices = sd.query_devices()
        host_apis = sd.query_hostapis()

        results = []

        for device_id, device in enumerate(devices):
            if device["max_output_channels"] <= 0:
                continue

            host_api_name = "Unknown"

            try:
                host_api_name = host_apis[
                    device["hostapi"]
                ]["name"]
            except Exception:
                pass

            results.append(
                {
                    "id": int(device_id),
                    "name": str(device["name"]),
                    "host_api": str(host_api_name),
                    "channels": int(
                        device["max_output_channels"]
                    ),
                }
            )

        # Prefer modern Windows backends where duplicate device names exist.
        priority = {
            "Windows WASAPI": 0,
            "MME": 1,
            "Windows DirectSound": 2,
            "Windows WDM-KS": 3,
        }

        deduplicated = {}

        for item in results:
            key = item["name"].strip().lower()

            existing = deduplicated.get(key)

            if (
                existing is None
                or priority.get(
                    item["host_api"],
                    99,
                )
                < priority.get(
                    existing["host_api"],
                    99,
                )
            ):
                deduplicated[key] = item

        results = list(
            deduplicated.values()
        )

        results.sort(
            key=lambda item:
            item["name"].lower()
        )

        return results

    def get_running_applications(self):
        """
        Enumerate visible running application processes.

        Uses Windows' built-in tasklist command so Priority 3 discovery
        does not add another Python package dependency.
        """
        if not self.is_supported():
            return []

        command = [
            "tasklist",
            "/FO",
            "CSV",
            "/NH",
        ]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
                check=False,
            )

            if completed.returncode != 0:
                self._last_error = (
                    completed.stderr.strip()
                    or "tasklist failed."
                )

                return []

            import csv
            import io

            reader = csv.reader(
                io.StringIO(
                    completed.stdout
                )
            )

            apps = {}

            ignored = {
                "system idle process",
                "system",
                "registry",
                "memory compression",
            }

            for row in reader:
                if len(row) < 2:
                    continue

                image_name = row[0].strip()
                pid_text = row[1].strip()

                if (
                    not image_name
                    or image_name.lower()
                    in ignored
                ):
                    continue

                try:
                    pid = int(pid_text)
                except ValueError:
                    continue

                key = image_name.lower()

                if key not in apps:
                    apps[key] = {
                        "name": image_name,
                        "pid": pid,
                    }

            results = list(
                apps.values()
            )

            results.sort(
                key=lambda item:
                item["name"].lower()
            )

            self._last_error = None

            return results

        except Exception as error:
            self._last_error = str(error)
            return []

    def get_route_status(
        self,
        application_name,
        output_device_name,
    ):
        """
        Phase-1 status model.

        Actual Windows per-app routing state inspection is intentionally
        deferred until the route-write mechanism is verified. This still
        gives the GUI useful status for missing apps/devices and makes the
        fallback path explicit.
        """
        if not self.is_supported():
            return {
                "state": "unsupported",
                "message": (
                    "Automatic Windows audio routing is only "
                    "available on Windows."
                ),
            }

        apps = {
            item["name"].lower():
            item
            for item in self.get_running_applications()
        }

        devices = {
            item["name"].lower():
            item
            for item in self.get_output_devices()
        }

        if not application_name:
            return {
                "state": "not_configured",
                "message": "Select an application to route.",
            }

        if not output_device_name:
            return {
                "state": "not_configured",
                "message": "Select an output device.",
            }

        if application_name.lower() not in apps:
            return {
                "state": "app_not_running",
                "message": (
                    f"{application_name} is not currently running."
                ),
            }

        if output_device_name.lower() not in devices:
            return {
                "state": "device_unavailable",
                "message": (
                    f"{output_device_name} is not currently available."
                ),
            }

        return {
            "state": "ready",
            "message": (
                f"Ready to route {application_name} "
                f"to {output_device_name}."
            ),
        }

    def routing_backend_available(self):
        return self.is_supported() and war is not None

    def get_audio_sessions(self):
        if not self.routing_backend_available():
            return []

        try:
            sessions = war.list_app_sessions()
            self._last_error = None
            return sessions or []
        except Exception as error:
            self._last_error = str(error)
            return []

    def app_has_audio_session(self, application_name):
        if not application_name:
            return False

        target = application_name.lower()

        try:
            sessions = self.get_audio_sessions()

            for session in sessions:
                text = str(session).lower()

                if target in text:
                    return True

            return False
        except Exception as error:
            self._last_error = str(error)
            return False

    def enable_route(self, application_name, output_device_name):
        if not self.routing_backend_available():
            return {
                "ok": False,
                "message": (
                    "Automatic routing backend is unavailable. "
                    "Use Windows Sound Settings instead."
                ),
            }

        if not application_name or not output_device_name:
            return {
                "ok": False,
                "message": "Select an application and output device first.",
            }

        try:
            war.set_app_output_device(
                process_name=application_name,
                device=output_device_name,
            )

            self._last_error = None

            return {
                "ok": True,
                "message": (
                    f"Route requested: {application_name} "
                    f"→ {output_device_name}"
                ),
            }

        except Exception as error:
            self._last_error = str(error)

            return {
                "ok": False,
                "message": str(error),
            }

    def disable_route(self, application_name):
        if not self.routing_backend_available():
            return {
                "ok": False,
                "message": "Automatic routing backend is unavailable.",
            }

        if not application_name:
            return {
                "ok": False,
                "message": "Select an application first.",
            }

        try:
            war.clear_app_output_device(
                process_name=application_name,
            )

            self._last_error = None

            return {
                "ok": True,
                "message": (
                    f"Routing cleared for {application_name}; "
                    "Windows system default will be used."
                ),
            }

        except Exception as error:
            self._last_error = str(error)

            return {
                "ok": False,
                "message": str(error),
            }

    def get_persisted_route(self, application_name):
        if (
            not self.routing_backend_available()
            or not application_name
        ):
            return None

        try:
            result = war.get_app_output_device(
                process_name=application_name,
            )

            self._last_error = None
            return result

        except Exception as error:
            self._last_error = str(error)
            return None

    def _normalize_output_device_name(
        self,
        device_name,
    ):
        """
        Normalize names reported by sounddevice/PortAudio and
        winappaudiorouter so the same Windows endpoint can be matched.

        Example:
          sounddevice:
            CABLE In 16ch (VB-Audio Virtual Cable) [MME]
          Windows endpoint:
            CABLE In 16ch (VB-Audio Virtual Cable)
        """
        if not device_name:
            return ""

        name = str(device_name).strip()

        # PortAudio host API suffixes are not part of the Windows
        # endpoint's friendly name.
        name = re.sub(
            r"\s*\[(MME|WDM-KS|WASAPI|DirectSound)\]\s*$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Collapse whitespace for stable comparisons.
        name = " ".join(
            name.split()
        )

        return name.casefold()

    def _find_war_output_device(
        self,
        output_device_name,
    ):
        if (
            not self.routing_backend_available()
            or not output_device_name
        ):
            return None

        target = (
            self._normalize_output_device_name(
                output_device_name
            )
        )

        try:
            devices = war.list_output_devices()

            # First preference: normalized exact match.
            for device in devices:
                candidate = (
                    self._normalize_output_device_name(
                        device.name
                    )
                )

                if candidate == target:
                    self._last_error = None
                    return device

            # Some PortAudio builds truncate long friendly names in
            # their device list. Safely accept a unique prefix match.
            prefix_matches = []

            for device in devices:
                candidate = (
                    self._normalize_output_device_name(
                        device.name
                    )
                )

                if (
                    target
                    and candidate
                    and (
                        candidate.startswith(target)
                        or target.startswith(candidate)
                    )
                ):
                    prefix_matches.append(
                        device
                    )

            if len(prefix_matches) == 1:
                self._last_error = None
                return prefix_matches[0]

            self._last_error = (
                "Could not uniquely map audio device "
                f"'{output_device_name}' to a Windows endpoint."
            )

            return None

        except Exception as error:
            self._last_error = str(error)
            return None

    def get_target_endpoint_id(
        self,
        output_device_name,
    ):
        device = self._find_war_output_device(
            output_device_name
        )

        if device is None:
            return None

        return str(
            device.id
        )

    def route_matches(
        self,
        application_name,
        output_device_name,
    ):
        if (
            not application_name
            or not output_device_name
        ):
            return False

        target_endpoint_id = (
            self.get_target_endpoint_id(
                output_device_name
            )
        )

        if not target_endpoint_id:
            return False

        persisted = self.get_persisted_route(
            application_name
        )

        if not persisted:
            return False

        target_lower = (
            target_endpoint_id
            .strip()
            .lower()
        )

        # winappaudiorouter returns:
        # {pid: "{endpoint-guid}", ...}
        if isinstance(
            persisted,
            dict,
        ):
            for endpoint_id in persisted.values():
                if (
                    str(endpoint_id)
                    .strip()
                    .lower()
                    == target_lower
                ):
                    return True

            return False

        return (
            target_lower
            in str(persisted).lower()
        )

    def get_active_app_session(
        self,
        application_name,
    ):
        if (
            not self.routing_backend_available()
            or not application_name
        ):
            return None

        target = (
            application_name
            .strip()
            .lower()
        )

        try:
            sessions = war.list_app_sessions()

            for session in sessions:
                process_name = getattr(
                    session,
                    "process_name",
                    None,
                )

                if (
                    process_name
                    and str(process_name)
                    .strip()
                    .lower()
                    == target
                ):
                    return session

            return None

        except Exception as error:
            self._last_error = str(error)
            return None

    def get_route_state(
        self,
        application_name,
        output_device_name,
    ):
        """
        Return both the persisted Windows preference and the device
        currently hosting the app's active audio session.

        Windows may save a per-app route immediately while an already
        running session remains on the old endpoint until playback or the
        app is restarted.
        """
        target_endpoint_id = (
            self.get_target_endpoint_id(
                output_device_name
            )
        )

        persisted_matches = self.route_matches(
            application_name,
            output_device_name,
        )

        session = self.get_active_app_session(
            application_name
        )

        active_matches = False
        active_device_name = None
        active_device_id = None

        if session is not None:
            active_device_name = getattr(
                session,
                "device_name",
                None,
            )

            active_device_id = getattr(
                session,
                "device_id",
                None,
            )

            if (
                target_endpoint_id
                and active_device_id
            ):
                active_matches = (
                    str(active_device_id)
                    .strip()
                    .lower()
                    ==
                    str(target_endpoint_id)
                    .strip()
                    .lower()
                )

        return {
            "persisted": persisted_matches,
            "active": active_matches,
            "active_device_name": active_device_name,
            "active_device_id": active_device_id,
            "target_device_id": target_endpoint_id,
            "has_session": session is not None,
        }

    def open_windows_sound_settings(self):
        if not self.is_supported():
            return False

        try:
            os.startfile(
                "ms-settings:apps-volume"
            )

            self._last_error = None
            return True

        except Exception:
            try:
                os.startfile(
                    "ms-settings:sound"
                )

                self._last_error = None
                return True

            except Exception as error:
                self._last_error = str(error)
                return False
