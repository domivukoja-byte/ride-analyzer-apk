"""Local override of p4a's hostpython3 recipe.

p4a's default hostpython3 version is 3.14.2 (or whatever the develop
branch tracks), but Kivy 2.3.0's Cython-generated C uses Python 3.11
internal APIs that changed signature in 3.12+ and were removed in
3.14. Building Kivy against 3.14.2 fails with errors like:

    error: too few arguments to function call, expected 6, have 5
        _PyLong_AsByteArray(...)
    error: call to undeclared function '_PyInterpreterState_GetConfig'
    error: call to undeclared function '_PyUnicode_FastCopyCharacters'

We pin BOTH python3 and hostpython3 to 3.11.4 (the highest 3.11 patch
that p4a has stable Android patches for). The hostpython3.download()
guard refuses to build if the two versions differ, so we must
explicitly match it.

The parent class's `url` is computed at class-definition time from the
parent's hardcoded `version = "3.14.2"`, so it does NOT auto-update
when we override `version`. We override `url` explicitly here too.

3.11.4 is downloaded from
    https://github.com/python/cpython/archive/refs/tags/v3.11.4.tar.gz
which is pre-seeded in the workflow.
"""
from pythonforandroid.recipes.hostpython3 import HostPython3Recipe


class HostPython3Recipe_3_11_4(HostPython3Recipe):
    version = '3.11.4'
    # Parent's `url` is a class-level f-string computed once at import
    # time, so we must redeclare it with the matching version.
    url = 'https://github.com/python/cpython/archive/refs/tags/v3.11.4.tar.gz'


recipe = HostPython3Recipe_3_11_4()
