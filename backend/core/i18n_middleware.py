# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# c:\Hackathons\IITM\SafeVixAI\backend\core\i18n_middleware.py

import logging
import time
import sys
from pathlib import Path
from collections import defaultdict

for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from i18n.locales import translate_message

logger = logging.getLogger("safevixai.backend.i18n")

SUPPORTED_LOCALES = ["en", "hi", "ta", "te", "kn", "ml", "mr", "gu", "bn", "pa", "ur", "ar", "es", "fr"]
DEFAULT_LOCALE = "en"

def get_locale_from_request(request: Request) -> str:
    """Extracts preferred locale from Cookie or Accept-Language header."""
    # 1. Cookie check
    cookie_locale = request.cookies.get("svai-locale")
    if cookie_locale in SUPPORTED_LOCALES:
        return cookie_locale
    
    # 2. Header check
    accept_lang = request.headers.get("accept-language")
    if accept_lang:
        matched = accept_lang.split(",")[0].split(";")[0].strip()[:2]
        if matched in SUPPORTED_LOCALES:
            return matched
            
    return DEFAULT_LOCALE

async def i18n_middleware(request: Request, call_next):
    """Saves the detected locale into request state for downstream lookup."""
    locale = get_locale_from_request(request)
    request.state.locale = locale
    
    # Sync with request headers so downstreams can read it natively
    response = await call_next(request)
    return response

async def localized_http_exception_handler(request: Request, exc: HTTPException):
    """Localizes HTTPException details based on request locale."""
    locale = getattr(request.state, "locale", DEFAULT_LOCALE)
    detail = exc.detail
    
    if isinstance(detail, str):
        translated_detail = translate_message(detail, locale)
    else:
        translated_detail = detail
        
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": translated_detail},
        headers=exc.headers
    )

async def localized_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Localizes Pydantic schema validation errors."""
    locale = getattr(request.state, "locale", DEFAULT_LOCALE)
    errors = exc.errors()
    
    localized_errors = []
    for err in errors:
        msg = err.get("msg", "")
        # Common Pydantic messages translation
        translated_msg = msg
        if "field required" in msg:
            translated_msg = "यह फ़ील्ड आवश्यक है" if locale == "hi" else \
                             "இந்த புலம் தேவை" if locale == "ta" else \
                             "هذا الحقل مطلوب" if locale == "ar" else \
                             "Este campo es requerido" if locale == "es" else \
                             "Ce champ est requis" if locale == "fr" else \
                             "Field required"
        elif "value is not a valid email" in msg:
            translated_msg = "अमान्य ईमेल पता" if locale == "hi" else \
                             "தவறான மின்னஞ்சல் முகவரி" if locale == "ta" else \
                             "عنوان بريد إلكتروني غير صالح" if locale == "ar" else \
                             "Correo electrónico inválido" if locale == "es" else \
                             "Adresse e-mail invalide" if locale == "fr" else \
                             "Invalid email address"
                             
        localized_err = dict(err)
        localized_err["msg"] = translated_msg
        localized_errors.append(localized_err)
        
    return JSONResponse(
        status_code=422,
        content={"detail": localized_errors}
    )

# In-memory rate limit hit tracker for alerting
_rate_limit_hits: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_ALERT_THRESHOLD = 20
_RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes


async def localized_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Localizes RateLimitExceeded exceptions and monitors rate limit hit rate."""
    locale = getattr(request.state, "locale", DEFAULT_LOCALE)
    msg = translate_message("Rate limit exceeded", locale)

    # Track rate limit hits per endpoint
    now = time.time()
    endpoint = request.url.path
    hits = _rate_limit_hits[endpoint]
    hits.append(now)
    # Prune old entries outside the window
    cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
    _rate_limit_hits[endpoint] = [h for h in hits if h > cutoff]
    recent_count = len(_rate_limit_hits[endpoint])

    if recent_count == _RATE_LIMIT_ALERT_THRESHOLD:
        logger.warning(
            "Rate limit threshold reached: %d hits on %s in %ds window",
            recent_count, endpoint, _RATE_LIMIT_WINDOW_SECONDS,
        )
        get_alert_service().alert_external_api_failed(
            service_name="Rate Limiter",
            endpoint=endpoint,
            status_code=429,
            error_msg=f"{recent_count} rate limit hits in {_RATE_LIMIT_WINDOW_SECONDS}s on {endpoint}",
        )

    return JSONResponse(
        status_code=429,
        content={"detail": msg}
    )

def setup_backend_i18n(app: FastAPI):
    """Registers i18n middleware and custom exception handlers on the FastAPI application."""
    app.middleware("http")(i18n_middleware)
    app.add_exception_handler(HTTPException, localized_http_exception_handler)
    app.add_exception_handler(RequestValidationError, localized_validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, localized_rate_limit_exceeded_handler)
    logger.info("✅ Multi-language backend exception localization system successfully mounted.")
