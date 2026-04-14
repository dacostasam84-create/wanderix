import os
import logging
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from core.prompt_builder import PromptBuilder, UserContext, Language
from core.translation_layer import TranslationLayer
import anthropic

# ─────────────────────────────────────────
# Setup
# ─────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wanderix AI Engine",
    description="Cerveau IA multilingue de Wanderix",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("BACKEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instances globales
prompt_builder = PromptBuilder()
translation_layer = TranslationLayer()
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


# ─────────────────────────────────────────
# Sécurité — API Key interne
# ─────────────────────────────────────────

def verify_internal_key(x_internal_key: str = Header(...)):
    expected = os.environ.get("INTERNAL_API_KEY")
    if x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_internal_key


# ─────────────────────────────────────────
# Modèles de requêtes
# ─────────────────────────────────────────

class ItineraryRequest(BaseModel):
    destination: str
    language: str = "en"
    nationality: Optional[str] = None
    travel_style: Optional[str] = None
    interests: Optional[list[str]] = None
    budget: Optional[str] = None
    trip_duration: Optional[int] = 7
    group_type: Optional[str] = None


class HotelRecommendationRequest(BaseModel):
    destination: str
    hotels: list[dict]
    language: str = "en"
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    group_type: Optional[str] = None


class GuideMatchRequest(BaseModel):
    destination: str
    guides: list[dict]
    language: str = "en"
    interests: Optional[list[str]] = None
    travel_style: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    destination: str
    language: str = "en"
    conversation_history: Optional[list[dict]] = None
    nationality: Optional[str] = None
    travel_style: Optional[str] = None
    interests: Optional[list[str]] = None


class TranslationRequest(BaseModel):
    text: str
    target_language: str
    context: Optional[str] = None


class BatchTranslationRequest(BaseModel):
    texts: list[str]
    target_language: str
    context: Optional[str] = None


# ─────────────────────────────────────────
# Helper — construire UserContext
# ─────────────────────────────────────────

def build_context(
    language: str,
    nationality: Optional[str] = None,
    travel_style: Optional[str] = None,
    interests: Optional[list[str]] = None,
    budget: Optional[str] = None,
    trip_duration: Optional[int] = None,
    group_type: Optional[str] = None,
) -> UserContext:
    try:
        lang = Language(language)
    except ValueError:
        lang = Language.EN

    return UserContext(
        language=lang,
        nationality=nationality,
        travel_style=travel_style,
        interests=interests,
        budget=budget,
        trip_duration=trip_duration,
        group_type=group_type,
    )


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "wanderix-ai-engine"}


@app.post("/ai/itinerary")
async def generate_itinerary(
    req: ItineraryRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        context = build_context(
            language=req.language,
            nationality=req.nationality,
            travel_style=req.travel_style,
            interests=req.interests,
            budget=req.budget,
            trip_duration=req.trip_duration,
            group_type=req.group_type,
        )

        system_prompt = prompt_builder.build_system_prompt(context)
        user_prompt = prompt_builder.build_itinerary_prompt(req.destination, context)

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return {
            "destination": req.destination,
            "language": req.language,
            "itinerary": response.content[0].text,
        }

    except Exception as e:
        logger.error(f"Itinerary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/hotels/recommend")
async def recommend_hotels(
    req: HotelRecommendationRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        context = build_context(
            language=req.language,
            travel_style=req.travel_style,
            budget=req.budget,
            group_type=req.group_type,
        )

        system_prompt = prompt_builder.build_system_prompt(context)
        user_prompt = prompt_builder.build_hotel_recommendation_prompt(
            req.destination, req.hotels, context
        )

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return {
            "destination": req.destination,
            "language": req.language,
            "recommendations": response.content[0].text,
        }

    except Exception as e:
        logger.error(f"Hotel recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/guides/match")
async def match_guide(
    req: GuideMatchRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        context = build_context(
            language=req.language,
            interests=req.interests,
            travel_style=req.travel_style,
        )

        system_prompt = prompt_builder.build_system_prompt(context)
        user_prompt = prompt_builder.build_guide_matching_prompt(
            req.destination, req.guides, context
        )

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return {
            "destination": req.destination,
            "language": req.language,
            "match": response.content[0].text,
        }

    except Exception as e:
        logger.error(f"Guide match error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/chat")
async def chat(
    req: ChatRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        context = build_context(
            language=req.language,
            nationality=req.nationality,
            travel_style=req.travel_style,
            interests=req.interests,
        )

        system_prompt = prompt_builder.build_system_prompt(context)
        messages = prompt_builder.build_chat_prompt(
            user_message=req.message,
            destination=req.destination,
            context=context,
            conversation_history=req.conversation_history,
        )

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
        )

        return {
            "language": req.language,
            "reply": response.content[0].text,
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/translate")
async def translate(
    req: TranslationRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        lang = Language(req.target_language)
        translated = translation_layer.translate(req.text, lang, req.context)
        return {"translated": translated, "language": req.target_language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/translate/batch")
async def translate_batch(
    req: BatchTranslationRequest,
    _: str = Depends(verify_internal_key),
):
    try:
        lang = Language(req.target_language)
        results = translation_layer.translate_batch(req.texts, lang, req.context)
        return {"translations": results, "language": req.target_language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AVATAR ROUTES
from core.avatar_brain import AvatarBrain, AvatarGender, AvatarLanguage
from pydantic import BaseModel as PydanticModel

avatar_brain = AvatarBrain()

class AvatarChatReq(PydanticModel):
    message: str
    gender: str = 'female'
    language: str = 'en'
    destination: str = None
    conversation_history: list = []

@app.post('/avatar/chat')
async def avatar_chat(req: AvatarChatReq, _: str = Depends(verify_internal_key)):
    try:
        result = avatar_brain.respond(message=req.message, gender=AvatarGender(req.gender), language=AvatarLanguage(req.language), destination=req.destination, conversation_history=req.conversation_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/avatar/welcome')
async def avatar_welcome(gender: str = 'female', language: str = 'en', destination: str = None, _: str = Depends(verify_internal_key)):
    try:
        result = avatar_brain.welcome(gender=AvatarGender(gender), language=AvatarLanguage(language), destination=destination)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ─────────────────────────────────────────
# HOTEL SEARCH ROUTES (Booking.com)
# ─────────────────────────────────────────

from core.hotel_search import HotelSearchService
from pydantic import BaseModel as PydanticBaseModel

hotel_search = HotelSearchService()

class HotelSearchReq(PydanticBaseModel):
    destination: str
    checkin: str
    checkout: str
    adults: int = 2
    language: str = "en"
    currency: str = "USD"
    min_price: int = None
    max_price: int = None
    stars: int = None
    limit: int = 10

@app.post("/hotels/search")
async def search_hotels(
    req: HotelSearchReq,
    _: str = Depends(verify_internal_key),
):
    try:
        hotels = await hotel_search.search_hotels(
            destination=req.destination,
            checkin=req.checkin,
            checkout=req.checkout,
            adults=req.adults,
            language=req.language,
            currency=req.currency,
            min_price=req.min_price,
            max_price=req.max_price,
            stars=req.stars,
            limit=req.limit,
        )
        return {"hotels": hotels, "total": len(hotels), "source": "booking.com"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hotels/destination")
async def search_destination(
    query: str,
    language: str = "en",
    _: str = Depends(verify_internal_key),
):
    try:
        result = await hotel_search.search_destination(query, language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))