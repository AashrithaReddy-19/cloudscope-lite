#!/usr/bin/env python3
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

CATALOGUE=Path(__file__).resolve().parents[1]/"pricing"/"aws_pricing_catalogue.json"
class DuplicateKey(ValueError): pass
def unique_pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise DuplicateKey(f"Duplicate JSON key: {key}")
        result[key]=value
    return result
def validate(path=CATALOGUE):
    errors=[]
    try: data=json.loads(Path(path).read_text(encoding="utf-8"),object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError,DuplicateKey) as exc: return [str(exc)]
    for field in ("effective_date","currency","source","source_references"):
        if not data.get(field): errors.append(f"Missing {field}")
    for region,services in data.get("regions",{}).items():
        for service,entries in services.items():
            for resource,value in entries.items():
                try: price=Decimal(str(value))
                except InvalidOperation: errors.append(f"Non-numeric price: {region}/{service}/{resource}");continue
                if price<0: errors.append(f"Negative price: {region}/{service}/{resource}")
                if price==0: errors.append(f"Zero price is not explicitly marked free: {region}/{service}/{resource}")
    return errors
if __name__=="__main__":
    problems=validate()
    if problems:
        print("Pricing catalogue INVALID");print("\n".join(f"- {x}" for x in problems));raise SystemExit(1)
    data=json.loads(CATALOGUE.read_text());count=sum(len(entries) for services in data["regions"].values() for entries in services.values());print(f"Pricing catalogue VALID: {count} priced combinations, {len(data['regions'])} regions, {data['currency']}, effective {data['effective_date']}")
