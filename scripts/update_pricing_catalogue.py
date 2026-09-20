#!/usr/bin/env python3
"""Import normalized AWS Price List API JSON. This script never guesses absent prices."""
import argparse,json
from datetime import date
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("input",help="Downloaded/normalized JSON from the official AWS Price List API");p.add_argument("--output",default="pricing/aws_pricing_catalogue.json");a=p.parse_args();data=json.loads(Path(a.input).read_text())
 for key in ("currency","regions"): 
  if key not in data: raise SystemExit(f"Missing required key: {key}")
 data["effective_date"]=data.get("effective_date",date.today().isoformat());data["source"]="AWS Price List API: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json";Path(a.output).write_text(json.dumps(data,indent=2)+"\n")
if __name__=="__main__":main()

