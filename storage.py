"""Cross-platform storage helper for picking a folder of .gpx files.

Strategy:
  * On Android (platform == "android"): use androidstorage4kivy to open a
    Storage Access Framework folder picker and return the granted URI. The
    URI is persisted in the app's private prefs and we use DocumentFile APIs
    to list it on subsequent runs.
  * Everywhere else (desktop, laptop): fall back to a plain text-input
    dialog asking for a folder path. This is enough to develop and test
    the UI without a real Android device.

Public API:
  pick_folder(callback) -> None
      Opens the appropriate picker; on selection, calls callback(folder_id)
      where folder_id is a SAF URI string on Android or an absolute path
      elsewhere.

  list_gpx(folder_id) -> [str] or None
      Returns filenames inside the folder, or None if unreadable.

  read_gpx(folder_id, filename) -> bytes or None
      Reads the GPX file as bytes.

  save_folder_id(app, folder_id) / load_folder_id(app) -> str or None
      Persists the picked folder across restarts.
"""

import os
import sys
from kivy.utils import platform as kivy_platform


_FOLDER_PREFS = "folder_id"


def _is_android():
    return kivy_platform == "android"


# ---- folder id persistence (shared by both platforms) ----

def save_folder_id(app, folder_id):
    if not folder_id:
        return
    try:
        from kivy.storage.jsonstore import JsonStore
        store = JsonStore(os.path.join(app.user_data_dir, "prefs.json"))
        store.put(_FOLDER_PREFS, value=folder_id)
    except Exception:
        pass


def load_folder_id(app):
    try:
        from kivy.storage.jsonstore import JsonStore
        store = JsonStore(os.path.join(app.user_data_dir, "prefs.json"))
        if _FOLDER_PREFS in store:
            return store.get(_FOLDER_PREFS).get("value")
    except Exception:
        return None
    return None


# ---- desktop / fallback ----

def _pick_folder_desktop(callback):
    from kivy.uix.popup import Popup
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.textinput import TextInput
    from kivy.uix.button import Button
    from kivy.uix.label import Label

    box = BoxLayout(orientation="vertical", padding=12, spacing=8)
    box.add_widget(Label(text="Enter the folder containing your .gpx files:",
                         size_hint_y=None, height=32))
    ti = TextInput(text="", multiline=False, hint_text="/path/to/folder")
    box.add_widget(ti)
    row = BoxLayout(size_hint_y=None, height=48, spacing=8)
    btn_ok = Button(text="OK")
    btn_cancel = Button(text="Cancel")
    row.add_widget(btn_ok)
    row.add_widget(btn_cancel)
    box.add_widget(row)
    popup = Popup(title="Choose folder", content=box, size_hint=(0.9, 0.5))

    def _ok(_):
        val = ti.text.strip()
        popup.dismiss()
        if val:
            callback(val)

    def _cancel(_):
        popup.dismiss()

    btn_ok.bind(on_release=_ok)
    btn_cancel.bind(on_release=_cancel)
    popup.open()


def _list_gpx_desktop(folder_id):
    if not folder_id or not os.path.isdir(folder_id):
        return None
    try:
        return sorted(f for f in os.listdir(folder_id) if f.lower().endswith(".gpx"))
    except OSError:
        return None


def _read_gpx_desktop(folder_id, filename):
    path = os.path.join(folder_id, filename)
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


# ---- Android via androidstorage4kivy ----

def _pick_folder_android(callback):
    try:
        from androidstorage4kivy import SharedStorage, choose_folder  # type: ignore
    except Exception as ex:
        # Library not available (e.g. testing on desktop, build missing
        # the recipe). Tell the user and fall back to nothing.
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        Popup(title="Storage error",
              content=Label(text=f"androidstorage4kivy missing:\n{ex}"),
              size_hint=(0.8, 0.4)).open()
        return

    def _on_pick(uri):
        callback(uri)

    try:
        choose_folder(on_selection=_on_pick)
    except Exception as ex:
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        Popup(title="Pick folder error",
              content=Label(text=f"Could not open folder picker:\n{ex}"),
              size_hint=(0.8, 0.4)).open()


def _list_gpx_android(folder_id):
    try:
        from androidstorage4kivy import SharedStorage  # type: ignore
        ss = SharedStorage()
        # SharedStorage.list_files returns file metadata dicts for the
        # documents under the chosen folder. Filter by extension.
        files = ss.list_files(folder_id) or []
        names = []
        for entry in files:
            name = entry.get("name", "")
            if name.lower().endswith(".gpx"):
                names.append(name)
        return sorted(names)
    except Exception:
        return None


def _read_gpx_android(folder_id, filename):
    try:
        from androidstorage4kivy import SharedStorage  # type: ignore
        ss = SharedStorage()
        return ss.read_file(folder_id, filename)
    except Exception:
        return None


# ---- public dispatchers ----

def pick_folder(callback):
    if _is_android():
        _pick_folder_android(callback)
    else:
        _pick_folder_desktop(callback)


def list_gpx(folder_id):
    if not folder_id:
        return None
    if _is_android() and folder_id.startswith("content://"):
        return _list_gpx_android(folder_id)
    return _list_gpx_desktop(folder_id)


def read_gpx(folder_id, filename):
    if not folder_id or not filename:
        return None
    if _is_android() and folder_id.startswith("content://"):
        return _read_gpx_android(folder_id, filename)
    return _read_gpx_desktop(folder_id, filename)
