# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)



class Settings(BaseSettings):
    app_name: str = 'SafeVixAI Backend'
    version: str = '1.0.0'
    environment: str = 'development'
    api_v1_prefix: str = '/api/v1'
    cors_origins_env: str = Field(default='*', validation_alias='CORS_ORIGINS')
    frontend_url: str | None = Field(default=None, validation_alias='FRONTEND_URL')
    admin_secret: str | None = None
    enable_mcp: bool = False
    sentry_dsn: str | None = Field(default=None, validation_alias='SENTRY_DSN')
    jwks_url: str | None = Field(default=None, validation_alias='JWKS_URL')

    database_url: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/safevixai'
    database_replica_url: str | None = None
    redis_url: str | None = None
    redis_tls_enabled: bool = Field(default=False, validation_alias='REDIS_TLS_ENABLED')
    redis_password: str | None = Field(default=None, validation_alias='REDIS_PASSWORD')
    provider_encryption_key: str | None = Field(default=None, validation_alias='PROVIDER_ENCRYPTION_KEY')
    # P1-05: Increased pool size from 1 to 10 (audit H8) to prevent severe connection bottlenecks
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout_seconds: float = 30.0
    db_pool_recycle_seconds: int = 1800
    echo_queries: bool = False

    allowed_hosts_env: str | None = Field(default=None, validation_alias='ALLOWED_HOSTS')
    default_radius: int = 5000
    max_radius: int = 50000
    emergency_min_results: int = 3
    emergency_radius_steps_env: str = Field(
        default='500,1000,5000,10000,25000,50000',
        validation_alias='EMERGENCY_RADIUS_STEPS',
    )
    cache_ttl_seconds: int = 3600
    geocode_cache_ttl_seconds: int = 86400
    authority_cache_ttl_seconds: int = 3600
    route_cache_ttl_seconds: int = 900

    overpass_url: str = 'https://overpass-api.de/api/interpreter'
    overpass_urls_env: str | None = Field(default=None, validation_alias='OVERPASS_URLS')
    photon_url: str = 'https://photon.komoot.io'
    nominatim_url: str = 'https://nominatim.openstreetmap.org'
    openrouteservice_base_url: str = 'https://api.openrouteservice.org'
    openrouteservice_api_key: str | None = None
    http_user_agent: str = 'SafeVixAI/1.0'
    request_timeout_seconds: float = 20.0
    upstream_retry_attempts: int = 2
    upstream_retry_backoff_seconds: float = 1.5
    data_gov_api_key: str | None = None
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    road_photo_bucket: str = 'road-photos'
    default_officer_ward: str = 'ward_09_teynampet'

    chatbot_mode: str = 'external_service'
    chatbot_ready: bool = False
    chatbot_service_url: str = 'http://localhost:8010/api/v1'
    chatbot_request_timeout_seconds: float = 20.0
    chatbot_internal_api_key: str | None = None

    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1] / 'data')
    upload_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[1] / 'data' / 'uploads')
    local_upload_base_url: str | None = None
    max_upload_bytes: int = 5 * 1024 * 1024
    allowed_upload_content_types_env: str = Field(
        default='image/jpeg,image/png,image/webp',
        validation_alias='ALLOWED_UPLOAD_CONTENT_TYPES',
    )

    # --- Civic Intelligence ETL settings ---
    cpgrams_api_url: str | None = None
    cpgrams_api_key: str | None = None
    lgd_api_key: str | None = None
    datameet_github_base: str = 'https://raw.githubusercontent.com/datameet/maps/master'
    india_geodata_base: str = 'https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson'
    lgd_csv_base_url: str = 'https://lgdirectory.gov.in/downloadDirectory'
    etl_batch_size: int = 1000
    etl_enabled: bool = True
    municipal_gis_registry_env: str = Field(default='{}', validation_alias='MUNICIPAL_GIS_REGISTRY')
    grievance_portals_env: str = Field(default='{}', validation_alias='GRIEVANCE_PORTALS')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    @property
    def cors_origins(self) -> list[str]:
        value = self.cors_origins_env
        if value is None or value == '':
            return ['*']
        if value.strip() == '*':
            if self.environment == 'production':
                import logging
                logging.getLogger(__name__).warning(
                    'CORS_ORIGINS=* in production — set it to your frontend URL in Render env vars.'
                )
            return ['*']
        return [item.strip() for item in value.split(',') if item.strip()]

    @field_validator('database_url', mode='before')
    @classmethod
    def normalize_database_url(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError('database_url must be a string')
        normalized = value.strip()
        if normalized.startswith('postgres://'):
            normalized = normalized.replace('postgres://', 'postgresql://', 1)
        if normalized.startswith('postgresql://'):
            normalized = normalized.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        # Auto-correct Supabase pooler using direct port 5432 to standard transaction port 6543
        if 'pooler.supabase.com' in normalized and ':5432' in normalized:
            import logging
            logging.getLogger('safevixai.config').warning(
                'Supabase pooler host detected with direct session port 5432! '
                'Rewriting database port to transaction pooler port 6543 to prevent connection saturation.'
            )
            normalized = normalized.replace(':5432', ':6543', 1)
            
        return normalized

    @property
    def emergency_radius_steps(self) -> list[int]:
        return [int(item.strip()) for item in self.emergency_radius_steps_env.split(',') if item.strip()]

    @property
    def overpass_urls(self) -> list[str]:
        value = self.overpass_urls_env
        if value is None or not value.strip():
            return [self.overpass_url]
        urls = [item.strip() for item in value.split(',') if item.strip()]
        return urls or [self.overpass_url]

    @property
    def allowed_upload_content_types(self) -> list[str]:
        value = self.allowed_upload_content_types_env
        if value is None or value == '':
            return ['image/jpeg', 'image/png', 'image/webp']
        return [item.strip().lower() for item in value.split(',') if item.strip()]

    @property
    def mcp_enabled(self) -> bool:
        if self.environment == 'production':
            return False
        return self.enable_mcp or self.environment in {'development', 'test'}

    @field_validator('local_upload_base_url', mode='before')
    @classmethod
    def normalize_upload_base_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('local_upload_base_url must be a string')
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.startswith('LOCAL_UPLOAD_BASE_URL='):
            normalized = normalized.split('=', 1)[1].strip()
        return normalized.rstrip('/')

    @field_validator('openrouteservice_base_url', mode='before')
    @classmethod
    def normalize_openrouteservice_base_url(cls, value: Any) -> str:
        if value is None:
            return 'https://api.openrouteservice.org'
        if not isinstance(value, str):
            raise ValueError('openrouteservice_base_url must be a string')
        normalized = value.strip()
        if not normalized:
            return 'https://api.openrouteservice.org'
        return normalized.rstrip('/')

    @field_validator('chatbot_service_url', mode='before')
    @classmethod
    def normalize_chatbot_service_url(cls, value: Any) -> str:
        if value is None:
            return 'http://localhost:8010/api/v1'
        if not isinstance(value, str):
            raise ValueError('chatbot_service_url must be a string')
        normalized = value.strip()
        if not normalized:
            return 'http://localhost:8010/api/v1'
        normalized = normalized.rstrip('/')
        if normalized.endswith('/api/v1'):
            return normalized
        return f'{normalized}/api/v1'

    @field_validator('frontend_url', mode='before')
    @classmethod
    def normalize_frontend_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError('frontend_url must be a string')
        normalized = value.strip()
        if not normalized:
            return None
        return normalized.rstrip('/')


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == 'production' and settings.cors_origins_env.strip() == '*':
        raise RuntimeError('CORS_ORIGINS must list explicit origins when ENVIRONMENT=production')
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        (settings.upload_dir / 'temp_pending').mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.debug("Suppressed exception", exc_info=True)
    return settings
