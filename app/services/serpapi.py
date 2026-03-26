import requests
from app.core.config import settings

class SerpAPIService:
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY

    def search_keywords(self, query: str, country: str = "de") -> list:
        # TODO: implement full keyword extraction
        params = {"engine": "google", "q": query, "gl": country, "hl": "de", "api_key": self.api_key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("organic_results", [])

    def get_trends(self, keyword: str, country: str = "DE") -> list:
        # TODO: implement trends parsing
        params = {"engine": "google_trends", "q": keyword, "geo": country, "api_key": self.api_key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("interest_over_time", {}).get("timeline_data", [])
