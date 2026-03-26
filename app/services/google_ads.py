from app.core.config import settings

class GoogleAdsService:
    def __init__(self):
        self.developer_token = settings.GOOGLE_ADS_DEVELOPER_TOKEN

    def create_campaign(self, niche_id, campaign_name, daily_budget_eur, keywords, geo_target="DE"):
        raise NotImplementedError("create_campaign not yet implemented")

    def pause_campaign(self, google_campaign_id):
        raise NotImplementedError("pause_campaign not yet implemented")

    def resume_campaign(self, google_campaign_id):
        raise NotImplementedError("resume_campaign not yet implemented")

    def get_campaign_metrics(self, google_campaign_id):
        raise NotImplementedError("get_campaign_metrics not yet implemented")
