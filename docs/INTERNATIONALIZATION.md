# Internationalization Guide

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [Features.md](./Features.md), [SDK_GUIDE.md](./SDK_GUIDE.md)

---

## Supported Languages

SafeVixAI supports 14 Indian languages with a 4-code mapping system:

| # | Language | UI Code | Recognition Code | Speech Target Code | Synthesis Code |
|---|----------|---------|-----------------|-------------------|----------------|
| 1 | English | `en` | `en-IN` | `en` | `en-IN` |
| 2 | Hindi | `hi` | `hi-IN` | `hi` | `hi-IN` |
| 3 | Tamil | `ta` | `ta-IN` | `ta` | `ta-IN` |
| 4 | Telugu | `te` | `te-IN` | `te` | `te-IN` |
| 5 | Bengali | `bn` | `bn-IN` | `bn` | `bn-IN` |
| 6 | Marathi | `mr` | `mr-IN` | `mr` | `mr-IN` |
| 7 | Gujarati | `gu` | `gu-IN` | `gu` | `gu-IN` |
| 8 | Kannada | `kn` | `kn-IN` | `kn` | `kn-IN` |
| 9 | Malayalam | `ml` | `ml-IN` | `ml` | `ml-IN` |
| 10 | Punjabi | `pa` | `pa-IN` | `pa` | `pa-IN` |
| 11 | Odia | `or` | `or-IN` | `or` | `or-IN` |
| 12 | Assamese | `as` | `as-IN` | `as` | `as-IN` |
| 13 | Urdu | `ur` | `ur-IN` | `ur` | `ur-IN` |
| 14 | Sanskrit | `sa` | — | `sa` | — |

**Definition:** `frontend/lib/languages.ts`

---

## Architecture

The language system has four layers:

1. **UI Code** (`en`) — Used for i18next translations, displayed in language selector
2. **Recognition Code** (`en-IN`) — Passed to Web Speech API for speech-to-text
3. **Speech Target Code** (`en`) — Passed to the backend `/speech/translate` endpoint
4. **Synthesis Code** (`en-IN`) — Passed to `speechSynthesis` for text-to-speech

---

## Chatbot Language Detection

The chatbot auto-detects the input language via Unicode script ranges in `providers/lang_detection.py`:

```python
# Detection is regex-based — no NLTK needed
LANG_RANGES = {
    "hi": range(0x0900, 0x097F),    # Devanagari
    "ta": range(0x0B80, 0x0BFF),    # Tamil
    "te": range(0x0C00, 0x0C7F),    # Telugu
    "bn": range(0x0980, 0x09FF),    # Bengali
    # ... 14 languages total
}
```

**Routing:**
- Indian language input → **Sarvam-30B** (Indic specialist)
- Legal/challan + Indian language → **Sarvam-105B** (higher accuracy for law)
- English → Default provider (typically Groq)

---

## Speech Translation Pipeline

The `/speech/translate` endpoint handles ASR + translation + TTS:

```
Audio Input → ASR (IndicSeamlessService) → Translation → TTS → Audio Output
```

**Implementation:** `chatbot_service/services/speech_translation.py`

---

## Adding a New Language

1. Add the language entry in `frontend/lib/languages.ts`
2. Add translation files in `frontend/public/locales/{code}/`
3. Add Unicode range detection in `chatbot_service/providers/lang_detection.py`
4. Verify ASR/TTS support for the language
5. Add test coverage in the respective test files

### Translation File Structure
```
frontend/public/locales/
├── en/
│   ├── common.json
│   ├── sos.json
│   ├── challan.json
│   └── ...
├── hi/
│   ├── common.json
│   └── ...
└── ta/
    ├── common.json
    └── ...
```

---

## RTL Language Support

Currently, no RTL languages are in the supported set. If adding Urdu (which uses a RTL script):
- Ensure CSS handles `direction: rtl`
- Test all components with RTL layout
- Update Tailwind configuration if needed

---

## Testing I18n

```typescript
// Frontend test pattern
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { defaultValue?: string }) =>
      typeof options?.defaultValue === 'string'
        ? options.defaultValue
        : key,
    i18n: { language: 'en' },
  }),
}));
```

---

## Contributing Translations

1. Fork the repository
2. Add or update translation files in `frontend/public/locales/{code}/`
3. Add language entry in `frontend/lib/languages.ts`
4. Test with a language selector
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution workflow.
