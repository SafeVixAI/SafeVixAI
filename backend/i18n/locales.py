# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# c:\Hackathons\IITM\SafeVixAI\backend\i18n\locales.py

# Multi-language lookup dictionary for backend exceptions and validation errors
TRANSLATIONS: dict[str, dict[str, str]] = {
    "Invalid credentials": {
        "en": "Invalid credentials",
        "hi": "अमान्य क्रेडेंशियल",
        "ta": "தவறான நற்சான்றிதழ்கள்",
        "ar": "بيانات الاعتماد غير صالحة",
        "es": "Credenciales inválidas",
        "fr": "Identifiants invalides"
    },
    "Refresh token has expired": {
        "en": "Refresh token has expired",
        "hi": "रिफ्रेश टोकन समाप्त हो गया है",
        "ta": "புதுப்பிப்பு டோக்கன் காலாவதியானது",
        "ar": "انتهت صلاحية رمز التحديث",
        "es": "El token de actualización ha expirado",
        "fr": "Le jeton de rafraîchissement a expiré"
    },
    "Refresh token has been revoked": {
        "en": "Refresh token has been revoked",
        "hi": "रिफ्रेश टोकन निरस्त कर दिया गया है",
        "ta": "புதுப்பிப்பு டோக்கன் ரத்து செய்யப்பட்டுள்ளது",
        "ar": "تم إلغاء رمز التحديث",
        "es": "El token de actualización ha sido revocado",
        "fr": "Le jeton de rafraîchissement a été révoqué"
    },
    "Invalid refresh token": {
        "en": "Invalid refresh token",
        "hi": "अमान्य रिफ्रेश टोकन",
        "ta": "தவறான புதுப்பிப்பு டோக்கன்",
        "ar": "رمز تحديث غير صالحة",
        "es": "Token de actualización inválido",
        "fr": "Jeton de rafraîchissement invalide"
    },
    "Invalid token purpose": {
        "en": "Invalid token purpose",
        "hi": "अमान्य टोकन उद्देश्य",
        "ta": "தவறான டோக்கன் நோக்கம்",
        "ar": "غرض الرمز غير صالحة",
        "es": "Propósito de token inválido",
        "fr": "Objectif du jeton invalide"
    },
    "Operator login is not configured": {
        "en": "Operator login is not configured",
        "hi": "ऑपरेटर लॉगिन कॉन्फ़िगर नहीं है",
        "ta": "ஆபரேட்டர் உள்நுழைவு கட்டமைக்கப்படவில்லை",
        "ar": "لم يتم تكوين تسجيل دخول المشغل",
        "es": "El inicio de sesión del operador no está configurado",
        "fr": "La connexion de l'opérateur n'est pas configurée"
    },
    "Invalid UUID format": {
        "en": "Invalid UUID format",
        "hi": "अमान्य यूयूआईडी प्रारूप",
        "ta": "தவறான UUID வடிவம்",
        "ar": "تنسيق UUID غير صالح",
        "es": "Formato de UUID inválido",
        "fr": "Format UUID invalide"
    },
    "Tracking session not found or expired": {
        "en": "Tracking session not found or expired",
        "hi": "ट्रैकिंग सत्र नहीं मिला या समाप्त हो गया",
        "ta": "கண்காணிப்பு அமர்வு கிடைக்கவில்லை அல்லது காலாவதியானது",
        "ar": "جلسة التتبع غير موجودة أو انتهت صلاحيتها",
        "es": "Sesión de seguimiento no encontrada o expirada",
        "fr": "Session de suivi introuvable ou expirée"
    },
    "Tracking session not found": {
        "en": "Tracking session not found",
        "hi": "ट्रैकिंग सत्र नहीं मिला",
        "ta": "கண்காணிப்பு அமர்வு கிடைக்கவில்லை",
        "ar": "جلسة التتبع غير موجودة",
        "es": "Sesión de seguimiento no encontrada",
        "fr": "Session de suivi introuvable"
    },
    "Tracking token required": {
        "en": "Tracking token required",
        "hi": "ट्रैकिंग टोकन आवश्यक है",
        "ta": "கண்காணிப்பு டோக்கன் தேவை",
        "ar": "رمز التتبع مطلوب",
        "es": "Token de seguimiento requerido",
        "fr": "Jeton de suivi requis"
    },
    "Invalid tracking link": {
        "en": "Invalid tracking link",
        "hi": "अमान्य ट्रैकिंग लिंक",
        "ta": "தவறான கண்காணிப்பு இணைப்பு",
        "ar": "رابط تتبع غير صالح",
        "es": "Enlace de seguimiento inválido",
        "fr": "Lien de suivi invalide"
    },
    "Invalid or expired tracking link": {
        "en": "Invalid or expired tracking link",
        "hi": "अमान्य या समाप्त हो चुका ट्रैकिंग लिंक",
        "ta": "தவறான அல்லது காலாவதியான கண்காணிப்பு இணைப்பு",
        "ar": "رابط تتبع غير صالح أو منتهي الصلاحية",
        "es": "Enlace de seguimiento inválido o expirado",
        "fr": "Lien de suivi invalide ou expiré"
    },
    "Admin secret required": {
        "en": "Admin secret required",
        "hi": "एडमिन सीक्रेट आवश्यक है",
        "ta": "நிர்வாக ரகசியம் தேவை",
        "ar": "مطلوب كلمة سر المسؤول",
        "es": "Se requiere secreto de administrador",
        "fr": "Secret administrateur requis"
    },
    "ETL scheduler not initialized": {
        "en": "ETL scheduler not initialized",
        "hi": "ईटीएल शेड्यूलर प्रारंभ नहीं हुआ",
        "ta": "ETL திட்டமிடுபவர் தொடங்கப்படவில்லை",
        "ar": "لم يتم تهيئة جدولة ETL",
        "es": "Programador ETL no inicializado",
        "fr": "Planificateur ETL non initialisé"
    },
    "Pole not found": {
        "en": "Pole not found",
        "hi": "पोल नहीं मिला",
        "ta": "கம்பம் கிடைக்கவில்லை",
        "ar": "العمود غير موجود",
        "es": "Poste no encontrado",
        "fr": "Poteau introuvable"
    },
    "Municipality not found": {
        "en": "Municipality not found",
        "hi": "नगर पालिका नहीं मिली",
        "ta": "நகராட்சி கிடைக்கவில்லை",
        "ar": "البلدية غير موجودة",
        "es": "Municipio no encontrado",
        "fr": "Municipalité introuvable"
    },
    "Unable to record SOS incident": {
        "en": "Unable to record SOS incident",
        "hi": "एसओएस घटना दर्ज करने में असमर्थ",
        "ta": "SOS சம்பவத்தை பதிவு செய்ய முடியவில்லை",
        "ar": "غير قادر على تسجيل حادثة SOS",
        "es": "No se pudo registrar el incidente de SOS",
        "fr": "Impossible d'enregistrer l'incident SOS"
    },
    "CSRF token missing or invalid": {
        "en": "CSRF token missing or invalid",
        "hi": "सीएसआरएफ टोकन गायब या अमान्य है",
        "ta": "CSRF டோக்கன் இல்லை அல்லது தவறானது",
        "ar": "رمز CSRF مفقود أو غير صالح",
        "es": "Token CSRF faltante o inválido",
        "fr": "Jeton CSRF manquant ou invalide"
    },
    "Rate limit exceeded": {
        "en": "Rate limit exceeded. Please retry later.",
        "hi": "दर सीमा पार हो गई। कृपया बाद में पुनः प्रयास करें।",
        "ta": "விகித வரம்பு மீறப்பட்டது. பின்னர் மீண்டும் முயற்சிக்கவும்.",
        "ar": "تم تجاوز حد المعدل. يرجى إعادة المحاولة لاحقًا.",
        "es": "Límite de tasa excedido. Por favor intente más tarde.",
        "fr": "Limite de débit dépassée. Veuillez réessayer plus tard."
    },
    "Internal server error": {
        "en": "Internal server error. The team has been notified.",
        "hi": "आंतरिक सर्वर त्रुटि। टीम को सूचित कर दिया गया है।",
        "ta": "உள் சர்வர் பிழை. குழுவிற்கு அறிவிக்கப்பட்டுள்ளது.",
        "ar": "خطأ داخلي في الخادم. تم إخطار الفريق.",
        "es": "Error interno del servidor. El equipo ha sido notificado.",
        "fr": "Erreur interne du serveur. L'équipe a été notifiée."
    }
}

def translate_message(message: str, locale: str) -> str:
    """Translates a message to the requested locale if supported; otherwise returns original message."""
    # Standard fallback to English, then original
    if message in TRANSLATIONS:
        return TRANSLATIONS[message].get(locale, TRANSLATIONS[message].get("en", message))

    # Check for prefix or substring matches for circuit breakers and others
    for key, loc_map in TRANSLATIONS.items():
        if key in message:
            return loc_map.get(locale, loc_map.get("en", message))

    return message
