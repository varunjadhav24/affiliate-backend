from app.core.config import settings

class GA4Service:
    def __init__(self):
        self.property_id = settings.GA4_PROPERTY_ID

    def get_traffic(self, property_id, subdomain, start_date="30daysAgo", end_date="today"):
        raise NotImplementedError("get_traffic not yet implemented")

    def get_conversions(self, property_id=None, start_date="30daysAgo", end_date="today"):
        raise NotImplementedError("get_conversions not yet implemented")
