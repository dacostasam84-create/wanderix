import os
import httpx
import anthropic
from typing import Optional

DID_API_KEY = os.environ.get("DID_API_KEY", "emFobm91bmlpc3NhbUBnbWFpbC5jb20:_-4Ud0i-rNAnaiROIn15L")
DID_BASE_URL = "https://api.d-id.com"

DID_HEADERS = {
    "Authorization": f"Basic {DID_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

WANDERIX_AVATARS = {
    "female": {
        "name": "Hélène",
        "agent_id": "v2_agt_YQasg7JL",
        "image_url": None,
        "voice_id": "en-US-JennyNeural",
        "gender": "female",
    },
    "male": {
        "name": "Karim",
        "agent_id": None,
        "image_url": "https://d-id-public-bucket.s3.amazonaws.com/or-roman.jpg",
        "voice_id": "en-US-GuyNeural",
        "gender": "male",
    },
}

VOICE_BY_LANGUAGE = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "ar": {"female": "ar-SA-ZariyahNeural", "male": "ar-SA-HamedNeural"},
    "es": {"female": "es-ES-ElviraNeural", "male": "es-ES-AlvaroNeural"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunxiNeural"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
    "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"},
    "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural"},
    "hi": {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"},
    "tr": {"female": "tr-TR-EmelNeural", "male": "tr-TR-AhmetNeural"},
    "nl": {"female": "nl-NL-FennaNeural", "male": "nl-NL-MaartenNeural"},
    "pl": {"female": "pl-PL-ZofiaNeural", "male": "pl-PL-MarekNeural"},
    "sv": {"female": "sv-SE-SofieNeural", "male": "sv-SE-MattiasNeural"},
    "uk": {"female": "uk-UA-PolinaNeural", "male": "uk-UA-OstapNeural"},
    "he": {"female": "he-IL-HilaNeural", "male": "he-IL-AvriNeural"},
    "fa": {"female": "fa-IR-DilaraNeural", "male": "fa-IR-FaridNeural"},
    "id": {"female": "id-ID-GadisNeural", "male": "id-ID-ArdiNeural"},
    "vi": {"female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural"},
    "th": {"female": "th-TH-PremwadeeNeural", "male": "th-TH-NiwatNeural"},
}


class DIDAvatarService:

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    async def generate_video(self, text: str, gender: str = "female", language: str = "en", destination: Optional[str] = None) -> dict:
        try:
            avatar = WANDERIX_AVATARS.get(gender, WANDERIX_AVATARS["female"])
            voice = VOICE_BY_LANGUAGE.get(language, VOICE_BY_LANGUAGE["en"])
            voice_id = voice.get(gender, voice["female"])

            if avatar.get("agent_id"):
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{DID_BASE_URL}/agents/{avatar['agent_id']}/chat",
                        headers=DID_HEADERS,
                        json={
                            "messages": [{"role": "user", "content": text}],
                            "stream": False,
                        },
                        timeout=30,
                    )
                    data = response.json()
                return {
                    "agent_id": avatar["agent_id"],
                    "talk_id": data.get("id", ""),
                    "status": "processing",
                    "avatar": avatar["name"],
                    "gender": gender,
                    "language": language,
                    "text": text,
                    "data": data,
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{DID_BASE_URL}/talks",
                    headers=DID_HEADERS,
                    json={
                        "source_url": avatar["image_url"],
                        "script": {
                            "type": "text",
                            "input": text,
                            "provider": {
                                "type": "microsoft",
                                "voice_id": voice_id,
                            },
                        },
                        "config": {"fluent": True, "pad_audio": 0},
                    },
                    timeout=30,
                )
                data = response.json()

            talk_id = data.get("id")
            if not talk_id:
                return {"error": "Failed to create talk", "details": data}

            return {
                "talk_id": talk_id,
                "status": "processing",
                "avatar": avatar["name"],
                "gender": gender,
                "language": language,
                "voice": voice_id,
                "text": text,
            }

        except Exception as e:
            return {"error": str(e), "gender": gender, "language": language}

    async def get_video_status(self, talk_id: str) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{DID_BASE_URL}/talks/{talk_id}",
                    headers=DID_HEADERS,
                    timeout=15,
                )
                data = response.json()
            status = data.get("status", "unknown")
            result = {"talk_id": talk_id, "status": status}
            if status == "done":
                result["video_url"] = data.get("result_url")
                result["duration"] = data.get("duration")
                result["ready"] = True
            elif status == "error":
                result["error"] = data.get("error", {}).get("description", "Unknown error")
                result["ready"] = False
            else:
                result["ready"] = False
            return result
        except Exception as e:
            return {"talk_id": talk_id, "error": str(e), "ready": False}

    async def avatar_chat_with_video(self, message: str, gender: str = "female", language: str = "en", destination: Optional[str] = None, conversation_history: Optional[list] = None) -> dict:
        try:
            avatar = WANDERIX_AVATARS.get(gender, WANDERIX_AVATARS["female"])
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=300,
                    system=self._build_system_prompt(avatar, language, destination),
                    messages=(conversation_history or []) + [{"role": "user", "content": message}],
                )
                reply_text = response.content[0].text.strip()
            except Exception:
                reply_text = self._get_mock_response(gender, language, destination)

            video_result = await self.generate_video(text=reply_text, gender=gender, language=language, destination=destination)
            return {
                "text": reply_text,
                "language": language,
                "gender": gender,
                "avatar_name": avatar["name"],
                "video": video_result,
                "has_video": "talk_id" in video_result or "agent_id" in video_result,
            }
        except Exception as e:
            return {"text": self._get_mock_response(gender, language, destination), "language": language, "gender": gender, "error": str(e), "has_video": False}

    async def welcome_with_video(self, gender: str = "female", language: str = "en", destination: Optional[str] = None) -> dict:
        welcome_messages = {
            "en": f"Welcome to Wanderix! {'I will be your guide in ' + destination + '!' if destination else 'Where would you like to travel today?'}",
            "fr": f"Bienvenue sur Wanderix! {'Je serai votre guide à ' + destination + '!' if destination else 'Où souhaitez-vous voyager?'}",
            "ar": f"مرحباً بك في Wanderix! {'سأكون دليلك في ' + destination + '!' if destination else 'إلى أين تريد السفر اليوم؟'}",
            "es": f"¡Bienvenido a Wanderix! {'¡Seré tu guía en ' + destination + '!' if destination else '¿A dónde quieres viajar hoy?'}",
            "de": f"Willkommen bei Wanderix! {'Ich bin Ihr Guide in ' + destination + '!' if destination else 'Wohin möchten Sie reisen?'}",
            "zh": f"欢迎来到Wanderix！{'我将是您在' + destination + '的向导！' if destination else '您今天想去哪里旅行？'}",
            "ja": f"Wanderixへようこそ！{'私は' + destination + 'でのガイドです！' if destination else '今日はどこへ旅行しますか？'}",
            "pt": f"Bem-vindo ao Wanderix! {'Serei seu guia em ' + destination + '!' if destination else 'Para onde quer viajar?'}",
            "ru": f"Добро пожаловать в Wanderix! {'Я буду вашим гидом в ' + destination + '!' if destination else 'Куда хотите путешествовать?'}",
            "ko": f"Wanderix에 오신 것을 환영합니다! {destination + '에서 안내해드리겠습니다!' if destination else '오늘 어디로 여행하시겠어요?'}",
            "hi": f"Wanderix में स्वागत है! {'मैं ' + destination + ' में आपका गाइड रहूंगा!' if destination else 'आज कहाँ यात्रा करना चाहते हैं?'}",
        }
        text = welcome_messages.get(language, welcome_messages["en"])
        avatar = WANDERIX_AVATARS.get(gender, WANDERIX_AVATARS["female"])
        video_result = await self.generate_video(text=text, gender=gender, language=language, destination=destination)
        return {
            "text": text,
            "language": language,
            "gender": gender,
            "avatar_name": avatar["name"],
            "video": video_result,
            "has_video": "talk_id" in video_result or "agent_id" in video_result,
        }

    def _build_system_prompt(self, avatar: dict, language: str, destination: Optional[str]) -> str:
        from core.universal_language import SUPPORTED_LANGUAGES
        lang_name = SUPPORTED_LANGUAGES.get(language, language)
        return f"""You are {avatar['name']}, Wanderix AI travel guide. Respond ONLY in {lang_name}. Max 2 sentences. Warm and inspiring.{f' Destination: {destination}.' if destination else ''}"""

    def _get_mock_response(self, gender: str, language: str, destination: Optional[str]) -> str:
        name = "Hélène" if gender == "female" else "Karim"
        responses = {
            "en": f"{name} here! {'Discover ' + destination + ' with Wanderix!' if destination else 'Let me help plan your journey!'}",
            "fr": f"C'est {name}! {'Découvrez ' + destination + ' avec Wanderix!' if destination else 'Je vous aide à planifier votre voyage!'}",
            "ar": f"أنا {'هيلين' if gender == 'female' else 'كريم'}! {'اكتشف ' + destination + ' مع Wanderix!' if destination else 'دعني أساعدك في التخطيط!'}",
        }
        return responses.get(language, responses["en"])