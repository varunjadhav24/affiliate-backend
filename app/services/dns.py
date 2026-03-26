from app.core.config import settings

class DNSService:
    def __init__(self):
        self.api_key = settings.DNS_PROVIDER_API_KEY
        self.base_domain = settings.DNS_BASE_DOMAIN

    def create_subdomain(self, name: str, target_ip: str = "127.0.0.1") -> dict:
        raise NotImplementedError("create_subdomain not yet implemented")

    def delete_subdomain(self, name: str) -> bool:
        raise NotImplementedError("delete_subdomain not yet implemented")
