# Ride Analyzer

A dark-themed Android app for analyzing bike-ride `.gpx` files. The same
math as `final_gpx_pydroid.py` (haversine, per-km chunked calorie model,
Mifflin-St Jeor BMR, EPOC, rolling-mean elevation, merged pause detection)
in a real installable APK.

## How to get the APK

1. Open the repo's **Actions** tab on GitHub.
2. Pick the most recent green "Build APK" run (or click **Run workflow**
   to trigger a fresh one).
3. Scroll to the bottom of the run page to the **Artifacts** section.
4. Download `ride-analyzer-debug-apk.zip`, unzip it.
5. Transfer `bin/*.apk` to your phone (USB, or just open the link in
   Chrome on the phone and download directly).
6. Tap the APK. Android will ask you to allow installs from this source
   (browser/file manager). Accept, install, open.

First build: ~40 min (downloads the NDK + SDK + recipes).
Subsequent builds: ~5 min (cache hit on `.buildozer/`).

## Features

- **Ride list** - all `.gpx` files in the folder you picked, sorted by
  name. Type to filter.
- **Ride detail** - total distance, riding time, elevation gain/loss,
  calorie breakdown (gross / EPOC / BMR / delta-vs-rest), pause list
  with location names, summary diagnostics.
- **Settings** - rider weight / height / age / sex, bike weight,
  rolling resistance (CRR), drag area (CdA), EPOC factor, elevation
  smoothing window, elevation spike cap. Saved to the app's private
  data dir; survives restarts.
- **About** - the calorie model, units, and version.

## Permissions

- `INTERNET` - so the app can hit OpenStreetMap Nominatim for reverse
  geocoding. If offline, place names fall back to coordinates.

## How the build works

- **Kivy** 2.3.0 + **KivyMD** 1.2.0 (Material Design widgets).
- **Buildozer** 1.5.0 + **python-for-android** compiles Python + deps
  into a single Android APK.
- **Cython** 3.0.10 (pinned; 3.1+ segfaults in p4a).
- **GitHub Actions** on `ubuntu-22.04` with OpenJDK 17 does the build
  in the cloud; no Android SDK on your laptop needed.

## Storage

- **On Android 10+** - the app uses the Storage Access Framework
  (`androidstorage4kivy`) so you pick a folder via the system file
  picker. The URI is saved in app prefs and listed on every launch.
- **On Android 7-9** - same code path; if SAF is missing, it falls
  back to `os.listdir` on the granted external storage path.

## Local dev / testing

```bash
pip install kivy==2.3.0 kivymd==1.2.0 pillow
python main.py
```

On desktop you'll be prompted to type a folder path (since SAF is
Android-only). The rest of the UI works the same.
