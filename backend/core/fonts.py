"""
Bundled font paths for PDF generation.

xhtml2pdf's default fonts (Helvetica/Times/Courier — the standard 14 PDF
fonts) don't include a glyph for the peso sign (₱, U+20B1), so any amount
containing it renders as a missing-glyph box. DejaVu Sans does include it —
bundled here as an actual file (not relying on a system font) so this works
identically on any machine, including Windows dev environments where the
Linux system font path this was originally verified against won't exist.
"""
import os
from pathlib import Path

_FONTS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "static" / "fonts"

# .as_posix() — CSS url() wants forward slashes even on Windows; a raw
# Windows path with backslashes would be misinterpreted as escape sequences.
DEJAVU_SANS_REGULAR = (_FONTS_DIR / "DejaVuSans.ttf").as_posix()
DEJAVU_SANS_BOLD = (_FONTS_DIR / "DejaVuSans-Bold.ttf").as_posix()