"""
Workaround for a known, currently-unfixed xhtml2pdf bug on Windows:
https://github.com/xhtml2pdf/xhtml2pdf/issues/623

xhtml2pdf's font loading (used for the DejaVu Sans peso-sign fix — see
core/fonts.py) always copies the font file into a tempfile.NamedTemporaryFile
before handing it to reportlab, even for a plain local file path. That temp
file is never closed before reportlab tries to open it a second time — fine
on Linux/Mac (multiple open handles to one file are allowed), but Windows
raises PermissionError: [WinError 5] Access is denied the moment a second
handle tries to open a file that's still held open elsewhere. This isn't
something a font path format can work around — it's a bug in xhtml2pdf's own
temp-file handling, confirmed against xhtml2pdf's actual source and an
open GitHub issue with the identical traceback.

The fix (the same one used elsewhere for this exact class of bug): create
the temp file with delete=False and close it immediately after writing, so
the file still exists on disk but isn't held open — a second open() then
succeeds on every platform. Since delete=False means closing no longer
auto-deletes it, cleanup is handled explicitly too, so temp files don't
quietly accumulate.
"""
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

_patched = False


def apply():
    global _patched
    if _patched:
        return
    _patched = True

    try:
        from xhtml2pdf import files as xhtml2pdf_files
    except ImportError:
        return

    def _windows_safe_get_named_tmp_file(self):
        data = self.get_data()
        tmp_file = tempfile.NamedTemporaryFile(suffix=self.suffix, delete=False)
        if data:
            tmp_file.write(data)
            tmp_file.flush()
        tmp_file.close()  # closed but NOT deleted (delete=False) — a second
        # open() elsewhere (reportlab, on the very next line in xhtml2pdf's
        # own loadFont()) now succeeds on Windows too.
        xhtml2pdf_files.files_tmp.append(tmp_file)
        if self.path is None:
            self.path = tmp_file.name
        return tmp_file

    def _clean_files(self):
        for f in self.files:
            try:
                f.close()  # already closed above; harmless if called again
            except Exception:
                pass
            try:
                os.unlink(f.name)
            except OSError:
                pass  # already gone, or still briefly locked — not worth failing a PDF render over
        self.files.clear()

    xhtml2pdf_files.BaseFile.get_named_tmp_file = _windows_safe_get_named_tmp_file
    xhtml2pdf_files.TmpFiles.cleanFiles = _clean_files
    logger.info("Applied Windows-safe xhtml2pdf temp-file patch (see core/xhtml2pdf_patches.py).")