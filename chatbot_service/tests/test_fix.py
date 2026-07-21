# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import os
import sys
import tempfile
from pathlib import Path


class TestFixScript:
    def _run_fix_in(self, tmpdir: Path, filename: str, content: str) -> str:
        tests_dir = tmpdir / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / filename
        test_file.write_text(content)

        old_cwd = Path.cwd()
        os.chdir(tmpdir)
        try:
            exec((Path(__file__).parent.parent / "fix.py").read_text())
        except SystemExit:
            pass
        finally:
            os.chdir(old_cwd)

        return test_file.read_text()

    def test_fix_script_adds_async_to_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._run_fix_in(
                Path(tmpdir), "test_example.py",
                "class Tool:\n"
                "    def search(self, message):\n"
                "        return []\n"
            )
            assert "async def search(self, message):" in content

    def test_fix_script_async_with_type_hint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._run_fix_in(
                Path(tmpdir), "test_example2.py",
                "class Tool:\n"
                "    def search(self, message: str) -> list:\n"
                "        return []\n"
            )
            assert "async def search(self, message: str) -> list:" in content

    def test_fix_script_skips_unmatched(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._run_fix_in(
                Path(tmpdir), "test_example3.py",
                "class Tool:\n"
                "    def lookup(self, query):\n"
                "        return []\n"
            )
            assert "def lookup(self, query):" in content
            assert "async" not in content
