"""Build-script validation that must fail before an archive is written."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_build():
    spec = importlib.util.spec_from_file_location("build_apworld", ROOT / "tools" / "_build_apworld.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildValidationTests(unittest.TestCase):
    def test_syntax_error_reports_file_and_line_without_writing_archive(self):
        build = load_build()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            bad = folder / "Broken.py"
            bad.write_text("def broken(:\n    pass\n", encoding="utf-8")
            archive = folder / "valheimapworld.apworld"
            with self.assertRaises(SystemExit) as caught:
                build.parse_python(bad)
            message = str(caught.exception)
            self.assertIn("Broken.py", message)
            self.assertIn(":1:", message)
            self.assertFalse(archive.exists())

    def test_valid_world_sources_parse(self):
        build = load_build()
        sources = [path for path in (ROOT / "valheimapworld").rglob("*.py")]
        build.validate_python_sources(sources)


if __name__ == "__main__":
    unittest.main()
