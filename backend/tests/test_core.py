import json
from pathlib import Path
import pytest
from app.db import build_database_url
from app.services.terraform_parser import parse_terraform,TerraformParseError,validate_upload
from app.services.budget_policy import evaluate_budget
from app.services.cost_calculator import calculate
from app.services.pricing_service import PricingService,PricingUnavailable
from app.services.recommendation_engine import recommend
from app.services.anomaly_detection import detect
from app.services.forecasting import forecast
TF='resource "aws_instance" "web" { instance_type = "t3.micro" root_volume_size_gb = 8 }'
class Prices:
    rates={("ec2","t3.micro"):"0.01",("ebs","gp3"):"0.08",("s3","STANDARD"):"0.023",("rds","db.t3.micro"):"0.02",("rds","storage_gp3"):"0.115"}
    def rate(self,region,service,key):
        if (service,key) not in self.rates: raise PricingUnavailable("missing")
        return self.rates[(service,key)]
def resource(kind,name="x",**attrs): return {"resource_type":kind,"resource_name":name,"region":"us-east-1","attributes":attrs,"warnings":[]}
def history(n=12): return [{"date":f"2025-{i+1:02}-01","cost":10+i*2} for i in range(n)]
def test_valid_parse(): assert parse_terraform(TF)["resources"][0]["resource_name"]=="web"
def test_invalid_hcl():
    with pytest.raises(TerraformParseError): parse_terraform("resource {")
def test_unsupported_resource(): assert parse_terraform('resource "aws_lambda_function" "x" {}')["unsupported_warnings"]
def test_unresolved_variable(): assert parse_terraform('resource "aws_instance" "x" { instance_type = var.kind }')["resources"][0]["warnings"]
@pytest.mark.parametrize("name,data",[("bad.txt",b"x"),("bad.tf",b"\0binary"),("bad.tf",b"x"*(1024*1024+1))],ids=["extension","binary","oversized"])
def test_invalid_uploads(name,data):
    with pytest.raises(TerraformParseError): validate_upload(name,data)
def test_ec2_cost(): assert calculate([resource("aws_instance",instance_type="t3.micro",root_volume_size_gb=8)],"us-east-1","high",pricing=Prices())["total_monthly_cost"]=="7.94"
def test_ebs_cost(): assert calculate([resource("aws_ebs_volume",size=20,type="gp3")],"us-east-1",pricing=Prices())["total_monthly_cost"]=="1.60"
def test_s3_cost(): assert calculate([resource("aws_s3_bucket",estimated_storage_gb=100)],"us-east-1",pricing=Prices())["total_monthly_cost"]=="2.30"
def test_rds_cost(): assert calculate([resource("aws_db_instance",instance_class="db.t3.micro",allocated_storage=20)],"us-east-1","high",pricing=Prices())["total_monthly_cost"]=="16.90"
def test_missing_pricing():
    with pytest.raises(PricingUnavailable): calculate([resource("aws_instance",instance_type="x",root_volume_size_gb=8)],"us-east-1",pricing=Prices())
@pytest.mark.parametrize("cost,status",[(79,"PASS"),(81,"WARNING"),(101,"FAIL")])
def test_budget_states(cost,status): assert evaluate_budget(cost,100)["status"]==status
def test_recommendations(): assert recommend([{"resource_name":"web","resource_type":"aws_instance","estimated_cost":"8"}],"8","low")[0]["estimated_savings"] is None
def test_forecasts():
    result=forecast(history()); assert len(result["linear_regression"])==3; assert result["moving_average"]==[30.0]*3; assert result["metrics"] is not None
def test_insufficient_history():
    with pytest.raises(ValueError): forecast(history(5))
def test_iqr_anomaly(): assert detect(history()+[{"date":"2026-01-01","cost":1000}],"iqr")
def test_rolling_anomaly(): assert detect(history(6)+[{"date":"2026-01-01","cost":1000}],"rolling_zscore")
def test_catalogue_missing_price(tmp_path:Path):
    path=tmp_path/"prices.json";path.write_text(json.dumps({"effective_date":"2026-01-01","regions":{"x":{"ec2":{}}}}))
    with pytest.raises(PricingUnavailable): PricingService(path).rate("x","ec2","x")

def test_rds_secret_database_url(monkeypatch):
    class Secrets:
        def get_secret_value(self, SecretId):
            assert SecretId == "arn:test"
            return {"SecretString": '{"username":"db_user","password":"p@ss word"}'}
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_SECRET_ARN", "arn:test")
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_NAME", "cloudscope")
    monkeypatch.delenv("DB_USERNAME", raising=False)
    url = build_database_url(Secrets())
    assert url == "postgresql+psycopg://db_user:p%40ss+word@db.internal:5432/cloudscope"
