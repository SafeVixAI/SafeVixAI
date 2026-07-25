# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from providers.router import detect_lang


class TestHindiDetection:
    def test_simple_hindi(self):
        assert detect_lang("नमस्ते") == "hi"

    def test_hindi_sentence(self):
        assert detect_lang("सड़क सुरक्षा बहुत महत्वपूर्ण है") == "hi"

    def test_hindi_with_numbers(self):
        assert detect_lang("धारा 185 का जुर्माना") == "hi"


class TestTamilDetection:
    def test_simple_tamil(self):
        assert detect_lang("வணக்கம்") == "ta"

    def test_tamil_sentence(self):
        assert detect_lang("சாலை பாதுகாப்பு விதிகள் முக்கியம்") == "ta"


class TestTeluguDetection:
    def test_simple_telugu(self):
        assert detect_lang("నమస్కారం") == "te"

    def test_telugu_sentence(self):
        assert detect_lang("రోడ్డు భద్రత ముఖ్యం") == "te"


class TestKannadaDetection:
    def test_simple_kannada(self):
        assert detect_lang("ನಮಸ್ಕಾರ") == "kn"

    def test_kannada_sentence(self):
        assert detect_lang("ರಸ್ತೆ ಸುರಕ್ಷತೆ ಮುಖ್ಯ") == "kn"


class TestMalayalamDetection:
    def test_simple_malayalam(self):
        assert detect_lang("നമസ്കാരം") == "ml"

    def test_malayalam_sentence(self):
        assert detect_lang("റോഡ് സുരക്ഷ പ്രധാനമാണ്") == "ml"


class TestBengaliDetection:
    def test_simple_bengali(self):
        assert detect_lang("নমস্কার") == "bn"

    def test_bengali_sentence(self):
        assert detect_lang("রাস্তা নিরাপত্তা গুরুত্বপূর্ণ") == "bn"


class TestGujaratiDetection:
    def test_simple_gujarati(self):
        assert detect_lang("નમસ્તે") == "gu"

    def test_gujarati_sentence(self):
        assert detect_lang("રોડ સુરક્ષા મહત્વપૂર્ણ છે") == "gu"


class TestPunjabiDetection:
    def test_simple_punjabi(self):
        assert detect_lang("ਨਮਸਤੇ") == "pa"

    def test_punjabi_sentence(self):
        assert detect_lang("ਸੜਕ ਸੁਰੱਖਿਆ ਮਹੱਤਵਪੂਰਨ ਹੈ") == "pa"


class TestOdiaDetection:
    def test_simple_odia(self):
        assert detect_lang("ନମସ୍କାର") == "or"

    def test_odia_sentence(self):
        assert detect_lang("ରାସ୍ତା ସୁରକ୍ଷା ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ") == "or"


class TestUrduDetection:
    def test_simple_urdu(self):
        assert detect_lang("السلام") == "ur"

    def test_urdu_sentence(self):
        assert detect_lang("سڑک حفاظت اہم ہے") == "ur"


class TestEnglishDetection:
    def test_english_returns_none(self):
        assert detect_lang("Road safety is important") is None

    def test_english_with_punctuation(self):
        assert detect_lang("What is the fine for speeding?") is None


class TestMixedScriptDetection:
    def test_hindi_english_mixed(self):
        result = detect_lang("Road सुरक्षा is important")
        assert result == "hi"

    def test_tamil_english_mixed(self):
        result = detect_lang("Road பாதுகாப்பு matters")
        assert result == "ta"

    def test_devanagari_priority_over_tamil(self):
        result = detect_lang("सड़क and சாலை")
        assert result == "hi"


class TestEdgeCases:
    def test_empty_string(self):
        assert detect_lang("") is None

    def test_only_numbers(self):
        assert detect_lang("12345") is None

    def test_only_punctuation(self):
        assert detect_lang("?!@#$%") is None

    def test_single_devanagari_char(self):
        assert detect_lang("अ") == "hi"

    def test_single_tamil_char(self):
        assert detect_lang("அ") == "ta"
