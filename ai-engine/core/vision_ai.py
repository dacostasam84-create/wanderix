import os
import base64
import anthropic
from typing import Optional


# ─────────────────────────────────────────
# Service Vision AI
# ─────────────────────────────────────────

class VisionAIService:
    """
    Service Vision AI — Analyse de photos de voyage via Claude Vision
    Identifie les lieux, monuments, hôtels, et génère des recommandations
    """

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    # ─────────────────────────────────────
    # Analyser une image de voyage
    # ─────────────────────────────────────

    async def analyze_travel_photo(
        self,
        image_data: bytes,
        language: str = "en",
        media_type: str = "image/jpeg",
    ) -> dict:
        try:
            # Encoder en base64
            image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

            from core.universal_language import SUPPORTED_LANGUAGES
            lang_name = SUPPORTED_LANGUAGES.get(language, "English")

            system = f"""You are Wanderix's expert travel vision AI.
Analyze travel photos and provide detailed information in {lang_name}.
Always respond in {lang_name} only.
Be enthusiastic and inspiring about travel."""

            user_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": f"""Analyze this travel photo and provide in {lang_name}:

1. LOCATION: What place/city/country is this? Be specific.
2. LANDMARKS: What monuments or attractions are visible?
3. ATMOSPHERE: Describe the mood, season, and best time to visit.
4. ACTIVITIES: Top 3 activities to do here.
5. HOTELS: What type of accommodation would suit this destination?
6. TRAVEL TIP: One unique insider tip for visiting this place.

Format your response as JSON with these exact keys:
{{
  "location": "city, country",
  "landmarks": ["landmark1", "landmark2"],
  "atmosphere": "description",
  "best_season": "season",
  "activities": ["activity1", "activity2", "activity3"],
  "hotel_style": "description of ideal accommodation",
  "travel_tip": "insider tip",
  "confidence": 0.95,
  "language": "{language}"
}}"""
                },
            ]

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )

            text = response.content[0].text.strip()

            # Parser le JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["success"] = True
                result["language"] = language
                return result

            return {
                "success": True,
                "location": "Unknown",
                "raw_analysis": text,
                "language": language,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "language": language,
            }

    # ─────────────────────────────────────
    # Identifier un hôtel depuis une photo
    # ─────────────────────────────────────

    async def identify_hotel(
        self,
        image_data: bytes,
        language: str = "en",
        media_type: str = "image/jpeg",
    ) -> dict:
        try:
            image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

            from core.universal_language import SUPPORTED_LANGUAGES
            lang_name = SUPPORTED_LANGUAGES.get(language, "English")

            user_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": f"""Analyze this hotel/accommodation photo in {lang_name}.
Provide JSON response:
{{
  "hotel_name": "name if identifiable or null",
  "hotel_type": "luxury/boutique/riad/resort/etc",
  "style": "description of style",
  "amenities_visible": ["pool", "etc"],
  "estimated_stars": 4,
  "city_guess": "city if possible",
  "similar_hotels": ["similar hotel type description"],
  "price_range": "budget/mid-range/luxury/ultra-luxury"
}}"""
                },
            ]

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": user_content}],
            )

            text = response.content[0].text.strip()
            import json, re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["success"] = True
                return result

            return {"success": True, "raw": text}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────
    # Générer une description multilingue
    # ─────────────────────────────────────

    async def generate_photo_description(
        self,
        image_data: bytes,
        language: str = "en",
        media_type: str = "image/jpeg",
        style: str = "inspiring",
    ) -> dict:
        try:
            image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

            from core.universal_language import SUPPORTED_LANGUAGES
            lang_name = SUPPORTED_LANGUAGES.get(language, "English")

            styles = {
                "inspiring": "Write an inspiring, poetic travel description",
                "informative": "Write a detailed, informative travel guide description",
                "social": "Write a catchy social media caption",
                "luxury": "Write an exclusive, luxury travel description",
            }

            style_prompt = styles.get(style, styles["inspiring"])

            user_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": f"{style_prompt} for this travel photo in {lang_name}. Maximum 3 sentences. Be vivid and evocative.",
                },
            ]

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": user_content}],
            )

            return {
                "success": True,
                "description": response.content[0].text.strip(),
                "language": language,
                "style": style,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}