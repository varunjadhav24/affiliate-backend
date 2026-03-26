from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",
                                      case_sensitive=True, extra="ignore")
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/affiliate_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    GOOGLE_ADS_REFRESH_TOKEN: str = ""
    GOOGLE_ADS_LOGIN_CUSTOMER_ID: str = ""
    AMAZON_ACCESS_KEY: str = ""
    AMAZON_SECRET_KEY: str = ""
    AMAZON_PARTNER_TAG: str = ""
    AMAZON_HOST: str = "webservices.amazon.de"
    AMAZON_REGION: str = "eu-west-1"
    GA4_PROPERTY_ID: str = ""
    DNS_PROVIDER_API_KEY: str = ""
    DNS_BASE_DOMAIN: str = "example.com"
    SENTRY_DSN: str = ""
    SECRET_KEY: str = "change-me-in-production"

settings = Settings()
