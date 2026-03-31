"""PyInstaller hook for Tree-sitter language grammars.

This hook ensures that the native libraries for common Tree-sitter language
bindings are bundled when using the ``tree_sitter_languages`` helper
package, so that ``get_parser()`` continues to work inside a one-file EXE.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

TREE_SITTER_LANGUAGES = [
    "tree_sitter_c",
    "tree_sitter_cpp",
    "tree_sitter_go",
    "tree_sitter_java",
    "tree_sitter_javascript",
    "tree_sitter_kotlin",
    "tree_sitter_python",
    "tree_sitter_ruby",
    "tree_sitter_rust",
    "tree_sitter_typescript",
]

binaries = []
datas = []
hiddenimports = list(TREE_SITTER_LANGUAGES)

for lang in TREE_SITTER_LANGUAGES:
    try:
        binaries.extend(collect_dynamic_libs(lang))
    except Exception:
        # If a particular grammar is not installed in the build environment,
        # we simply skip it.
        continue
