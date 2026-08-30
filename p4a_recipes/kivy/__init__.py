"""Local override of p4a's kivy recipe.

Injects a multi-file patch that fixes the glShaderSource pointer type to
match Android NDK r28c's GLES2 header across the whole kivy graphics
backend.

Background: Kivy 2.3.0 declares glShaderSource as `const GLchar**` in
five places:

  - kivy/graphics/cgl.pxd                       (ctypedef + struct field)
  - kivy/graphics/cgl_backend/cgl_gl.pyx       (cdef extern in cgl_gl.c)
  - kivy/graphics/cgl_backend/cgl_debug.pyx    (dbgShaderSource + gil_dbgShaderSource)
  - kivy/graphics/cgl_backend/cgl_mock.pyx     (mockShaderSource)
  - kivy/include/common_subset.h               (declaration in mock-only header)

NDK r28c's <GLES2/gl2.h> declares glShaderSource as
`const GLchar *const *` (pointer to const-pointer-to-const-char).
clang 19+ (used by NDK r28c) promotes
-Wincompatible-function-pointer-types to a hard error, so the slot
assignment in Cython-generated cgl_gl.c fails with:

    cgl_gl.c:4382:52: error: incompatible function pointer types
      assigning to 'void (*)(..., const GLchar **, ...)'
      from 'void (..., const GLchar *const *, ...)'

Patching only cgl_gl.pyx (the cdef extern that drives the RHS of the
assignment) is not enough: the LHS of the assignment comes from the
GLES2_Context struct in cgl.pxd, which still carries the old type. We
patch all five files to match the upstream kivy fix in commit 506bbb8
("Revert #8415 and align glShaderSource typedef in common_subset.h
with Khronos Headers (#8911)"). With this in place, both sides of the
C-level assignment use `const GLchar *const *` and clang is happy.

The cgl_debug.pyx and cgl_mock.pyx changes are also required for
type-consistency (their cdef functions are referenced from the
cdef-extern declarations), even though on Android we only link cgl_gl.

Applied as a single p4a patch via self.patches so p4a invokes its
standard apply_patch which joins 'patches/cgl_gl_glShaderSource.patch'
to self.get_recipe_dir() — which returns our local override dir when
p4a.local_recipes is set in buildozer.spec.
"""
from pythonforandroid.recipes.kivy import KivyRecipe


class KivyRecipe_local(KivyRecipe):
    # Inherit everything from the parent recipe (version, url, env setup,
    # build_arch flow, etc.). We only change the patch list.

    def apply_patches(self, arch, build_dir=None):
        # Add our glShaderSource const-fix before the parent's patches run.
        if 'patches/cgl_gl_glShaderSource.patch' not in self.patches:
            self.patches.append('patches/cgl_gl_glShaderSource.patch')
        super().apply_patches(arch, build_dir=build_dir)


recipe = KivyRecipe_local()
