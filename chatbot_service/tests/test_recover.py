# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import json
import os
import tempfile
from pathlib import Path


class TestRecoverScript:
    def _run_recover_in(self, tmpdir: Path, transcript_content: str) -> None:
        transcript_path = tmpdir / ".system_generated" / "logs" / "transcript_full.jsonl"
        transcript_path.parent.mkdir(parents=True)
        transcript_path.write_text(transcript_content)

        old_cwd = Path.cwd()
        script_path = Path(__file__).parent.parent / "recover.py"
        script_content = script_path.read_text()
        old_path = (
            r'C:\Users\Dell\.gemini\antigravity\brain\23643f0f-aff8-44f9-b2c6-d6c31d24d827'
            r'\.system_generated\logs\transcript_full.jsonl'
        )
        script_content = script_content.replace(old_path, str(transcript_path))

        # Replace generator expression with list comprehension to avoid exec scope issue
        script_content = script_content.replace(
            "if any(filename in line for filename in files_to_recover):",
            "if any([filename in line for filename in files_to_recover]):"
        )

        os.chdir(tmpdir)
        try:
            exec(script_content)
        finally:
            os.chdir(old_cwd)

    def test_recover_finds_matching_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_recover_in(
                Path(tmpdir),
                json.dumps({
                    "type": "PLANNER_RESPONSE",
                    "step_index": 1,
                    "tool_calls": [{
                        "name": "write_to_file",
                        "arguments": {
                            "TargetFile": "test_ragas.py",
                            "CodeContent": "print('hello')"
                        }
                    }]
                }) + "\n"
            )
            recovered = Path(tmpdir) / "recovered_test_ragas.py"
            assert recovered.exists()
            assert recovered.read_text() == "print('hello')"

    def test_recover_skips_non_matching_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_recover_in(
                Path(tmpdir),
                json.dumps({"type": "OTHER", "data": "no match here"}) + "\n"
            )
            for fname in ["test_enterprise_circuit_breaker.py", "test_episodic_memory.py"]:
                assert not Path(tmpdir, f"recovered_{fname}").exists()
