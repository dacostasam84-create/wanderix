import os
import logging
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from core.prompt_builder import PromptBuilder, UserContext, Language
from core.translation_layer import TranslationLayer
from core.avatar_brain import AvatarBrain, AvatarGender, AvatarLanguage
from core.hotel_search import HotelSearchService
from core.universal_language import UniversalLanguageService
from core.did_avatar import DIDAvatarService
from core.voice_ai import VoiceAIService
from core.vision_ai import VisionAIService
from core.map_service import MapService
from core.flights_search import FlightsSearchService
from core.cars_search import CarsSearchService
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wanderix AI Engine", description="Cerveau IA multilingue de Wanderix", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

prompt_builder = PromptBuilder()
translation_layer = TranslationLayer()
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
avatar_brain = AvatarBrain()
hotel_search = HotelSearchService()
universal_lang = UniversalLanguageService()
did_service = DIDAvatarService()
voice_service = VoiceAIService()
vision_service = VisionAIService()
map_service = MapService()
flights_service = FlightsSearchService()
cars_service = CarsSearchService()
def verify_internal_key(x_internal_key: str = Header(...)):
    expected = os.environ.get("INTERNAL_API_KEY")
    if x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_internal_key

def build_context(language, nationality=None, travel_style=None, interests=None, budget=None, trip_duration=None, group_type=None):
    try:
        lang = Language(language)
    except ValueError:
        lang = Language.EN
    return UserContext(language=lang, nationality=nationality, travel_style=travel_style, interests=interests, budget=budget, trip_duration=trip_duration, group_type=group_type)

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

class AvatarChatReq(BaseModel):
    message: str
    gender: str = "female"
    language: str = "en"
    destination: Optional[str] = None
    conversation_history: list = []

class HotelSearchReq(BaseModel):
    destination: str
    checkin: str
    checkout: str
    adults: int = 2
    language: str = "en"
    currency: str = "USD"
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    stars: Optional[int] = None
    limit: int = 10

class TranslateUniversalReq(BaseModel):
    text: str
    target_language: str
    context: Optional[str] = None
    source_language: Optional[str] = None

class DetectLanguageReq(BaseModel):
    text: str

class RespondInLanguageReq(BaseModel):
    user_message: str
    system_prompt: str = "You are Wanderix AI travel assistant."
    detected_language: Optional[str] = None

class DIDChatReq(BaseModel):
    message: str
    gender: str = "female"
    language: str = "en"
    destination: Optional[str] = None
    conversation_history: list = []

class DIDWelcomeReq(BaseModel):
    gender: str = "female"
    language: str = "en"
    destination: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "wanderix-ai-engine"}

@app.get("/map", response_class=HTMLResponse)
async def map_page():
    map_path = os.path.join(os.path.dirname(__file__), "static", "map.html")
    with open(map_path, "r", encoding="utf-8") as f:
        return f.read()
@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    landing_path = os.path.join(os.path.dirname(__file__), "..", "landing", "index.html")
    with open(landing_path, "r", encoding="utf-8") as f:
        return f.read()
@app.post("/ai/itinerary")
async def generate_itinerary(req: ItineraryRequest, _: str = Depends(verify_internal_key)):
    try:
        context = build_context(req.language, req.nationality, req.travel_style, req.interests, req.budget, req.trip_duration, req.group_type)
        response = anthropic_client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000, system=prompt_builder.build_system_prompt(context), messages=[{"role": "user", "content": prompt_builder.build_itinerary_prompt(req.destination, context)}])
        return {"destination": req.destination, "language": req.language, "itinerary": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/hotels/recommend")
async def recommend_hotels(req: HotelRecommendationRequest, _: str = Depends(verify_internal_key)):
    try:
        context = build_context(req.language, travel_style=req.travel_style, budget=req.budget, group_type=req.group_type)
        response = anthropic_client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000, system=prompt_builder.build_system_prompt(context), messages=[{"role": "user", "content": prompt_builder.build_hotel_recommendation_prompt(req.destination, req.hotels, context)}])
        return {"destination": req.destination, "language": req.language, "recommendations": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/guides/match")
async def match_guide(req: GuideMatchRequest, _: str = Depends(verify_internal_key)):
    try:
        context = build_context(req.language, interests=req.interests, travel_style=req.travel_style)
        response = anthropic_client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000, system=prompt_builder.build_system_prompt(context), messages=[{"role": "user", "content": prompt_builder.build_guide_matching_prompt(req.destination, req.guides, context)}])
        return {"destination": req.destination, "language": req.language, "match": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/chat")
async def chat(req: ChatRequest, _: str = Depends(verify_internal_key)):
    try:
        context = build_context(req.language, req.nationality, req.travel_style, req.interests)
        messages = prompt_builder.build_chat_prompt(user_message=req.message, destination=req.destination, context=context, conversation_history=req.conversation_history)
        response = anthropic_client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000, system=prompt_builder.build_system_prompt(context), messages=messages)
        return {"language": req.language, "reply": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/translate")
async def translate(req: TranslationRequest, _: str = Depends(verify_internal_key)):
    try:
        lang = Language(req.target_language)
        translated = translation_layer.translate(req.text, lang, req.context)
        return {"translated": translated, "language": req.target_language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/translate/batch")
async def translate_batch(req: BatchTranslationRequest, _: str = Depends(verify_internal_key)):
    try:
        lang = Language(req.target_language)
        results = translation_layer.translate_batch(req.texts, lang, req.context)
        return {"translations": results, "language": req.target_language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/chat")
async def avatar_chat(req: AvatarChatReq, _: str = Depends(verify_internal_key)):
    try:
        result = avatar_brain.respond(message=req.message, gender=AvatarGender(req.gender), language=AvatarLanguage(req.language), destination=req.destination, conversation_history=req.conversation_history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar/welcome")
async def avatar_welcome(gender: str = "female", language: str = "en", destination: str = None, _: str = Depends(verify_internal_key)):
    try:
        result = avatar_brain.welcome(gender=AvatarGender(gender), language=AvatarLanguage(language), destination=destination)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hotels/search")
async def search_hotels(req: HotelSearchReq, _: str = Depends(verify_internal_key)):
    try:
        hotels = await hotel_search.search_hotels(destination=req.destination, checkin=req.checkin, checkout=req.checkout, adults=req.adults, language=req.language, currency=req.currency, min_price=req.min_price, max_price=req.max_price, stars=req.stars, limit=req.limit)
        return {"hotels": hotels, "total": len(hotels), "source": "booking.com"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hotels/destination")
async def search_destination(query: str, language: str = "en", _: str = Depends(verify_internal_key)):
    try:
        result = await hotel_search.search_destination(query, language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/languages")
async def get_languages(_: str = Depends(verify_internal_key)):
    langs = universal_lang.get_supported_languages()
    return {"languages": langs, "total": len(langs)}
@app.post("/language/detect")
async def detect_language(req: DetectLanguageReq, _: str = Depends(verify_internal_key)):
    try:
        return await universal_lang.detect_language(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/language/translate")
async def translate_universal(req: TranslateUniversalReq, _: str = Depends(verify_internal_key)):
    try:
        return await universal_lang.translate(text=req.text, target_language=req.target_language, context=req.context, source_language=req.source_language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/language/respond")
async def respond_in_language(req: RespondInLanguageReq, _: str = Depends(verify_internal_key)):
    try:
        return await universal_lang.respond_in_language(user_message=req.user_message, system_prompt=req.system_prompt, detected_language=req.detected_language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/avatar/video/chat")
async def avatar_video_chat(req: DIDChatReq, _: str = Depends(verify_internal_key)):
    try:
        return await did_service.avatar_chat_with_video(message=req.message, gender=req.gender, language=req.language, destination=req.destination, conversation_history=req.conversation_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avatar/video/welcome")
async def avatar_video_welcome(req: DIDWelcomeReq, _: str = Depends(verify_internal_key)):
    try:
        return await did_service.welcome_with_video(gender=req.gender, language=req.language, destination=req.destination)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/avatar/video/status/{talk_id}")
async def avatar_video_status(talk_id: str, _: str = Depends(verify_internal_key)):
    try:
        return await did_service.get_video_status(talk_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...), language: str = Form(default="auto"), _: str = Depends(verify_internal_key)):
    try:
        audio_data = await file.read()
        return await voice_service.speech_to_text(audio_data=audio_data, language=language if language != "auto" else None, filename=file.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/speak")
async def speak(text: str = Form(...), language: str = Form(default="en"), voice: str = Form(default="nova"), _: str = Depends(verify_internal_key)):
    try:
        audio_bytes = await voice_service.text_to_speech(text=text, voice=voice, language=language)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS failed")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/analyze")
async def analyze_photo(file: UploadFile = File(...), language: str = Form(default="en"), _: str = Depends(verify_internal_key)):
    try:
        image_data = await file.read()
        return await vision_service.analyze_travel_photo(image_data=image_data, language=language, media_type=file.content_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/hotel")
async def identify_hotel(file: UploadFile = File(...), language: str = Form(default="en"), _: str = Depends(verify_internal_key)):
    try:
        image_data = await file.read()
        return await vision_service.identify_hotel(image_data=image_data, language=language, media_type=file.content_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision/describe")
async def describe_photo(file: UploadFile = File(...), language: str = Form(default="en"), style: str = Form(default="inspiring"), _: str = Depends(verify_internal_key)):
    try:
        image_data = await file.read()
        return await vision_service.generate_photo_description(image_data=image_data, language=language, media_type=file.content_type or "image/jpeg", style=style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/map/data")
async def get_map_data(destination: str, checkin: str, checkout: str, language: str = "en", currency: str = "USD", limit: int = 20, _: str = Depends(verify_internal_key)):
    try:
        return await map_service.get_map_data(destination=destination, checkin=checkin, checkout=checkout, language=language, currency=currency, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/map/destinations")
async def get_destinations(_: str = Depends(verify_internal_key)):
    try:
        return {"destinations": map_service.get_all_destinations(), "total": len(map_service.get_all_destinations())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/flights/search")
async def search_flights(
    origin: str,
    destination: str,
    date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    cabin_class: str = "economy",
    currency: str = "USD",
    language: str = "en",
    _: str = Depends(verify_internal_key),
):
    try:
        return await flights_service.search_flights(
            origin=origin,
            destination=destination,
            date=date,
            return_date=return_date,
            adults=adults,
            cabin_class=cabin_class,
            currency=currency,
            language=language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        returts(
            origin=origin,
            destination=destination,
            date=date,
            return_date=return_date,
            adults=adults,
            cabin_class=cabin_class,
            currency=currency,
            language=language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/flights/airports")
async def get_airports(_: str = Depends(verify_internal_key)):
    return {"airports": flights_service.get_airports(), "total": len(flights_service.get_airports())}

@app.get("/flights/calendar")
async def get_price_calendar(
    origin: str,
    destination: str,
    year: int,
    month: int,
    currency: str = "USD",
    _: str = Depends(verify_internal_key),
):
    try:
        return await flights_service.get_price_calendar(
            origin=origin,
            destination=destination,
            year=year,
            month=month,
            currency=currency,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cars/search")
async def search_cars(
    pickup_location: str,
    pickup_date: str,
    pickup_time: str,
    dropoff_date: str,
    dropoff_time: str,
    dropoff_location: Optional[str] = None,
    driver_age: int = 30,
    currency: str = "USD",
    _: str = Depends(verify_internal_key),
):
    try:
        return await cars_service.search_cars(
            pickup_location=pickup_location,
            pickup_date=pickup_date,
            pickup_time=pickup_time,
            dropoff_date=dropoff_date,
            dropoff_time=dropoff_time,
            dropoff_location=dropoff_location,
            driver_age=driver_age,
            currency=currency,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
    