import os
import httpx
from typing import Optional


RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "ca88515025mshadb79cf1132fd81p1af5abjsned1dc604fc7f")
RAPIDAPI_HOST = "apidojo-booking-v1.p.rapidapi.com"
BASE_URL = "https://apidojo-booking-v1.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

# Coordonnées des destinations principales
DESTINATION_COORDS = {
    "marrakech": {"bbox": "31.5,31.7,-8.1,-7.8"},
    "paris": {"bbox": "48.8,48.9,2.2,2.4"},
    "dubai": {"bbox": "25.0,25.3,55.1,55.4"},
    "barcelona": {"bbox": "41.3,41.5,2.1,2.2"},
    "tokyo": {"bbox": "35.6,35.8,139.6,139.8"},
    "london": {"bbox": "51.4,51.6,-0.2,0.0"},
    "new york": {"bbox": "40.6,40.8,-74.1,-73.9"},
    "rome": {"bbox": "41.8,42.0,12.4,12.6"},
    "amsterdam": {"bbox": "52.3,52.4,4.8,5.0"},
    "casablanca": {"bbox": "33.5,33.6,-7.7,-7.5"},
}


class HotelSearchService:

    async def search_hotels(
        self,
        destination: str,
        checkin: str,
        checkout: str,
        adults: int = 2,
        language: str = "en",
        currency: str = "USD",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        stars: Optional[int] = None,
        limit: int = 10,
    ) -> list:
        try:
            dest_key = destination.lower()
            coords = DESTINATION_COORDS.get(dest_key, {"bbox": "31.5,31.7,-8.1,-7.8"})
            bbox = coords["bbox"]

            params = {
                "room_qty": 1,
                "guest_qty": adults,
                "bbox": bbox,
                "search_id": "none",
                "languagecode": language,
                "order_by": "popularity",
                "offset": 0,
                "arrival_date": checkin,
                "departure_date": checkout,
                "price_filter_currencycode": currency,
            }

            if stars:
                params["categories_filter"] = f"class::{stars}"
            if min_price:
                params["price_filter_min"] = min_price
            if max_price:
                params["price_filter_max"] = max_price

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BASE_URL}/properties/list-by-map",
                    headers=HEADERS,
                    params=params,
                    timeout=15,
                )
                data = response.json()

            hotels = (data.get("result") or data.get("hotels") or [])[:limit]
            return [self._format_hotel(h, currency) for h in hotels]

        except Exception as e:
            print(f"search_hotels error: {e}")
            return []

    async def search_destination(self, query: str, language: str = "en") -> dict:
        dest_key = query.lower()
        coords = DESTINATION_COORDS.get(dest_key)
        if coords:
            return {"name": query, "bbox": coords["bbox"], "found": True}
        return {"name": query, "found": False}

    def _format_hotel(self, hotel: dict, currency: str = "USD") -> dict:
        price_info = hotel.get("price_breakdown", {})
        price = price_info.get("gross_price", 0) or hotel.get("min_total_price", 0)
        return {
            "id": str(hotel.get("hotel_id", "")),
            "name": hotel.get("hotel_name_trans", hotel.get("hotel_name", "")),
            "stars": int(hotel.get("class", 0)),
            "rating": float(hotel.get("review_score", 0)),
            "review_count": int(hotel.get("review_nr", 0)),
            "price_per_night": round(float(price), 2) if price else 0,
            "currency": hotel.get("currency_code", currency),
            "city": hotel.get("city_trans", ""),
            "country": hotel.get("country_trans", ""),
            "address": hotel.get("address_trans", hotel.get("address", "")),
            "latitude": hotel.get("latitude"),
            "longitude": hotel.get("longitude"),
            "cover_image": hotel.get("main_photo_url", ""),
            "url": hotel.get("url", ""),
            "is_available": True,
            "source": "booking.com",
        }