from decimal import Decimal, ROUND_HALF_UP
from .pricing_service import PricingService
HOURS={"low":176,"medium":352,"high":730}
D=lambda value: Decimal(str(value))
def money(value): return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

UNITS={"aws_instance":"USD/hour (compute) + USD/GB-month (root volume)","aws_ebs_volume":"USD/GB-month","aws_s3_bucket":"USD/GB-month","aws_db_instance":"USD/hour (instance) + USD/GB-month (storage)"}

def calculate(resources, region, scenario="high", overrides=None, pricing=None):
    pricing=pricing or PricingService(); overrides=overrides or {}; rows=[]
    hours=D(overrides.get("operating_hours",HOURS[scenario]))
    for resource in resources:
        a=resource["attributes"]; kind=resource["resource_type"]
        if kind=="aws_instance":
            rate=D(pricing.rate(region,"ec2",a.get("instance_type"))); size=D(a.get("root_volume_size_gb",8)); storage=D(pricing.rate(region,"ebs","gp3")); cost=rate*hours+size*storage; formula=f"{rate} x {hours} hours + {size} GB x {storage}"
        elif kind=="aws_ebs_volume":
            size=D(overrides.get("ebs_storage_gb",a.get("size"))); rate=D(pricing.rate(region,"ebs",a.get("type","gp3"))); cost=size*rate; formula=f"{size} GB x {rate}"
        elif kind=="aws_s3_bucket":
            size=D(overrides.get("s3_storage_gb",a.get("estimated_storage_gb",0))); rate=D(pricing.rate(region,"s3","STANDARD")); cost=size*rate; formula=f"{size} GB x {rate}"; resource["warnings"].append({"field":"pricing","message":"S3 requests and data transfer are excluded."})
        else:
            rate=D(pricing.rate(region,"rds",a.get("instance_class"))); size=D(overrides.get("rds_storage_gb",a.get("allocated_storage"))); storage=D(pricing.rate(region,"rds","storage_gp3")); cost=rate*hours+size*storage; formula=f"{rate} x {hours} hours + {size} GB x {storage}"
        rows.append({**resource,"pricing_rate":str(rate),"pricing_unit":UNITS[kind],"quantity":str(hours if kind in {"aws_instance","aws_db_instance"} else size),"formula":formula,"estimated_cost":str(money(cost)),"assumptions":[f"{scenario} workload"],"warnings":resource["warnings"]})
    return {"resources":rows,"total_monthly_cost":str(money(sum((D(r["estimated_cost"]) for r in rows),D(0))))}

def compare_scenarios(resources,region,pricing=None): return {s:calculate(resources,region,s,pricing=pricing) for s in HOURS}

