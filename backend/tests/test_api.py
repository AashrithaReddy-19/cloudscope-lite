import io,os,uuid
os.environ["DATABASE_URL"]="sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def credentials():
    email=f"user-{uuid.uuid4()}@example.com";password="securepass123";response=client.post("/api/auth/register",json={"name":"Test User","email":email,"password":password});assert response.status_code==201;return email,password,response.json()["access_token"]
def test_health(): assert client.get("/health").json()["status"]=="healthy"
def test_registration_login_and_invalid_login():
    email,password,_=credentials();assert client.post("/api/auth/login",json={"email":email,"password":password}).status_code==200;assert client.post("/api/auth/login",json={"email":email,"password":"incorrect"}).status_code==401
def test_project_analysis_and_downloads():
    _,_,token=credentials();headers={"Authorization":f"Bearer {token}"};project=client.post("/api/projects",headers=headers,json={"project_name":"Integration","aws_region":"us-east-1","monthly_budget":20});assert project.status_code==201
    response=client.post("/api/analyze",headers=headers,data={"project_id":project.json()["id"],"workload_scenario":"high","terraform_text":'resource "aws_instance" "web" { instance_type="t3.micro" root_volume_size_gb=8 }'});assert response.status_code==201;aid=response.json()["analysis_id"]
    assert client.get(f"/api/analyses/{aid}/download/json",headers=headers).status_code==200;csv=client.get(f"/api/analyses/{aid}/download/csv",headers=headers);assert csv.status_code==200 and "resource_name" in csv.text
    history=client.get(f"/api/projects/{project.json()['id']}/analyses",headers=headers);assert history.status_code==200 and history.json()[0]["analysis_id"]==aid
def test_forecast_and_anomalies_return_clean_errors_not_500():
    _,_,token=credentials();headers={"Authorization":f"Bearer {token}"};project=client.post("/api/projects",headers=headers,json={"project_name":"History","aws_region":"us-east-1","monthly_budget":20})
    pid=project.json()["id"]
    assert client.get(f"/api/projects/{pid}/forecast",headers=headers).status_code==422
    assert client.get(f"/api/projects/{pid}/anomalies?method=not-a-method",headers=headers).status_code==422
    bad_csv=io.BytesIO(b"not,the,right,columns\n1,2,3,4")
    upload=client.post(f"/api/projects/{pid}/history/upload",headers=headers,files={"file":("history.csv",bad_csv,"text/csv")})
    assert upload.status_code==422
def test_direct_backend_access_is_not_blocked():
    assert client.get("/health").status_code==200
    assert client.get("/api/pricing/regions").status_code==200
def test_local_dev_cors_still_allows_localhost_3000():
    response=client.options("/api/pricing/regions",headers={"Origin":"http://localhost:3000","Access-Control-Request-Method":"GET"})
    assert response.status_code==200
    assert response.headers["access-control-allow-origin"]=="http://localhost:3000"
def test_pasted_terraform_with_crlf_bytes_is_accepted():
    _,_,token=credentials();headers={"Authorization":f"Bearer {token}"}
    project=client.post("/api/projects",headers=headers,json={"project_name":"CRLF Paste","aws_region":"us-east-1","monthly_budget":20});assert project.status_code==201
    crlf_text='resource "aws_instance" "web" {\r\n  instance_type="t3.micro"\r\n  root_volume_size_gb=8\r\n}\r\n'
    response=client.post("/api/analyze",headers=headers,data={"project_id":project.json()["id"],"workload_scenario":"high","terraform_text":crlf_text})
    assert response.status_code==201
    assert response.json()["resources"][0]["resource_name"]=="web"
def test_uploaded_tf_file_with_crlf_bytes_is_accepted():
    _,_,token=credentials();headers={"Authorization":f"Bearer {token}"}
    project=client.post("/api/projects",headers=headers,json={"project_name":"CRLF Upload","aws_region":"us-east-1","monthly_budget":20});assert project.status_code==201
    crlf_bytes=b'resource "aws_instance" "web" {\r\n  instance_type="t3.micro"\r\n  root_volume_size_gb=8\r\n}\r\n'
    response=client.post("/api/analyze",headers=headers,data={"project_id":project.json()["id"],"workload_scenario":"high"},files={"file":("main.tf",crlf_bytes,"text/plain")})
    assert response.status_code==201
    assert response.json()["resources"][0]["resource_name"]=="web"
