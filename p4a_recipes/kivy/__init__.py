"""Local override of p4a's kivy recipe.

Injects a small patch to kivy/graphics/cgl_backend/cgl_gl.pyx that fixes
the glShaderSource pointer type to match Android NDK r28c's GLES2 header.

Background: Kivy 2.3.0's cgl_gl.pyx declares the local glShaderSource
function pointer as `const GLchar**` (pointer to pointer-to-const-char).
NDK r28c's <GLES2/gl2.h> declares glShaderSource as
`const GLchar *const *` (pointer to const-pointer-to-const-char). The
slot assignment in Cython-generated cgl_gl.c (line 4382) triggers
clang's -Wincompatible-function-pointer-types which the NDK r28c
toolchain promotes to a hard error. The patch changes the Cython-side
declaration to match the NDK header, making the C-level assignment
type-compatible.

Applied as a p4a patch via self.patches so p4a invokes its standard
apply_patch which joins 'patches/cgl_gl_glShaderSource.patch' to
self.get_recipe_dir() — which returns our local override dir when
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
