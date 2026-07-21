# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations


from providers.sarvam_provider import SarvamProvider, Sarvam105BProvider, INDIAN_LANGUAGE_CODES, HIGH_STAKES_INTENTS
from providers.router import detect_lang


class TestIndianLanguageCodes:
    def test_hindi_in_codes(self):
        assert "hi" in INDIAN_LANGUAGE_CODES

    def test_tamil_in_codes(self):
        assert "ta" in INDIAN_LANGUAGE_CODES

    def test_telugu_in_codes(self):
        assert "te" in INDIAN_LANGUAGE_CODES

    def test_kannada_in_codes(self):
        assert "kn" in INDIAN_LANGUAGE_CODES

    def test_malayalam_in_codes(self):
        assert "ml" in INDIAN_LANGUAGE_CODES


class TestHighStakesIntents:
    def test_challan_dispute_is_high_stakes(self):
        assert "CHALLAN_DISPUTE" in HIGH_STAKES_INTENTS

    def test_legal_advice_is_high_stakes(self):
        assert "LEGAL_ADVICE" in HIGH_STAKES_INTENTS

    def test_emergency_report_is_high_stakes(self):
        assert "EMERGENCY_REPORT" in HIGH_STAKES_INTENTS


class TestSarvamProviderRouting:
    def _make_settings(self):
        from config import Settings
        from pathlib import Path
        return Settings(
            environment="test",
            service_name="test",
            service_port=8010,
            cors_origins="http://localhost:3000",
            main_backend_base_url="http://localhost:8000",
            main_backend_timeout_seconds=20.0,
            redis_url=None,
            internal_api_key=None,
            chroma_persist_dir=Path("/tmp/chroma_test"),
            rag_data_dir=Path("/tmp/rag_test"),
            embedding_model="test",
            rag_min_score=0.0,
            top_k_retrieval=5,
            default_llm_provider="groq",
            default_llm_model="test",
            speech_model_id="test",
            speech_model_dir=None,
            speech_device="cpu",
            speech_default_target_lang="eng",
            openweather_api_key=None,
            openweather_base_url="https://api.openweathermap.org/data/2.5",
            openweather_units="metric",
            w3w_api_key=None,
            opencage_api_key=None,
            http_timeout_seconds=5.0,
            http_user_agent="test/1.0",
            session_ttl_seconds=3600,
            admin_secret=None,
        )

    def test_sarvam_30b_for_general_indian(self):
        from providers.router import ProviderRouter

        settings = self._make_settings()
        router = ProviderRouter(settings)

        from providers.base import ProviderRequest

        request = ProviderRequest(
            message="सड़क सुरक्षा क्या है?",
            intent="general",
            history=[],
        )

        provider_name = router._select_provider_name(request, detected_lang="hi")
        assert provider_name == "sarvam_30b"

    def test_sarvam_105b_for_challan_dispute(self):
        from providers.router import ProviderRouter

        settings = self._make_settings()
        router = ProviderRouter(settings)

        from providers.base import ProviderRequest

        request = ProviderRequest(
            message="धारा 185 का जुर्माना क्या है?",
            intent="challan_dispute",
            history=[],
        )

        provider_name = router._select_provider_name(request, detected_lang="hi")
        assert provider_name == "sarvam_105b"

    def test_sarvam_30b_for_tamil_general(self):
        from providers.router import ProviderRouter

        settings = self._make_settings()
        router = ProviderRouter(settings)

        from providers.base import ProviderRequest

        request = ProviderRequest(
            message="சாலை பாதுகாப்பு விதிகள்",
            intent="general",
            history=[],
        )

        provider_name = router._select_provider_name(request, detected_lang="ta")
        assert provider_name == "sarvam_30b"


class TestLanguageDetection:
    def test_hindi_devanagari(self):
        assert detect_lang("सड़क सुरक्षा") == "hi"

    def test_tamil(self):
        assert detect_lang("சாலை பாதுகாப்பு") == "ta"

    def test_telugu(self):
        assert detect_lang("రోడ్డు భద్రత") == "te"

    def test_kannada(self):
        assert detect_lang("ರಸ್ತೆ ಸುರಕ್ಷತೆ") == "kn"

    def test_malayalam(self):
        assert detect_lang("റോഡ് സുരക്ഷ") == "ml"

    def test_bengali(self):
        assert detect_lang("রাস্তা নিরাপত্তা") == "bn"

    def test_gujarati(self):
        assert detect_lang("રોડ સુરક્ષા") == "gu"

    def test_punjabi(self):
        assert detect_lang("ਸੜਕ ਸੁਰੱਖਿਆ") == "pa"

    def test_odia(self):
        assert detect_lang("ରାସ୍ତା ସୁରକ୍ଷା") == "or"

    def test_english_returns_none(self):
        assert detect_lang("Road safety is important") is None

    def test_mixed_hindi_english(self):
        result = detect_lang("Road सुरक्षा is important")
        assert result == "hi"

    def test_empty_string(self):
        assert detect_lang("") is None


class TestSarvamProviderInstantiation:
    def test_sarvam_provider_name(self):
        provider = SarvamProvider()
        assert provider.name == "sarvam_30b"

    def test_sarvam_105b_provider_name(self):
        provider = Sarvam105BProvider()
        assert provider.name == "sarvam_105b"
