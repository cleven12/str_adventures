"""
Utility to generate realistic sample content JSON for testing and local development.

This helps with rapid iteration on the import system without manual JSON creation.
Can be expanded with more realistic data generation.
"""

import random
from datetime import datetime


def generate_sample_tour(index: int = 1) -> dict:
    routes = ["Lemosho", "Machame", "Rongai", "Marangu", "Northern Circuit"]
    route = routes[index % len(routes)]

    return {
        "title": f"{6 + (index % 4)}-Day {route} Route Kilimanjaro",
        "slug": f"{6 + (index % 4)}-day-{route.lower().replace(' ', '-')}-route",
        "category": "Kilimanjaro Treks",
        "tour_type": "multi_day_trek",
        "place_name": "Mount Kilimanjaro, Tanzania",
        "duration_days": 6 + (index % 4),
        "difficulty": random.choice(["moderate", "challenging"]),
        "price_usd": 1450 + (index * 50),
        "excerpt": f"Classic {route} route with excellent acclimatization.",
        "description": f"<p>Experience the {route} route on Kilimanjaro.</p>",
        "is_active": True,
        "is_featured": index % 3 == 0,
        "tags": [route.lower().replace(" ", "-"), "kilimanjaro", "trekking"],
        "seo": {
            "meta_title": f"{6 + (index % 4)} Day {route} Route | Visit Kili",
            "meta_description": f"Book the {route} route. Small groups, expert guides.",
            "focus_keyword": f"{6 + (index % 4)} day {route.lower()} route kilimanjaro",
            "schema_type": "TouristTrip",
        },
        "inclusions": ["Professional guides", "Park fees", "Meals"],
        "exclusions": ["Flights", "Tips"],
        "content_blocks": [
            {"type": "heading", "heading": "Day 1", "content": "Arrival and briefing.", "order": 1},
            {"type": "paragraph", "content": "Meet your guide.", "order": 2},
        ],
        "seasonal_windows": [
            {"month_start": 1, "month_end": 3, "rating": "best"},
            {"month_start": 6, "month_end": 10, "rating": "best"},
        ],
        "gallery": [],
    }


def generate_sample_destination(index: int = 1) -> dict:
    parks = ["Serengeti", "Ngorongoro", "Tarangire", "Lake Manyara"]
    park = parks[index % len(parks)]

    return {
        "name": f"{park} National Park",
        "slug": f"{park.lower().replace(' ', '-')}-national-park",
        "category": "National Parks",
        "short_description": f"Iconic wildlife in {park}.",
        "description": f"<p>Explore {park}.</p>",
        "location_name": "Northern Tanzania",
        "altitude": "1500m",
        "best_time_to_visit": "June to October",
        "is_active": True,
        "seo": {
            "meta_title": f"{park} Safari | Visit Kili",
            "meta_description": f"Best {park} safari packages.",
            "focus_keyword": f"{park.lower()} national park safari",
        },
        "faqs": [
            {"question": f"What animals are in {park}?", "answer": "The Big Five.", "order": 1}
        ],
        "gallery": [],
    }
