#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"backend"))
from app.services.terraform_parser import parse_terraform
from app.services.cost_calculator import calculate
from app.services.budget_policy import evaluate_budget
from app.services.pricing_service import PricingService,PricingUnavailable
def main():
 p=argparse.ArgumentParser();p.add_argument("--terraform",required=True);p.add_argument("--budget",type=float,required=True);p.add_argument("--region",default="us-east-1");p.add_argument("--scenario",choices=["low","medium","high"],default="high");p.add_argument("--output",default="cost-report.json");a=p.parse_args()
 try:
  pricing=PricingService();parsed=parse_terraform(Path(a.terraform).read_text(encoding="utf-8"),a.region);cost=calculate(parsed["resources"],a.region,a.scenario,pricing=pricing);policy=evaluate_budget(cost["total_monthly_cost"],a.budget);report={**cost,"budget_policy":policy,"unsupported_warnings":parsed["unsupported_warnings"],"pricing_effective_date":pricing.effective_date};Path(a.output).write_text(json.dumps(report,indent=2),encoding="utf-8")
  print(f"CloudScope Lite Cost Check\nRegion: {a.region}\nSupported resources: {len(cost['resources'])}\nUnsupported resources: {len(parsed['unsupported_warnings'])}\nEstimated monthly cost: ${float(cost['total_monthly_cost']):.2f}\nMonthly budget: ${a.budget:.2f}\nBudget usage: {policy['budget_usage_percentage']:.2f}%\nPolicy result: {policy['status']}\nPricing effective date: {pricing.effective_date}\nReport generated: {a.output}")
  return 1 if policy["status"]=="FAIL" else 0
 except (ValueError,OSError,PricingUnavailable) as e: print(f"CloudScope input/pricing error: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())

