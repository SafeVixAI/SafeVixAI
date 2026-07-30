# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
#!/usr/bin/env python3
"""Batch upgrade AST stubs to LLM docs with email alerts on failure.
Usage: python scripts/batch_upgrade_wiki.py [--limit N] [--delay SECS]
"""
import json
import os
import re
import smtplib
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent.parent
WIKI_CONTENT = ROOT / "docs" / "wiki" / "content"

# ── Email Alert ─────────────────────────────────────────────────────────────
def send_alert_email(subject, error_details, file_name, provider_errors):
    """Send email alert when wiki generation fails persistently."""
    smtp_user = os.environ.get("ALERT_EMAIL", "")
    smtp_pass = os.environ.get("ALERT_EMAIL_PASSWORD", "")
    alert_to = os.environ.get("ALERT_EMAIL_TO", smtp_user)

    if not smtp_user or not smtp_pass:
        print("  [ALERT] No email configured (set ALERT_EMAIL + ALERT_EMAIL_PASSWORD)")
        print(f"  [ALERT] Issue: {subject}")
        print(f"  [ALERT] Details: {error_details}")
        _print_solutions(provider_errors)
        return

    body = f"""SafeVixAI Wiki Manager — Alert

ISSUE: {subject}
FILE: {file_name}
TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}

DETAILS:
{error_details}

PROVIDER ERRORS:
{chr(10).join(f'  - {p}: {e}' for p, e in provider_errors.items())}

3 WAYS TO FIX THIS:

1. RATE LIMIT EXHAUSTED
   → Wait 1 hour and re-run: python scripts/batch_upgrade_wiki.py --limit 20 --delay 5
   → Or switch to a different provider by updating OPENROUTER_API_KEY or MISTRAL_API_KEY

2. API KEY EXPIRED/INVALID
   → Check your keys at: https://openrouter.ai/keys | https://console.mistral.ai/api-keys
   → Update chatbot_service/.env with fresh keys
   → Add keys as GitHub Secrets for CI: Settings → Secrets → OPENROUTER_API_KEY

3. SERVICE OUTAGE
   → Check status: https://status.openrouter.ai | https://status.mistral.ai
   → The {len(provider_errors)} failed files will stay as AST stubs (still functional)
   → Re-run later: python scripts/wiki_manager.py update
"""
    msg = MIMEText(body)
    msg["Subject"] = f"[SafeVixAI] {subject}"
    msg["From"] = smtp_user
    msg["To"] = alert_to

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        print(f"  [ALERT] Email sent to {alert_to}")
    except Exception as e:
        print(f"  [ALERT] Email failed: {e}")
        _print_solutions(provider_errors)

def _print_solutions(provider_errors):
    print("\n  === 3 WAYS TO FIX ===")
    print("  1. Rate limit → wait 1hr, re-run with --delay 5")
    print("  2. Key expired → refresh at openrouter.ai/keys or console.mistral.ai")
    print("  3. Service down → check status pages, re-run later")
    print()

# ── LLM Calls ───────────────────────────────────────────────────────────────
def call_llm(prompt, or_key, ms_key, gk_key):
    """Try OpenRouter → Mistral → Gemini with per-provider error tracking."""
    errors = {}
    providers = [
        ("openrouter", or_key, "https://openrouter.ai/api/v1/chat/completions",
         {"model": "google/gemini-2.0-flash-lite-001", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.3}),
        ("mistral", ms_key, "https://api.mistral.ai/v1/chat/completions",
         {"model": "mistral-small-latest", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.3}),
    ]
    for name, key, url, payload in providers:
        if not key:
            continue
        for attempt in range(2):  # 2 retries per provider
            try:
                body = json.dumps(payload).encode("utf-8")
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
                req = Request(url, data=body, headers=headers)
                resp = urlopen(req, timeout=60)
                data = json.loads(resp.read().decode("utf-8"))
                result = data["choices"][0]["message"]["content"]
                if result and len(result) > 100:
                    if len(result) > 8000:
                        result = result[:8000].rsplit("\n", 1)[0] + "\n"
                    return result, name, errors
            except HTTPError as e:
                errors[name] = f"HTTP {e.code} (attempt {attempt+1})"
                if e.code == 429:
                    time.sleep((attempt + 1) * 5)
                else:
                    break
            except Exception as e:
                errors[name] = str(e)
                break

    # Try Gemini direct as last resort
    if gk_key:
        try:
            gurl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={gk_key}"
            body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 4096, "temperature": 0.3}}).encode()
            req = Request(gurl, data=body, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=60)
            data = json.loads(resp.read().decode("utf-8"))
            result = data["candidates"][0]["content"]["parts"][0]["text"]
            if result and len(result) > 100:
                if len(result) > 8000:
                    result = result[:8000].rsplit("\n", 1)[0] + "\n"
                return result, "gemini", errors
        except HTTPError as e:
            errors["gemini"] = f"HTTP {e.code}"
        except Exception as e:
            errors["gemini"] = str(e)

    return None, None, errors

# ── Prompt ──────────────────────────────────────────────────────────────────
def build_prompt(name, ext, section, path, code):
    return f"""Technical documentation writer for SafeVixAI (AI road safety platform, IIT Madras Hackathon 2026).

Generate a comprehensive wiki page in Markdown for this module.

Module: `{name}{ext}` | Section: {section} | File: `{path}`
Platform: 9 LLM providers, Supabase Auth, Next.js, FastAPI, LocalHashEmbeddingFunction (SHA-256)

```{ext.lstrip('.')}
{code}
```

Generate these sections:
1. # Title
2. ## Overview (what it does, 2-3 sentences)
3. ## Architecture (where it fits)
4. ## Key Classes/Functions (table: name | params | return | description)
5. ## Dependencies (imports)
6. ## Configuration (env vars, constants)
7. ## Usage Examples (real code)
8. ## Error Handling
9. ## Related Modules

Rules: Use actual names from code. No TODOs. Be specific. Output ONLY markdown."""

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    limit = 127
    delay = 3
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--limit" and i + 1 < len(args): limit = int(args[i+1])
        if arg == "--delay" and i + 1 < len(args): delay = int(args[i+1])

    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    ms_key = os.environ.get("MISTRAL_API_KEY", "")
    gk_key = os.environ.get("GOOGLE_API_KEY", "")

    if not or_key and not ms_key and not gk_key:
        print("ERROR: No LLM API keys found")
        sys.exit(1)

    active = [n for n, k in [("OpenRouter", or_key), ("Mistral", ms_key), ("Gemini", gk_key)] if k]
    print(f"Providers: {' → '.join(active)}", flush=True)

    # Find stubs
    stubs = []
    for f in sorted(WIKI_CONTENT.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        if "Auto-generated:" not in text:
            continue
        src_match = re.search(r'Source: `(.+?)`', text)
        if not src_match:
            continue
        spath = src_match.group(1).replace("\\", "/")
        if (ROOT / spath).exists():
            stubs.append((f, spath))

    total = min(len(stubs), limit)
    print(f"Stubs: {len(stubs)} found, processing {total} (delay: {delay}s)", flush=True)
    print("=" * 50, flush=True)

    success, fail, consecutive_fails = 0, 0, 0
    all_errors = {}

    for i, (wiki_path, spath) in enumerate(stubs[:total]):
        ext = "." + spath.rsplit(".", 1)[-1]
        name = spath.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        section = str(wiki_path.parent.relative_to(WIKI_CONTENT))

        try:
            src = (ROOT / spath).read_text(encoding="utf-8", errors="ignore")
            lines = src.split("\n")
            if len(lines) > 150:
                src = "\n".join(lines[:150]) + f"\n# ... ({len(lines)} total lines)"
        except Exception:
            print(f"[{i+1}/{total}] SKIP {name} (unreadable)", flush=True)
            continue

        print(f"[{i+1}/{total}] {name}{ext} ...", end=" ", flush=True)

        prompt = build_prompt(name, ext, section, spath, src)
        result, provider, errors = call_llm(prompt, or_key, ms_key, gk_key)

        if result:
            wiki_path.write_text(result, encoding="utf-8")
            success += 1
            consecutive_fails = 0
            print(f"OK ({len(result)} chars via {provider})", flush=True)
        else:
            fail += 1
            consecutive_fails += 1
            all_errors[name] = errors
            print(f"FAILED {errors}", flush=True)

            if consecutive_fails >= 5:
                print("\n5 consecutive failures — stopping early.", flush=True)
                send_alert_email(
                    "Wiki generation stopped — 5 consecutive LLM failures",
                    f"Failed at file #{i+1}: {name}{ext}\n{success} succeeded before failure.",
                    name + ext, errors
                )
                break

        time.sleep(delay)

    print("=" * 50, flush=True)
    remaining = len(stubs) - success - fail
    print(f"Results: {success} upgraded | {fail} failed | {remaining} remaining", flush=True)

    if fail > 0 and consecutive_fails < 5:
        send_alert_email(
            f"Wiki generation completed with {fail} failures",
            f"{success} upgraded, {fail} failed out of {total} attempted.",
            "multiple files", all_errors.get(list(all_errors.keys())[-1], {}) if all_errors else {}
        )

    # Clean up test script if it exists
    test_script = ROOT / "scripts" / "test_llm.py"
    if test_script.exists():
        test_script.unlink()

if __name__ == "__main__":
    main()
