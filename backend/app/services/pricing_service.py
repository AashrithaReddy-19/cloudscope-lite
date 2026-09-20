import json
from pathlib import Path

class PricingUnavailable(ValueError): pass
CATALOGUE = Path(__file__).resolve().parents[3] / "pricing" / "aws_pricing_catalogue.json"

class PricingService:
    def __init__(self, path=CATALOGUE): self.data=json.loads(Path(path).read_text(encoding="utf-8"))
    @property
    def effective_date(self): return self.data["effective_date"]
    @property
    def currency(self): return self.data["currency"]
    @property
    def source(self): return self.data["source"]
    def regions(self): return list(self.data["regions"])
    def rate(self, region, service, key):
        value=self.data.get("regions",{}).get(region,{}).get(service,{}).get(key)
        if value is None: raise PricingUnavailable(f"Pricing unavailable for {service} {key} in {region}; refresh the catalogue.")
        return value

