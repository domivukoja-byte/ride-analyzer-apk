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
# Pin python3 to 3.11.4: p4a's current default is 3.14.2, but Kivy
# 2.3.0's Cython-generated C uses Python 3.11 internal APIs
# (_PyLong_AsByteArray with 5 args, _PyInterpreterState_GetConfig,
# _PyUnicode_FastCopyCharacters) that changed signature in 3.12+ and
# were removed in 3.14. Building Kivy against 3.14.2 fails with
# "too few arguments to function call" errors. 3.11.4 works.
# Note: p4a downloads cpython from
#   https://github.com/python/cpython/archive/refs/tags/v3.11.4.tar.gz
# which we pre-seed in the workflow.
requirements = python3, kivy==2.3.0, kivymd==1.2.0, pillow, androidstorage4kivy, urllib3, certifi

# (str) Presplash file
presplash.filename = %(source.dir)s/assets/presplash.jpg

# (str) Icon
icon.filename = %(source.dir)s/assets/icon.png

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum Android API supported
# Set to 21 (Android 5.0) to match android.ndk_api = 21 and the prebuilt
# rideanalyzer distribution's "min API 21". Buildozer 1.5.0 refuses to
# package the APK when --minsdk differs from the api the recipes were
# compiled against unless --allow-minsdk-ndkapi-mismatch is passed; using
# 21 here keeps everything aligned without that flag. Android 5.0+ covers
# 99.5%+ of active devices and includes all the scoped-storage / runtime-
# permission APIs we need.
android.minapi = 21

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
