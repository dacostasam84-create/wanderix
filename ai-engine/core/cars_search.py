import os
import httpx
from typing import Optional

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "ca88515025mshadb79cf1132fd81p1af5abjsned1dc604fc7f")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "booking-com15.p.rapidapi.com",
}

BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1/cars"

CITY_COORDS = {
    "marrakech": {"lat": 31.6295, "lng": -7.9811},
    "casablanca": {"lat": 33.5731, "lng": -7.5898},
    "paris": {"lat": 48.8566, "lng": 2.3522},
    "london": {"lat": 51.5074, "lng": -0.1278},
    "dubai": {"lat": 25.2048, "lng": 55.2708},
    "new york": {"lat": 40.6397, "lng": -73.7792},
    "barcelona": {"lat": 41.3851, "lng": 2.1734},
    "tokyo": {"lat": 35.6762, "lng": 139.6503},
    "amsterdam": {"lat": 52.3676, "lng": 4.9041},
    "rome": {"lat": 41.9028, "lng": 12.4964},
    "istanbul": {"lat": 41.0082, "lng": 28.9784},
    "bangkok": {"lat": 13.7563, "lng": 100.5018},
    "singapore": {"lat": 1.3521, "lng": 103.8198},
    "sydney": {"lat": -33.8688, "lng": 151.2093},
    "cairo": {"lat": 30.0444, "lng": 31.2357},
    "madrid": {"lat": 40.4168, "lng": -3.7038},
    "frankfurt": {"lat": 50.0379, "lng": 8.5622},
}


class CarsSearchService:

    async def search_cars(self, pickup_location: str, pickup_date: str, pickup_time: str, dropoff_date: str, dropoff_time: str, dropoff_location: Optional[str] = None, driver_age: int = 30, currency: str = "USD") -> dict:
        try:
            coords = CITY_COORDS.get(pickup_location.lower())
            if not coords:
                return {"cars": [], "error": f"Location not found: {pickup_location}"}

            pickup_lat = coords["lat"]
            pickup_lng = coords["lng"]
            drop_coords = CITY_COORDS.get((dropoff_location or pickup_location).lower(), coords)
            dropoff_lat = drop_coords["lat"]
            dropoff_lng = drop_coords["lng"]

            params = {
                "pick_up_latitude": pickup_lat,
                "pick_up_longitude": pickup_lng,
                "drop_off_latitude": dropoff_lat,
                "drop_off_longitude": dropoff_lng,
                "pick_up_date": pickup_date,
                "drop_off_date": dropoff_date,
                "pick_up_time": pickup_time,
                "drop_off_time": dropoff_time,
                "driver_age": driver_age,
                "currency_code": currency,
                "location": "US",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{BASE_URL}/searchCarRentals",
                    headers=HEADERS,
                    params=params,
                    timeout=20,
                )
                data = response.json()

            if not data.get("status"):
                return {"cars": [], "error": data.get("message", "No cars found"), "raw": data}

            vehicles = data.get("data", {}).get("search_results", [])
            cars = []

            for vehicle in vehicles[:10]:
                vehicle_info = vehicle.get("vehicle_info", {})
                pricing = vehicle.get("pricing_info", {})
                supplier = vehicle.get("supplier_info", {})
                cars.append({
                    "id": vehicle.get("vehicle_id", ""),
                    "name": vehicle_info.get("v_name", ""),
                    "category": vehicle_info.get("category", ""),
                    "seats": vehicle_info.get("seats", 5),
                    "transmission": vehicle_info.get("transmission", "automatic"),
                    "air_conditioning": vehicle_info.get("air_con", True),
                    "image": vehicle_info.get("img_url", ""),
                    "price_per_day": pricing.get("drive_away_price", 0),
                    "total_price": pricing.get("base_price", 0),
                    "currency": currency,
                    "supplier": supplier.get("name", ""),
                    "rating": supplier.get("rating", 0),
                    "free_cancellation": vehicle.get("free_cancellation", False),
                    "pickup_location": pickup_location,
                })

            cars.sort(key=lambda x: x["price_per_day"])

            return {
                "cars": cars,
                "total": len(cars),
                "pickup_location": pickup_location,
                "pickup_date": pickup_date,
                "dropoff_date": dropoff_date,
                "currency": currency,
                "source": "booking.com",
            }

        except Exception as e:
            return {"cars": [], "error": str(e)}