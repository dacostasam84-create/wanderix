import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPPORTED_LANGUAGES = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
    "ru": "Russian", "sv": "Swedish", "no": "Norwegian", "da": "Danish",
    "fi": "Finnish", "cs": "Czech", "ro": "Romanian", "hu": "Hungarian",
    "el": "Greek", "bg": "Bulgarian", "hr": "Croatian", "sk": "Slovak",
    "sl": "Slovenian", "uk": "Ukrainian", "ca": "Catalan", "eu": "Basque",
    "ar": "Arabic", "he": "Hebrew", "fa": "Persian (Farsi)", "tr": "Turkish",
    "ur": "Urdu", "zh": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese", "ko": "Korean", "hi": "Hindi", "bn": "Bengali",
    "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "gu": "Gujarati",
    "pa": "Punjabi", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
    "ms": "Malay", "tl": "Filipino", "my": "Burmese", "km": "Khmer",
    "lo": "Lao", "si": "Sinhala", "ne": "Nepali", "ka": "Georgian",
    "az": "Azerbaijani", "kk": "Kazakh", "uz": "Uzbek", "sw": "Swahili",
    "am": "Amharic", "ha": "Hausa", "yo": "Yoruba", "ig": "Igbo",
    "zu": "Zulu", "af": "Afrikaans", "so": "Somali", "qu": "Quechua",
    "ht": "Haitian Creole", "gn": "Guarani",
}

RTL_LANGUAGES = {"ar", "he", "fa", "ur"}


async def _openai_chat(system: str, user: str) -> str:
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return "Error: OpenAI API key not found"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=30,
            )
            data = response.json()
            if "choices" not in data:
                return f"OpenAI Error: {data}"
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {e}"


class UniversalLanguageService:

    async def detect_language(self, text: str) -> dict:
        try:
            result_text = await _openai_chat(
                'You are a language detector. Respond ONLY with JSON: {"code": "xx", "name": "Language", "confidence": 0.99}',
                f"Detect language: {text}"
            )
            result = json.loads(result_text)
            result["rtl"] = result.get("code") in RTL_LANGUAGES
            return result
        except Exception:
            return {"code": "en", "name": "English", "confidence": 0.5, "rtl": False}

    async def translate(self, text: str, target_language: str, context: Optional[str] = None, source_language: Optional[str] = None) -> dict:
        try:
            lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
            translated = await _openai_chat(
                f"You are a travel translator. Translate to {lang_name}. Return ONLY the translated text.",
                text
            )
            return {
                "original": text,
                "translated": translated,
                "target_language": target_language,
                "target_language_name": lang_name,
                "rtl": target_language in RTL_LANGUAGES,
            }
        except Exception as e:
            return {"original": text, "translated": text, "error": str(e), "target_language": target_language, "rtl": False}

    async def respond_in_language(self, user_message: str, system_prompt: str = "You are Wanderix AI.", detected_language: Optional[str] = None) -> dict:
        try:
            if not detected_language:
                detection = await self.detect_language(user_message)
                detected_language = detection.get("code", "en")
            lang_name = SUPPORTED_LANGUAGES.get(detected_language, detected_language)
            reply = await _openai_chat(
                f"{system_prompt}\nRespond ONLY in {lang_name}.",
                user_message
            )
            return {"reply": reply, "detected_language": detected_language, "language_name": lang_name, "rtl": detected_language in RTL_LANGUAGES}
        except Exception as e:
            return {"reply": user_message, "detected_language": detected_language or "en", "error": str(e), "rtl": False}

    def translate_object(self, obj: dict, target_language: str, fields_to_translate: list, context: Optional[str] = None) -> dict:
        result = dict(obj)
        for field in fields_to_translate:
            if field in obj and isinstance(obj[field], str) and obj[field]:
                import asyncio
                translation = asyncio.get_event_loop().run_until_complete(
                    self.translate(obj[field], target_language, context=context)
                )
                result[field] = translation.get("translated", obj[field])
        return result

    def get_supported_languages(self) -> list:
        return [{"code": code, "name": name, "rtl": code in RTL_LANGUAGES} for code, name in SUPPORTED_LANGUAGES.items()]