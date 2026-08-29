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
  2. Override apply_patches() so the parent's version-conditional
     patches still get registered, AND our grpmodule-decl.patch is
     added to the list before p4a iterates and applies them.

p4a's base Recipe.apply_patch joins each entry in self.patches to
self.get_recipe_dir(). When p4a.local_recipes is set in
buildozer.spec, get_recipe_dir() returns the local override dir,
so 'patches/grpmodule-decl.patch' resolves to our local
p4a_recipes/python3/patches/grpmodule-decl.patch automatically —
no separate patches_dir wiring needed.
"""
import os
from pythonforandroid.recipes.python3 import Python3Recipe

_HERE = os.path.dirname(os.path.abspath(__file__))


class Python3Recipe_3_11_4(Python3Recipe):
    version = '3.11.4'
    url = 'https://github.com/python/cpython/archive/refs/tags/v3.11.4.tar.gz'

    def apply_patches(self, arch, build_dir=None):
        # Append our fix BEFORE the parent iterates self.patches.
        # The parent will add the stock version-conditional entries
        # (pyconfig_detection, reproducible-buildinfo,
        # cpython-311-ctypes-find-library, etc.) at the start of
        # its own apply_patches; we want our entry to ride along in
        # the same iteration loop.
        if 'patches/grpmodule-decl.patch' not in self.patches:
            self.patches.append('patches/grpmodule-decl.patch')
        super().apply_patches(arch, build_dir=build_dir)


recipe = Python3Recipe_3_11_4()
