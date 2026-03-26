import urllib.parse
from app.core.config import settings

class AmazonPAService:
    def __init__(self):
        self.access_key = settings.AMAZON_ACCESS_KEY
        self.secret_key = settings.AMAZON_SECRET_KEY
        self.partner_tag = settings.AMAZON_PARTNER_TAG
        self.host = settings.AMAZON_HOST

    def search_products(self, keywords: str, item_count: int = 20) -> list:
        raise NotImplementedError("search_products not yet implemented")

    def get_product_details(self, asin: str) -> dict:
        raise NotImplementedError("get_product_details not yet implemented")

    def generate_affiliate_link(self, asin: str) -> str:
        params = urllib.parse.urlencode({"tag": self.partner_tag, "linkCode": "ogi"})
        return f"https://www.amazon.de/dp/{asin}?{params}"
