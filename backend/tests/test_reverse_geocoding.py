import asyncio

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="resilience-ai")

async def get_place_name(
    latitude: float,
    longitude: float,
) -> str | None:
    location = await asyncio.to_thread(
        geolocator.reverse,
        (latitude, longitude),
    )

    return getattr(location, "address", None) if location else None

async def main():
    # Example coordinates: San Francisco
    latitude = 37.7749
    longitude = -122.4194

    place_name = await get_place_name(
        latitude,
        longitude,
    )

    if place_name:
        print("Place name:")
        print(place_name)
    else:
        print("Failed to find place name")


if __name__ == "__main__":
    asyncio.run(main())