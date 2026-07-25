# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import json

transcript_path = r"C:\Users\Dell\.gemini\antigravity\brain\23643f0f-aff8-44f9-b2c6-d6c31d24d827\.system_generated\logs\transcript_full.jsonl"
files_to_recover = [
    "test_enterprise_circuit_breaker.py",
    "test_episodic_memory.py",
    "test_ragas.py",
    "test_router_idempotency.py"
]

with open(transcript_path, encoding='utf-8') as f:
    for raw_line in f:
        for filename in files_to_recover:
            if filename in raw_line:
                try:
                    data = json.loads(raw_line)
                    if data.get('type') == 'PLANNER_RESPONSE':
                        tool_calls = data.get('tool_calls', [])
                        for call in tool_calls:
                            if call.get('name') == 'write_to_file':
                                args = call.get('arguments', {})
                                target = args.get('TargetFile', '')
                                for fname in files_to_recover:
                                    if fname in target:
                                        with open(f"recovered_{fname}", 'w', encoding='utf-8') as out:
                                            out.write(args.get('CodeContent', ''))
                except Exception:
                    pass
                break
