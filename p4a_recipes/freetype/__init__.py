"""Local override of p4a's freetype recipe.

Savannah's main download host (download.savannah.gnu.org) returns HTTP 502
to GitHub Actions runner IPs, making every build fail at the freetype
download step. The official `download-mirror.savannah.gnu.org` host is
the recommended fallback (per the matplotlib issue #31340 thread and
Savannah's own status page) and reliably serves the same file.

This recipe subclasses the original to swap only the `url`, leaving
version, md5sum, build commands, etc. intact.
"""
from pythonforandroid.recipes.freetype import FreetypeRecipe


class FreetypeRecipeMirror(FreetypeRecipe):
    url = 'https://download-mirror.savannah.gnu.org/releases/freetype/freetype-2.14.1.tar.gz'


recipe = FreetypeRecipeMirror()
