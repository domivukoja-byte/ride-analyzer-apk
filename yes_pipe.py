"""Y-stdin source for buildozer's license auto-accept.

Buildozer invokes `sdkmanager` to install Android SDK components.
Sdkmanager prints "Accept? (y/N):" for each license and waits for
input on stdin. Buildozer does not forward this to the user; the
caller must pre-accept.

This script writes an unending stream of "y\n" to stdout. It
ignores SIGPIPE so it does not die with a non-zero exit code
when buildozer closes stdin. The caller pipes it into buildozer:
    python -u yes_pipe.py | buildozer -v android debug ...
"""
import signal
import sys

signal.signal(signal.SIGPIPE, signal.SIG_IGN)

# Unbuffered (PYTHONUNBUFFERED also works) so the consumer gets
# each y promptly rather than waiting for a full block.
sys.stdout.reconfigure(line_buffering=True)
while True:
    sys.stdout.write("y\n")
