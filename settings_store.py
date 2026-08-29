"""Persists the user's physical/physiological settings to a JSON file in
the app's private data directory. Survives app restarts and updates.

Used by main.py for both reading (at startup, before showing any screen)
and writing (when the user taps Save in the settings screen).
"""

import json
import os

from analyzer import get_default_settings

_SETTINGS_FILENAME = "settings.json"


def settings_path(app):
    """Return absolute path to the settings JSON. app is a Kivy App or
    anything with a `.user_data_dir` attribute; we also accept a plain str."""
    try:
        d = app.user_data_dir
    except AttributeError:
        d = os.path.dirname(str(app))
    if not os.path.isdir(d):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
    return os.path.join(d, _SETTINGS_FILENAME)


def load_settings(app):
    """Return the saved settings dict, or a defaults dict on first run /
    if the file is missing or unparseable. Always returns a dict."""
    path = settings_path(app)
    if not os.path.isfile(path):
        return get_default_settings()
    try:
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, ValueError):
        return get_default_settings()
    if not isinstance(saved, dict):
        return get_default_settings()
    # merge on top of defaults so new keys get filled in
    out = get_default_settings()
    for k, v in saved.items():
        out[k] = v
    return out


def save_settings(app, settings):
    """Persist the settings dict to disk. Best-effort; returns True on success."""
    if not isinstance(settings, dict):
        return False
    path = settings_path(app)
    try:
        # write to temp + replace, so a crash mid-write doesn't corrupt
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
        return True
    except OSError:
        return False
