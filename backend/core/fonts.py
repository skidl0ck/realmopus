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

# .as_posix() — a bare absolute path with forward slashes, understood
# correctly by xhtml2pdf's font loader on every platform (confirmed by
# direct testing — a file:// URI is parsed but never actually loads the
# font, silently falling back to a font with no peso-sign glyph). The
# Windows-specific crash this used to trigger wasn't actually caused by the
# path format at all — it's a genuine bug in xhtml2pdf's own temp-file
# handling, fixed in core/xhtml2pdf_patches.py instead.
DEJAVU_SANS_REGULAR = (_FONTS_DIR / "DejaVuSans.ttf").as_posix()
DEJAVU_SANS_BOLD = (_FONTS_DIR / "DejaVuSans-Bold.ttf").as_posix()