"""Ride Analyzer - main app and UI.

KivyMD screens:
  HomeScreen       - homepage.jpg background, big tappable cards
  RideListScreen   - list of .gpx files in the chosen folder
  RideDetailScreen - shows the analysis result for one ride
  SettingsScreen   - edit rider / bike / physics constants

Theme:
  Dark by default. Background sampled from the bottom of homepage.jpg
  (#27141A, dark maroon). Accent is the green from the image's middle
  band (#2B9C4C) so the home screen "Analyze a ride" card feels at home
  against the homepage image.
"""

import io
import os
import threading
from datetime import datetime

from kivy.config import Config
# Restrict to portrait phones, but keep it minimal - android will rotate
# if the user does. We just don't ask for a desktop window.
Config.set("input", "mouse", "mouse,multitouch_on_demand")

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp
from kivy.utils import platform as kivy_platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import OneLineListItem, TwoLineListItem, MDList
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.fitimage import FitImage
from kivymd.uix.snackbar import Snackbar

import analyzer
import storage
import settings_store


# ---- theme constants (extracted from homepage.jpg) ----
BG_DARK    = (0.094, 0.039, 0.067, 1)   # #18100F dark maroon, easier on eyes than pure black
SURFACE    = (0.122, 0.067, 0.094, 1)   # slightly lighter card surface
ACCENT     = (0.169, 0.612, 0.298, 1)   # #2B9C4C from the green band of the image
ACCENT_LIGHT = (0.78, 0.61, 0.71, 1)    # #C79BB4 dusty rose from the top of the image
TEXT_PRIMARY  = (0.95, 0.95, 0.95, 1)
TEXT_SECONDARY = (0.70, 0.70, 0.72, 1)


# ---- KV layout (Kivy language) ----
KV = r"""
#:import FadeTransition kivy.uix.screenmanager.FadeTransition
#:import dp kivy.metrics.dp

<HomeScreen>:
    name: "home"
    md_bg_color: app.bg_dark

    FloatLayout:
        id: bg_layer
        size_hint: 1, 1
        # FitImage fills the whole screen; on top of it a dark wash so
        # the foreground text is always readable regardless of the image.
        FitImage:
            id: bg
            source: app.homepage_source
            size_hint: 1, 1
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            allow_stretch: True
            keep_ratio: False
        Canvas:
            color: 0, 0, 0, 0.55
            Rectangle:
                pos: self.pos
                size: self.size

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20), dp(40), dp(20), dp(24)
            spacing: dp(16)
            size_hint: 1, 1

            MDLabel:
                text: "Ride Analyzer"
                font_style: "H3"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                halign: "center"
                size_hint_y: None
                height: dp(56)
                bold: True

            MDLabel:
                text: "GPS ride breakdowns, calories, pauses."
                font_style: "Subtitle1"
                theme_text_color: "Custom"
                text_color: 0.85, 0.85, 0.85, 1
                halign: "center"
                size_hint_y: None
                height: dp(28)

            Widget:
                size_hint_y: 1

            MDCard:
                id: card_analyze
                orientation: "vertical"
                padding: dp(20), dp(20), dp(20), dp(20)
                spacing: dp(6)
                size_hint: 1, None
                height: dp(110)
                md_bg_color: app.accent
                radius: [dp(18)]
                elevation: 6
                on_release: app.go_to_rides()

                MDLabel:
                    text: "Analyze a ride"
                    font_style: "H5"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                MDLabel:
                    text: "Open your latest .gpx and see the full breakdown"
                    font_style: "Body1"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 0.92

            MDCard:
                id: card_settings
                orientation: "vertical"
                padding: dp(20), dp(20), dp(20), dp(20)
                spacing: dp(6)
                size_hint: 1, None
                height: dp(90)
                md_bg_color: app.surface
                radius: [dp(18)]
                elevation: 3
                on_release: app.go_to_settings()

                MDLabel:
                    text: "Settings"
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                MDLabel:
                    text: "Rider weight, BMR, physics constants"
                    font_style: "Body2"
                    theme_text_color: "Custom"
                    text_color: 0.78, 0.78, 0.80, 1

            MDCard:
                id: card_about
                orientation: "vertical"
                padding: dp(20), dp(20), dp(20), dp(20)
                spacing: dp(6)
                size_hint: 1, None
                height: dp(90)
                md_bg_color: app.surface
                radius: [dp(18)]
                elevation: 3
                on_release: app.show_about()

                MDLabel:
                    text: "About"
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    bold: True
                MDLabel:
                    text: "Calorie model, build, version"
                    font_style: "Body2"
                    theme_text_color: "Custom"
                    text_color: 0.78, 0.78, 0.80, 1


<RideListScreen>:
    name: "rides"
    md_bg_color: app.bg_dark

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: toolbar
            title: "Rides"
            elevation: 4
            left_action_items: [["arrow-left", lambda x: app.go_home()]]
            right_action_items: [["folder-refresh", lambda x: app.refresh_rides()], ["folder", lambda x: app.pick_folder()]]
            md_bg_color: app.surface
            specific_text_color: 1, 1, 1, 1

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(12), dp(8), dp(12), dp(8)
            spacing: dp(8)

            MDTextField:
                id: search
                hint_text: "Search by filename"
                mode: "round"
                icon_left: "magnify"
                on_text: app.filter_rides(self.text)

            MDProgressBar:
                id: progress
                value: 0
                size_hint_y: None
                height: dp(3)
                opacity: 0

        ScrollView:
            id: scroller
            MDList:
                id: ride_list
                padding: 0, 0, 0, dp(16)
                spacing: dp(2)


<RideDetailScreen>:
    name: "detail"
    md_bg_color: app.bg_dark

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Ride"
            elevation: 4
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            md_bg_color: app.surface
            specific_text_color: 1, 1, 1, 1

        ScrollView:
            MDBoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(14)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True


<SettingsScreen>:
    name: "settings"
    md_bg_color: app.bg_dark

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Settings"
            elevation: 4
            left_action_items: [["arrow-left", lambda x: app.go_back()]]
            right_action_items: [["content-save", lambda x: app.save_settings()]]
            md_bg_color: app.surface
            specific_text_color: 1, 1, 1, 1

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: dp(16)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                adaptive_height: True

                MDLabel:
                    text: "Rider"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: app.accent
                    bold: True
                    size_hint_y: None
                    height: dp(28)

                MDTextField:
                    id: rider_weight
                    hint_text: "Rider weight (kg)"
                    text: str(app.settings["rider_weight_kg"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: bike_weight
                    hint_text: "Bike weight (kg)"
                    text: str(app.settings["bike_weight_kg"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: rider_height
                    hint_text: "Rider height (cm)"
                    text: str(app.settings["rider_height_cm"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: rider_age
                    hint_text: "Rider age (years)"
                    text: str(app.settings["rider_age"])
                    input_filter: "int"
                    mode: "rect"

                MDLabel:
                    text: "Sex (for BMR)"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.78, 0.78, 0.80, 1
                    size_hint_y: None
                    height: dp(24)

                MDBoxLayout:
                    id: sex_box
                    orientation: "horizontal"
                    spacing: dp(8)
                    size_hint_y: None
                    height: dp(48)
                    adaptive_width: False

                MDLabel:
                    text: " "
                    size_hint_y: None
                    height: dp(12)

                MDLabel:
                    text: "Physics"
                    font_style: "Subtitle1"
                    theme_text_color: "Custom"
                    text_color: app.accent
                    bold: True
                    size_hint_y: None
                    height: dp(28)

                MDTextField:
                    id: crr
                    hint_text: "Rolling resistance (CRR)"
                    text: str(app.settings["crr"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: cda
                    hint_text: "Drag area (CdA, m^2)"
                    text: str(app.settings["cda"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: epoc
                    hint_text: "EPOC factor (e.g. 0.10)"
                    text: str(app.settings["epoc_factor"])
                    input_filter: "float"
                    mode: "rect"

                MDTextField:
                    id: ele_smooth
                    hint_text: "Elevation smoothing window (samples)"
                    text: str(app.settings["ele_smooth"])
                    input_filter: "int"
                    mode: "rect"

                MDTextField:
                    id: ele_max
                    hint_text: "Elevation spike cap (m)"
                    text: str(app.settings["ele_max_m"])
                    input_filter: "float"
                    mode: "rect"

                MDRaisedButton:
                    text: "Reset to defaults"
                    md_bg_color: app.surface
                    text_color: 1, 1, 1, 1
                    on_release: app.reset_settings()
                    size_hint_y: None
                    height: dp(48)

                MDLabel:
                    id: bmr_preview
                    text: ""
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.78, 0.78, 0.80, 1
                    size_hint_y: None
                    height: dp(48)
                    halign: "center"
"""


# ---- card factory for the detail screen ----

def _kv_card():
    """Build an MDCard with vertical padding. Helper because every section
    on the detail screen uses the same shape."""
    return MDCard(
        orientation="vertical",
        padding=[dp(14), dp(12), dp(14), dp(12)],
        spacing=dp(4),
        size_hint=(1, None),
        md_bg_color=SURFACE,
        radius=[dp(12)],
        elevation=2,
    )


def _kv_label(text, font_style="Body1", bold=False, color=None):
    return MDLabel(
        text=text,
        font_style=font_style,
        bold=bold,
        theme_text_color="Custom",
        text_color=color if color else TEXT_PRIMARY,
        size_hint_y=None,
        adaptive_height=True,
    )


# ---- screens ----

class HomeScreen(MDScreen):
    pass


class RideListScreen(MDScreen):
    pass


class RideDetailScreen(MDScreen):
    pass


class SettingsScreen(MDScreen):
    pass


# ---- app ----

class RideAnalyzerApp(MDApp):
    bg_dark = BG_DARK
    surface = SURFACE
    accent = ACCENT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings = {}
        self._folder_id = None
        self._all_rides = []        # full list of (filename, mtime, size)
        self._filtered_rides = []   # after search filter
        self._search_text = ""
        self._current_detail = None
        self._sex_buttons = None    # M/F segmented control
        self._progress_dialog = None
        self._sm = None

    # -- Kivy lifecycle --

    def build(self):
        self.title = "Ride Analyzer"
        self.icon = os.path.join("assets", "icon.png")
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.accent_palette = "Pink"
        self.theme_cls.accent_hue = "200"

        # settings + folder id
        self._settings = settings_store.load_settings(self)
        analyzer.apply_settings(self._settings)
        analyzer.set_settings_provider(lambda: self._settings)
        self._folder_id = storage.load_folder_id(self)

        # KV
        Builder.load_string(KV)
        self._sm = MDScreenManager(transition=None)
        self._sm.add_widget(HomeScreen())
        self._sm.add_widget(RideListScreen())
        self._sm.add_widget(RideDetailScreen())
        self._sm.add_widget(SettingsScreen())

        # wire search debounce
        Clock.schedule_once(self._post_build, 0)
        return self._sm

    @property
    def homepage_source(self):
        # on Android, packaged resource is in the apk
        for p in [os.path.join("assets", "homepage.jpg"),
                  "/data/data/org.dominik.rideanalyzer/files/app/assets/homepage.jpg"]:
            if os.path.isfile(p):
                return p
        return os.path.join("assets", "homepage.jpg")

    def _post_build(self, _dt):
        # Build the Sex segmented control programmatically (KV doesn't have
        # one out of the box in KivyMD 1.2.0).
        settings_screen = self._sm.get_screen("settings")
        sex_box = settings_screen.ids.sex_box
        from kivymd.uix.segmentedcontrol import MDSegmentedControl, MDSegmentedControlItem
        try:
            control = MDSegmentedControl()
            control.add_widget(MDSegmentedControlItem(text="Male",
                                active=(self._settings.get("rider_male", True))))
            control.add_widget(MDSegmentedControlItem(text="Female",
                                active=(not self._settings.get("rider_male", True))))
            sex_box.add_widget(control)
            self._sex_buttons = control
        except Exception:
            # Fallback: two plain chips
            from kivymd.uix.chip import MDChip
            male = MDChip(text="Male",
                          active=(self._settings.get("rider_male", True)))
            female = MDChip(text="Female",
                            active=(not self._settings.get("rider_male", True)))
            sex_box.add_widget(male)
            sex_box.add_widget(female)
            self._sex_buttons = {"male": male, "female": female}

        # update BMR preview
        self._refresh_bmr_preview()

    # -- navigation --

    def go_home(self):
        self._sm.current = "home"

    def go_back(self):
        if self._sm.current == "detail":
            self._sm.current = "rides"
        else:
            self._sm.current = "home"

    def go_to_rides(self):
        if not self._folder_id:
            self.pick_folder()
            return
        self._sm.current = "rides"
        self.refresh_rides()

    def go_to_settings(self):
        self._sm.current = "settings"

    # -- about dialog --

    def show_about(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        body = (
            "Ride Analyzer v1.0\n\n"
            "Calorie model: per-km chunked mechanical work, gross "
            "metabolic cost via EFF_GROSS = 0.22, plus EPOC. BMR is "
            "Mifflin-St Jeor. You decide whether to subtract BMR.\n\n"
            "Elevation: rolling mean (ELE_SMOOTH) then summed deltas, "
            "ignoring samples above ELE_MAX_M.\n\n"
            "Pauses: time gaps + standstill runs, merged if close enough. "
            "GPS dropouts (big jumps) are reported separately."
        )
        dlg = MDDialog(title="About",
                       text=body,
                       size_hint=(0.85, 0.7),
                       buttons=[MDFlatButton(text="Close",
                                             on_release=lambda x: dlg.dismiss())])
        dlg.open()

    # -- folder picker + ride list --

    def pick_folder(self):
        storage.pick_folder(self._on_folder_picked)

    def _on_folder_picked(self, folder_id):
        if not folder_id:
            return
        self._folder_id = folder_id
        storage.save_folder_id(self, folder_id)
        if self._sm.current != "rides":
            self._sm.current = "rides"
        self.refresh_rides()

    def refresh_rides(self):
        if not self._folder_id:
            self._show_message("Pick a folder first (folder icon, top right).")
            return
        # clear + show progress
        ride_list = self._sm.get_screen("rides").ids.ride_list
        ride_list.clear_widgets()
        progress = self._sm.get_screen("rides").ids.progress
        progress.opacity = 1
        progress.start()

        def _worker():
            names = storage.list_gpx(self._folder_id) or []
            # best-effort: pull mtime for sort
            entries = []
            for n in names:
                mtime = 0
                try:
                    data = storage.read_gpx(self._folder_id, n)
                    if data:
                        # we don't have stat; fall back to 0 - sort by name
                        pass
                except Exception:
                    pass
                entries.append((n, mtime))
            entries.sort(key=lambda e: e[0].lower(), reverse=False)
            Clock.schedule_once(lambda dt: self._on_rides_loaded(entries), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_rides_loaded(self, entries):
        self._all_rides = entries
        self._filtered_rides = list(entries)
        progress = self._sm.get_screen("rides").ids.progress
        progress.stop()
        progress.opacity = 0
        self._rebuild_ride_list()

    def filter_rides(self, q):
        self._search_text = (q or "").strip().lower()
        if not self._search_text:
            self._filtered_rides = list(self._all_rides)
        else:
            self._filtered_rides = [(n, m) for (n, m) in self._all_rides
                                    if self._search_text in n.lower()]
        self._rebuild_ride_list()

    def _rebuild_ride_list(self):
        ride_list = self._sm.get_screen("rides").ids.ride_list
        ride_list.clear_widgets()
        if not self._filtered_rides:
            empty = OneLineListItem(text="No .gpx files in this folder")
            ride_list.add_widget(empty)
            return
        for (name, _mtime) in self._filtered_rides:
            item = TwoLineListItem(
                text=name,
                secondary_text="Tap to analyze",
                on_release=lambda _btn, n=name: self.open_ride(n),
            )
            ride_list.add_widget(item)

    def open_ride(self, filename):
        # show progress, then run analyze in background
        self._sm.current = "detail"
        content = self._sm.get_screen("detail").ids.content
        content.clear_widgets()
        loading = _kv_label(f"Analyzing {filename}...", color=TEXT_SECONDARY)
        content.add_widget(loading)

        def _worker():
            try:
                data = storage.read_gpx(self._folder_id, filename)
                if data is None:
                    res = {"ok": False, "error": "Could not read file",
                           "filename": filename}
                else:
                    # analyzer.analyze needs a path on Android (SharedStorage
                    # uses URIs, not paths). Save the bytes to a temp file in
                    # the app's cache dir, then analyze that path, then clean up.
                    import tempfile
                    tmp_dir = self.user_data_dir
                    tmp_path = os.path.join(tmp_dir, "_tmp_" + filename.replace("/", "_"))
                    with open(tmp_path, "wb") as f:
                        f.write(data)
                    try:
                        res = analyzer.analyze(tmp_path)
                    finally:
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception as ex:
                res = {"ok": False, "error": str(ex), "filename": filename}
            Clock.schedule_once(lambda dt, r=res: self._render_detail(r), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _render_detail(self, r):
        content = self._sm.get_screen("detail").ids.content
        content.clear_widgets()
        # update toolbar title
        toolbar = self._sm.get_screen("detail").ids.toolbar
        toolbar.title = r.get("filename", "Ride")

        if not r.get("ok"):
            card = _kv_card()
            card.add_widget(_kv_label("Error", font_style="H6", color=ACCENT))
            card.add_widget(_kv_label(r.get("error", "Unknown error"),
                                      color=TEXT_SECONDARY))
            content.add_widget(card)
            return

        # header card
        header = _kv_card()
        header.add_widget(_kv_label(r["filename"], font_style="H6", bold=True))
        if r.get("start_loc") or r.get("end_loc"):
            track = f"{r.get('start_loc', '?')}  ->  {r.get('end_loc', '?')}"
            header.add_widget(_kv_label(track, color=TEXT_SECONDARY,
                                        font_style="Caption"))
        header.add_widget(_kv_label(
            f"{r['start']} - {r['end']}  (elapsed {r['elapsed_hm']} h)",
            color=TEXT_PRIMARY))
        header.add_widget(_kv_label(
            f"{r['distance_km']:.1f} km  -  {r['riding_min']:.1f} min riding",
            font_style="H6", color=ACCENT, bold=True))
        content.add_widget(header)
        # size the card to fit its children
        self._fit_card_height(header)

        # elevation
        ele_card = _kv_card()
        ele_card.add_widget(_kv_label("Elevation", font_style="Subtitle1",
                                      bold=True, color=ACCENT))
        if r["has_ele"]:
            ele_card.add_widget(_kv_label(
                f"Gain: {r['gain_m']:.0f} m   Loss: {r['loss_m']:.0f} m   "
                f"Net: {r['net_m']:+.0f} m"))
        else:
            ele_card.add_widget(_kv_label("n/a (no <ele> tags in this GPX)",
                                         color=TEXT_SECONDARY))
        content.add_widget(ele_card)
        self._fit_card_height(ele_card)

        # calories
        c = r["calories"]
        cal_card = _kv_card()
        cal_card.add_widget(_kv_label("Calories", font_style="Subtitle1",
                                      bold=True, color=ACCENT))
        cal_card.add_widget(_kv_label(
            f"{c['full']:.0f} kcal", font_style="H4", bold=True))
        cal_card.add_widget(_kv_label(
            f"Full ride cost ({c['n_chunks']} km-chunks, "
            f"EPOC x{c['epoc_factor']:.2f})",
            color=TEXT_SECONDARY, font_style="Caption"))
        cal_card.add_widget(_kv_label(
            f"detail: gross {c['gross']:.0f} + EPOC {c['epoc']:.0f} = "
            f"{c['full']:.0f} kcal",
            font_style="Caption", color=TEXT_SECONDARY))
        cal_card.add_widget(_kv_label(
            f"-> minus ~{c['bmr']:.0f} kcal BMR = {c['delta']:.0f} kcal "
            f"if you want delta-vs-rest",
            font_style="Caption", color=TEXT_SECONDARY))
        content.add_widget(cal_card)
        self._fit_card_height(cal_card)

        # pauses
        p_card = _kv_card()
        p_card.add_widget(_kv_label("Pauses", font_style="Subtitle1",
                                    bold=True, color=ACCENT))
        p_card.add_widget(_kv_label(
            f"{r['n_stops']} pauses  -  {r['stop_min']:.1f} min stopped",
            font_style="H6"))
        if r["pauses"]:
            for p in r["pauses"]:
                line = f"{p['start']} - {p['end']}  {p['dur_min']:.1f} min"
                if p.get("loc"):
                    line += f"  -  {p['loc']}"
                p_card.add_widget(_kv_label(line, font_style="Body2",
                                            color=TEXT_SECONDARY))
        else:
            p_card.add_widget(_kv_label("none", color=TEXT_SECONDARY,
                                        font_style="Body2"))
        content.add_widget(p_card)
        self._fit_card_height(p_card)

        # summary footer
        s_card = _kv_card()
        s_card.add_widget(_kv_label("Summary", font_style="Subtitle1",
                                    bold=True, color=ACCENT))
        s_card.add_widget(_kv_label(
            f"Average riding speed: {r['avg_riding_kmh']:.1f} km/h"))
        s_card.add_widget(_kv_label(
            f"Pauses >= 1 min: {r['n_stops']} ({r['stop_min']:.1f} min)",
            color=TEXT_SECONDARY, font_style="Caption"))
        s_card.add_widget(_kv_label(
            f"GPS dropouts: {r['n_dropout']}  -  "
            f"micro-stops < 1 min: {r['n_micro']}  -  "
            f"end blips: {r['n_end_artifact']}",
            color=TEXT_SECONDARY, font_style="Caption"))
        content.add_widget(s_card)
        self._fit_card_height(s_card)

    def _fit_card_height(self, card):
        """Resize the card to fit its children's total height. MDCard defaults
        to a height that clips its children when adaptive_height is off."""
        h = 0
        for child in card.children:
            h += child.height
        h += dp(24)  # padding top + bottom
        card.height = h

    # -- settings --

    def _read_settings_widgets(self):
        s = self._sm.get_screen("settings")
        out = {}
        for key, wid in [
            ("rider_weight_kg", s.ids.rider_weight),
            ("bike_weight_kg",  s.ids.bike_weight),
            ("rider_height_cm", s.ids.rider_height),
            ("rider_age",       s.ids.rider_age),
            ("crr",             s.ids.crr),
            ("cda",             s.ids.cda),
            ("epoc_factor",     s.ids.epoc),
            ("ele_smooth",      s.ids.ele_smooth),
            ("ele_max_m",       s.ids.ele_max),
        ]:
            try:
                out[key] = float(wid.text)
                if key == "rider_age" or key == "ele_smooth":
                    out[key] = int(out[key])
            except (ValueError, TypeError):
                out[key] = self._settings.get(key)
        # sex segmented control
        male = True
        if self._sex_buttons is not None:
            if isinstance(self._sex_buttons, dict):
                male = self._sex_buttons["male"].active
            else:
                # MDSegmentedControl: read .items
                try:
                    items = list(self._sex_buttons.items)
                    male = True
                    for it in items:
                        if "male" in it.text.lower() and not it.active:
                            male = False
                except Exception:
                    male = True
        out["rider_male"] = male
        return out

    def save_settings(self):
        new = self._read_settings_widgets()
        self._settings.update(new)
        if settings_store.save_settings(self, self._settings):
            analyzer.apply_settings(self._settings)
            self._refresh_bmr_preview()
            self._show_message("Settings saved.")
        else:
            self._show_message("Could not save settings.")

    def reset_settings(self):
        self._settings = analyzer.get_default_settings()
        s = self._sm.get_screen("settings")
        s.ids.rider_weight.text = str(self._settings["rider_weight_kg"])
        s.ids.bike_weight.text  = str(self._settings["bike_weight_kg"])
        s.ids.rider_height.text = str(self._settings["rider_height_cm"])
        s.ids.rider_age.text    = str(self._settings["rider_age"])
        s.ids.crr.text          = str(self._settings["crr"])
        s.ids.cda.text          = str(self._settings["cda"])
        s.ids.epoc.text         = str(self._settings["epoc_factor"])
        s.ids.ele_smooth.text   = str(self._settings["ele_smooth"])
        s.ids.ele_max.text      = str(self._settings["ele_max_m"])
        if self._sex_buttons is not None:
            if isinstance(self._sex_buttons, dict):
                self._sex_buttons["male"].active = self._settings["rider_male"]
                self._sex_buttons["female"].active = not self._settings["rider_male"]
            else:
                for it in self._sex_buttons.items:
                    if "male" in it.text.lower():
                        it.active = self._settings["rider_male"]
                    elif "female" in it.text.lower():
                        it.active = not self._settings["rider_male"]
        analyzer.apply_settings(self._settings)
        self._refresh_bmr_preview()

    def _refresh_bmr_preview(self):
        s = self._sm.get_screen("settings")
        w = self._settings["rider_weight_kg"]
        h = self._settings["rider_height_cm"]
        a = self._settings["rider_age"]
        m = self._settings["rider_male"]
        bmr = 10*w + 6.25*h - 5*a + (5 if m else -161)
        sex_str = "male" if m else "female"
        s.ids.bmr_preview.text = (f"Current BMR: {bmr:.0f} kcal/day "
                                  f"({w} kg, {h} cm, {a} y, {sex_str})")

    # -- helpers --

    def _show_message(self, text):
        try:
            Snackbar(text=text, duration=2.0).open()
        except Exception:
            print(text)


if __name__ == "__main__":
    RideAnalyzerApp().run()
