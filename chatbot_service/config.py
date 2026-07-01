# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / '.env')


def _split_csv(value: str | None, *, default: list[str]) -> list[str]:
    if value is None or not value.strip():
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


def _as_path(value: str | None, *, default: Path) -> Path:
    if value is None or not value.strip():
        return default
    path = Path(value.strip())
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _as_optional_path(value: str | None) -> Path | None:
    if value is None or not value.strip():
        return None
    path = Path(value.strip())
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    environment: str = "development"
    service_name: str = Field(default="SafeVixAI Chatbot Service", alias="CHATBOT_SERVICE_NAME")
    service_port: int = Field(default=8010, alias="CHATBOT_SERVICE_PORT")
    cors_origins: str = "http://localhost:3000, http://127.0.0.1:3000"
    main_backend_base_url: str = "http://localhost:8000"
    main_backend_timeout_seconds: float = 20.0
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/safevixai"
    redis_url: str | None = None
    internal_api_key: str | None = Field(default=None, alias="CHATBOT_INTERNAL_API_KEY")
    chroma_persist_dir: Path = ROOT_DIR / "data" / "chroma_db"
    rag_data_dir: Path = ROOT_DIR / "data"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    rag_reranker: str | None = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rag_min_score: float = 0.55
    top_k_retrieval: int = 5
    default_llm_provider: str = "groq"
    default_llm_model: str = "deterministic-rag"
    speech_model_id: str = "ai4bharat/indic-seamless"
    speech_model_dir: Path | None = None
    speech_device: str = "auto"
    speech_default_target_lang: str = "eng"
    openweather_api_key: str | None = None
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_units: str = "metric"
    w3w_api_key: str | None = None
    opencage_api_key: str | None = None
    http_timeout_seconds: float = 20.0
    http_user_agent: str = "SafeVixAIChatbot/1.0"
    session_ttl_seconds: int = 86400
    admin_secret: str | None = None
    sentry_dsn: str | None = None

    @field_validator("main_backend_base_url", "openweather_base_url", mode="before")
    @classmethod
    def _rstrip_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @field_validator("chroma_persist_dir", "rag_data_dir", mode="before")
    @classmethod
    def _resolve_path(cls, v: str | Path) -> Path:
        p = Path(v) if isinstance(v, str) else v
        if not p.is_absolute():
            p = ROOT_DIR / p
        return p

    @field_validator("speech_model_dir", mode="before")
    @classmethod
    def _resolve_optional_path(cls, v: str | Path | None) -> Path | None:
        if v is None:
            return None
        p = Path(v) if isinstance(v, str) else v
        if not p.is_absolute():
            p = ROOT_DIR / p
        return p

    @field_validator("default_llm_provider", mode="before")
    @classmethod
    def _strip_lower_provider(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("default_llm_model", "speech_model_id", mode="before")
    @classmethod
    def _strip_value(cls, v: str) -> str:
        return v.strip()

    @field_validator("speech_device", "speech_default_target_lang", mode="before")
    @classmethod
    def _strip_lower_value(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("redis_url", "internal_api_key", "openweather_api_key",
                     "w3w_api_key", "opencage_api_key", "admin_secret", "sentry_dsn",
                     mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @computed_field
    @property
    def bootstrap_env_providers(self) -> list[str]:
        import os
        providers = []
        if os.environ.get("GROQ_API_KEY"): providers.append("groq")
        if os.environ.get("OPENAI_API_KEY"): providers.append("openai")
        if os.environ.get("OLLAMA_BASE_URL"): providers.append("ollama")
        if os.environ.get("VLLM_BASE_URL"): providers.append("vllm")
        if os.environ.get("CEREBRAS_API_KEY"): providers.append("cerebras")
        if os.environ.get("GEMINI_API_KEY"): providers.append("gemini")
        if os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_KEY"): providers.append("github")
        if os.environ.get("SARVAM_API_KEY"): providers.append("sarvam")
        if os.environ.get("MISTRAL_API_KEY"): providers.append("mistral")
        if os.environ.get("TOGETHER_API_KEY"): providers.append("together")
        if os.environ.get("OPENROUTER_API_KEY"): providers.append("openrouter")
        return providers


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == "production" and "*" in settings.cors_origins_list:
        raise RuntimeError("CORS_ORIGINS must list explicit origins when ENVIRONMENT=production")
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    settings.rag_data_dir.mkdir(parents=True, exist_ok=True)
    return settings

import logging as _logging

_logging.getLogger(__name__).info(f"Module config loaded for environment={get_settings().environment}")
_logging.getLogger(__name__).info(f"Contributor bootstrap providers detected: {get_settings().bootstrap_env_providers}")
