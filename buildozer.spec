[app]
# (str) Title of your application
title = Ride Analyzer

# (str) Package name
package.name = rideanalyzer

# (str) Package domain (needed for android/ios packaging)
package.domain = org.dominik

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,jfif,kv,atlas,json,txt

# Build only the arm64 architecture (all phones from 2017+). Cuts build
# time roughly in half vs. building both arm64 and armv7. If you ever need
# to support a 32-bit-only device, add "armeabi-v7a" here.
android.archs = arm64-v8a

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# Kivy 2.3.0 + KivyMD 1.2.0 work together; androidstorage4kivy is the
# SAF folder picker; pillow for the icon/presplash work; urllib3 + certifi
# so Nominatim HTTPS calls don't fail with SSL errors on Android.
# 3.11.4 instead of 3.11.6 because python.org's 3.11.6 tarball URL has
# been returning HTTP 502 to GitHub's IP for weeks (kivy/python-for-android
# issue #2640). 3.11.4 is the most-recent p4a-tested patch in 2026.
requirements = python3==3.11.4, kivy==2.3.0, kivymd==1.2.0, pillow, androidstorage4kivy, urllib3, certifi

# (str) Presplash file
presplash.filename = %(source.dir)s/assets/presplash.jpg

# (str) Icon
icon.filename = %(source.dir)s/assets/icon.png

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum Android API supported
android.minapi = 24

# (int) Android NDK API
android.ndk_api = 21

# (bool) Use --private data storage with Android 10+ Scoped Storage
android.private = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
# android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
# android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
# android.ant_path =

# (bool) If True, then skip trying to update the Android dependencies
# (useful for offline / docker builds). Not honored in p4a>=2023 - we pin
# the toolchain via the requirements above.
# android.skip_update = False

# (str) Android entry point
android.entry_point = org.kivy.android.PythonActivity

# (list) Patterns to black-list from the package
blacklist = doc/, tests/, .github/, README.md, .gitignore, *.pyc, __pycache__/, push_to_github.py

# (bool) Whitelist for forcing the orientation
orientation = portrait

# Local p4a recipe overrides (see p4a_recipes/).
# freetype is overridden to use the working download-mirror.savannah.gnu.org
# host because the primary savannah host returns 502 to GitHub runner IPs.
p4a.local_recipes = %(source.dir)s/p4a_recipes

# (str) App's launch screen orientation
# (auto / landscape / portrait)
# launch_screen.orientation = portrait

# (bool) If True, the application will be fullscreen
# fullscreen = 0

# (list) Status bar to be hidden (on Android only)
# status.bar = none

# (str) Supported orientation (one value or a list of them separated by comma)
# supported_orientations = landscape, portrait

# (bool) Indicate if this is a debug build
# android.debug = True

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if the available app dependencies' versions are outdated
warn_on_tools_upgrade = True

# (str) Path to build artifact storage (absolute path or relative to working dir)
# build_dir = ./.buildozer

# (int) Don't open the android emulator/device after build
# android.emulator = 0
