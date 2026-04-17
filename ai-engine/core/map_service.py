import os
import httpx
from typing import Optional


# ─────────────────────────────────────────
# Coordonnées des destinations
# ─────────────────────────────────────────

DESTINATIONS = {
    "marrakech": {"lat": 31.6295, "lng": -7.9811, "zoom": 13, "country": "Morocco"},
    "paris": {"lat": 48.8566, "lng": 2.3522, "zoom": 13, "country": "France"},
    "dubai": {"lat": 25.2048, "lng": 55.2708, "zoom": 12, "country": "UAE"},
    "barcelona": {"lat": 41.3851, "lng": 2.1734, "zoom": 13, "country": "Spain"},
    "tokyo": {"lat": 35.6762, "lng": 139.6503, "zoom": 13, "country": "Japan"},
    "london": {"lat": 51.5074, "lng": -0.1278, "zoom": 13, "country": "UK"},
    "new york": {"lat": 40.7128, "lng": -74.0060, "zoom": 13, "country": "USA"},
    "rome": {"lat": 41.9028, "lng": 12.4964, "zoom": 13, "country": "Italy"},
    "amsterdam": {"lat": 52.3676, "lng": 4.9041, "zoom": 13, "country": "Netherlands"},
    "casablanca": {"lat": 33.5731, "lng": -7.5898, "zoom": 13, "country": "Morocco"},
    "istanbul": {"lat": 41.0082, "lng": 28.9784, "zoom": 13, "country": "Turkey"},
    "bangkok": {"lat": 13.7563, "lng": 100.5018, "zoom": 13, "country": "Thailand"},
    "singapore": {"lat": 1.3521, "lng": 103.8198, "zoom": 13, "country": "Singapore"},
    "sydney": {"lat": -33.8688, "lng": 151.2093, "zoom": 13, "country": "Australia"},
    "cairo": {"lat": 30.0444, "lng": 31.2357, "zoom": 13, "country": "Egypt"},
    "mumbai": {"lat": 19.0760, "lng": 72.8777, "zoom": 13, "country": "India"},
    "beijing": {"lat": 39.9042, "lng": 116.4074, "zoom": 13, "country": "China"},
    "seoul": {"lat": 37.5665, "lng": 126.9780, "zoom": 13, "country": "South Korea"},
    "mexico city": {"lat": 19.4326, "lng": -99.1332, "zoom": 13, "country": "Mexico"},
    "rio de janeiro": {"lat": -22.9068, "lng": -43.1729, "zoom": 13, "country": "Brazil"},
}


class MapService:
    """
    Service Map IA — Carte interactive avec hôtels en temps réel
    """

    # ─────────────────────────────────────
    # Obtenir les données de la carte
    # ─────────────────────────────────────

    async def get_map_data(
        self,
        destination: str,
        checkin: str,
        checkout: str,
        language: str = "en",
        currency: str = "USD",
        limit: int = 20,
    ) -> dict:
        try:
            dest_key = destination.lower()
            dest_info = DESTINATIONS.get(dest_key, {
                "lat": 31.6295,
                "lng": -7.9811,
                "zoom": 13,
                "country": "Morocco"
            })

            # Chercher les hôtels via Booking.com
            from core.hotel_search import HotelSearchService
            hotel_service = HotelSearchService()

            hotels = await hotel_service.search_hotels(
                destination=destination,
                checkin=checkin,
                checkout=checkout,
                language=language,
                currency=currency,
                limit=limit,
            )

            # Formater pour la carte
            markers = []
            for hotel in hotels:
                if hotel.get("latitude") and hotel.get("longitude"):
                    markers.append({
                        "id": hotel.get("id"),
                        "name": hotel.get("name"),
                        "lat": float(hotel.get("latitude")),
                        "lng": float(hotel.get("longitude")),
                        "stars": hotel.get("stars", 0),
                        "rating": hotel.get("rating", 0),
                        "price": hotel.get("price_per_night", 0),
                        "currency": hotel.get("currency", currency),
                        "address": hotel.get("address", ""),
                        "image": hotel.get("cover_image", ""),
                        "url": hotel.get("url", ""),
                        "color": self._get_marker_color(hotel.get("rating", 0)),
                    })

            return {
                "destination": destination,
                "center": {
                    "lat": dest_info["lat"],
                    "lng": dest_info["lng"],
                    "zoom": dest_info["zoom"],
                },
                "country": dest_info.get("country", ""),
                "markers": markers,
                "total": len(markers),
                "language": language,
                "currency": currency,
            }

        except Exception as e:
            return {"error": str(e), "destination": destination}

    # ─────────────────────────────────────
    # Obtenir toutes les destinations
    # ─────────────────────────────────────

    def get_all_destinations(self) -> list:
        return [
            {
                "name": name.title(),
                "key": name,
                "lat": info["lat"],
                "lng": info["lng"],
                "country": info["country"],
            }
            for name, info in DESTINATIONS.items()
        ]

    # ─────────────────────────────────────
    # Helper — couleur du marker
    # ─────────────────────────────────────

    def _get_marker_color(self, rating: float) -> str:
        if rating >= 9.0:
            return "#22c55e"  # vert
        elif rating >= 8.0:
            return "#3b82f6"  # bleu
        elif rating >= 7.0:
            return "#f59e0b"  # orange
        else:
            return "#6b7280"  # gris