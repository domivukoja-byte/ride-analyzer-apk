"""Local override of p4a's python3 recipe.

The stock python3 recipe is for 3.14.2 and has patches tuned to that
version. When we pin python3==3.11.4 in buildozer.spec, the stock
recipe is used but the patches subdirectory includes
`cpython-311-ctypes-find-library.patch` (3.11+ only) and
`3.14_*.patch` files (3.14 only) that don't apply correctly.

The actual blocker for 3.11.4 is that Android NDK r28c's clang turns
`-Wimplicit-function-declaration` into a hard error, and Python
3.11.4's grpmodule.c calls setgrent/getgrent/endgrent without
declaring them. Android's <grp.h> doesn't declare them. Result:

    python3/Modules/grpmodule.c:275:5: error: call to undeclared
    function 'setgrent'; ISO C99 and later do not support implicit
    function declarations [-Wimplicit-function-declaration]

We override the recipe to:
  1. Pin version='3.11.4' so it matches the buildozer.spec pin.
  2. Use a custom patches_dir (this dir's 'patches/' subdir) that
     includes the stock p4a 3.11+ patch PLUS our grpmodule-decl.patch
     that adds the missing function declarations.
"""
import os
from pythonforandroid.recipes.python3 import Python3Recipe

_HERE = os.path.dirname(os.path.abspath(__file__))


class Python3Recipe_3_11_4(Python3Recipe):
    version = '3.11.4'
    url = 'https://github.com/python/cpython/archive/refs/tags/v3.11.4.tar.gz'
    # Use our local patches dir. The parent class's patches_dir points
    # inside p4a's installed source, which is read-only and contains
    # patches for the stock 3.14.2 version. Our override reuses only
    # the patches valid for 3.11.x.
    patches_dir = os.path.join(_HERE, 'patches')


recipe = Python3Recipe_3_11_4()
