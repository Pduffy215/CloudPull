import os
import sys
import json


# ── Project working folders ──────────────────────────────────────────────────
# Base folder for this project's own working files (output JSON, logs).
# Defaults to the folder this config.py lives in, so it travels with the
# project automatically - no machine-specific username needed.
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

CONFIG_DIR     = os.path.join(PROJECT_ROOT, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
LOG_FILE       = os.path.join(CONFIG_DIR, "monitorLog.txt")
ICON_PATH = os.path.join(PROJECT_ROOT, "assets", "vsc_icon.ico")

# ── External, user-editable settings ────────────────────────────────────────
# Lives next to the .exe (or next to Config.py when run from source), NOT
# bundled inside PyInstaller's package - so it can be edited without a rebuild.
SETTINGS_PATH = os.path.join(CONFIG_DIR, "default_config.json")

# Defaults used for any key missing from config.json, and used to generate
# a starter config.json the first time the app runs somewhere new.
_DEFAULTS = {
    "PROTECT_SERVER_URL": "http://vscprotect.twintechlabs.io",
    "ARCA_URL": "http://vscarca.twintechlabs.io/",
    "ARCA_API_KEY": "7740a73c-f497-4d7f-8e68-200b071ff320",
    "WINPROTECT_BASE_PATH": r"C:\VSC\WinProtect",
    "DEFAULT_FOLDER": r"C:\VSC2\Recorder\Data",
}


def _load_settings():
    if not os.path.isfile(SETTINGS_PATH):
        # First run on this machine - write a starter config.json using the
        # defaults, so there's immediately something the user can find and edit.
        with open(SETTINGS_PATH, "w") as f:
            json.dump(_DEFAULTS, f, indent=4)
        return dict(_DEFAULTS)

    try:
        with open(SETTINGS_PATH, "r") as f:
            loaded = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        # Malformed config.json - fail loudly rather than silently running
        # with wrong/missing values. Better to see this at startup than to
        # debug a mysterious failure three steps into a pipeline run.
        raise RuntimeError(
            f"Failed to read {SETTINGS_PATH}: {e}\n"
            f"Check the file for typos (missing commas/quotes are the usual cause), "
            f"or delete it to regenerate a fresh default copy."
        ) from e

    # Fill in any keys the user's file is missing with defaults, rather than
    # KeyError-ing deep in the pipeline the first time that value is used.
    merged = dict(_DEFAULTS)
    merged.update(loaded)
    return merged


_settings = _load_settings()

ARCA_URL            = _settings["ARCA_URL"]

# ── API keys / credentials ──────────────────────────────────────────────────
ARCA_API_KEY = _settings["ARCA_API_KEY"]

