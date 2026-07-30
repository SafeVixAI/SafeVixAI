# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import json
import os
import re
import time
import urllib.parse
import urllib.request

LOCALES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../i18n/locales'))
TARGET_LANGS = ['ar', 'es', 'fr']
NAMESPACES = ['common', 'auth', 'dashboard', 'challan', 'chat', 'settings', 'errors', 'validation']

# Placeholder regex matching {{param}}
PLACEHOLDER_RE = re.compile(r'\{\{([^}]+)\}\}')

def translate_text(text: str, target_lang: str) -> str:
    if not text.strip():
        return text

    # 1. Protect placeholders (e.g. {{count}} -> __PH_0__)
    placeholders = []
    def replace_ph(match):
        placeholders.append(match.group(0))
        return f" __PH_{len(placeholders) - 1}__ "

    protected_text = PLACEHOLDER_RE.sub(replace_ph, text)

    # 2. Call free Google Translate API via urllib
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": target_lang,
        "dt": "t",
        "q": protected_text
    }

    query_string = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query_string}", headers={'User-Agent': 'Mozilla/5.0'})

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            translated_parts = [part[0] for part in res_data[0] if part[0]]
            translated_text = "".join(translated_parts)
    except Exception as e:
        print(f"  Warning: translation failed for '{text[:20]}...': {e}. Using English fallback.")
        return text

    # 3. Restore placeholders (e.g. __PH_0__ -> {{count}})
    def restore_ph(match):
        try:
            idx = int(match.group(1))
            return placeholders[idx]
        except (IndexError, ValueError):
            return match.group(0)

    restored_text = re.sub(r'__PH_(\d+)__', restore_ph, translated_text).replace("{ {", "{{").replace("} }", "}}")
    return restored_text.strip()

def translate_dict(d, target_lang: str):
    if isinstance(d, dict):
        res = {}
        for k, v in d.items():
            res[k] = translate_dict(v, target_lang)
        return res
    if isinstance(d, str):
        # Prevent translating specific constant names or numeric constants
        if d.isdigit() or d in ['Secure Region', 'Caution Zone', 'High Risk Area']:
            return d
        # Standard safety rule never remove
        if "112" in d and target_lang == 'ar':
            # Preserve immediate safety rules
            translated_arabic = translate_text(d, target_lang)
            if "112" not in translated_arabic:
                translated_arabic = "إتصل بـ 112 فوراً! " + translated_arabic
            return translated_arabic
        return translate_text(d, target_lang)
    return d

def main():
    print("Starting AI Translation Generation Pipeline...")
    en_dir = os.path.join(LOCALES_DIR, 'en')
    if not os.path.exists(en_dir):
        print(f"Error: English locales directory not found: {en_dir}")
        return

    for lang in TARGET_LANGS:
        print(f"\nProcessing target language: {lang.upper()}")
        lang_dir = os.path.join(LOCALES_DIR, lang)
        os.makedirs(lang_dir, exist_ok=True)

        for ns in NAMESPACES:
            en_file = os.path.join(en_dir, f"{ns}.json")
            target_file = os.path.join(lang_dir, f"{ns}.json")

            if not os.path.exists(en_file):
                # Write empty file if English source doesn't exist
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)
                continue

            print(f"  Translating namespace: {ns}")
            with open(en_file, encoding='utf-8') as f:
                en_data = json.load(f)

            translated_data = translate_dict(en_data, lang)

            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, indent=2, ensure_ascii=False)

            # Simple rate limiting protection
            time.sleep(0.5)

    print("\n[SUCCESS] AI Translation generation completed successfully for ar, es, fr!")

if __name__ == "__main__":
    main()
