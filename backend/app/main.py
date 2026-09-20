import csv,io,json,logging,os
from datetime import datetime,timedelta,timezone
from pathlib import Path,PurePath
import jwt
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy.orm import Session
from .db import Base,engine,get_db
from .models import User,Project,Analysis,HistoricalCost,ResourceEstimate,Recommendation
from .services.terraform_parser import parse_terraform,validate_upload,TerraformParseError
from .services.pricing_service import PricingService,PricingUnavailable
from .services.cost_calculator import calculate,compare_scenarios
from .services.budget_policy import evaluate_budget
from .services.recommendation_engine import recommend
from .services.forecasting import forecast
from .services.anomaly_detection import detect
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
Base.metadata.create_all(engine)
app=FastAPI(title="CloudScope Lite",version="1.0.0",description="Safe pre-deployment AWS Terraform cost simulator")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:3000").split(","),allow_methods=["*"],allow_headers=["*"])

pwd=CryptContext(schemes=["pbkdf2_sha256"],deprecated="auto"); bearer=HTTPBearer(); SECRET=os.getenv("JWT_SECRET","development-only-change-me")
class Register(BaseModel): name:str=Field(min_length=2,max_length=100); email:EmailStr; password:str=Field(min_length=8)
class Login(BaseModel): email:EmailStr; password:str
class ProjectIn(BaseModel): project_name:str; aws_region:str="us-east-1"; monthly_budget:float=Field(gt=0)
def token(user): return jwt.encode({"sub":str(user.id),"exp":datetime.now(timezone.utc)+timedelta(hours=12)},SECRET,algorithm="HS256")
def current(credentials:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    try: uid=int(jwt.decode(credentials.credentials,SECRET,algorithms=["HS256"])["sub"])
    except Exception: raise HTTPException(401,"Invalid or expired token")
    user=db.get(User,uid)
    if not user: raise HTTPException(401,"User no longer exists")
    return user
@app.exception_handler(TerraformParseError)
async def bad_hcl(_,exc): return JSONResponse(status_code=422,content={"detail":str(exc)})
@app.exception_handler(PricingUnavailable)
async def missing_price(_,exc): return JSONResponse(status_code=422,content={"detail":str(exc)})
@app.get("/health")
def health(): return {"status":"healthy","database":"configured"}
@app.post("/api/auth/register",status_code=201)
def register(data:Register,db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,"Email already registered")
    user=User(name=data.name,email=data.email,password_hash=pwd.hash(data.password)); db.add(user); db.commit(); db.refresh(user); return {"access_token":token(user),"token_type":"bearer"}
@app.post("/api/auth/login")
def login(data:Login,db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==data.email).first()
    if not user or not pwd.verify(data.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":token(user),"token_type":"bearer"}
@app.get("/api/auth/me")
def me(user=Depends(current)): return {"id":user.id,"name":user.name,"email":user.email}
@app.post("/api/projects",status_code=201)
def create_project(data:ProjectIn,user=Depends(current),db:Session=Depends(get_db)):
    item=Project(user_id=user.id,**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
@app.get("/api/projects")
def projects(user=Depends(current),db:Session=Depends(get_db)): return db.query(Project).filter(Project.user_id==user.id).all()
@app.get("/api/projects/{project_id}")
def project(project_id:int,user=Depends(current),db:Session=Depends(get_db)):
    item=db.query(Project).filter(Project.id==project_id,Project.user_id==user.id).first()
    if not item: raise HTTPException(404,"Project not found")
    return item
@app.delete("/api/projects/{project_id}",status_code=204)
def delete_project(project_id:int,user=Depends(current),db:Session=Depends(get_db)):
    item=project(project_id,user,db); db.delete(item); db.commit()
@app.get("/api/projects/{project_id}/analyses")
def list_analyses(project_id:int,user=Depends(current),db:Session=Depends(get_db)):
    project(project_id,user,db)
    rows=db.query(Analysis).filter(Analysis.project_id==project_id).order_by(Analysis.created_at.desc()).all()
    return [{"analysis_id":r.id,"terraform_filename":r.terraform_filename,"workload_scenario":r.workload_scenario,"estimated_monthly_cost":r.estimated_monthly_cost,"budget_status":r.budget_status,"pricing_effective_date":r.pricing_effective_date,"created_at":r.created_at.isoformat()} for r in rows]
@app.post("/api/analyze",status_code=201)
async def analyze(project_id:int=Form(...),workload_scenario:str=Form("high"),terraform_text:str|None=Form(None),file:UploadFile|None=File(None),user=Depends(current),db:Session=Depends(get_db)):
    p=project(project_id,user,db)
    if workload_scenario not in {"low","medium","high"}: raise HTTPException(422,"Invalid workload scenario")
    if file: text=validate_upload(PurePath(file.filename or "").name,await file.read()); filename=PurePath(file.filename or "upload.tf").name
    elif terraform_text: text=terraform_text; filename="pasted.tf"
    else: raise HTTPException(422,"Provide a .tf file or Terraform text")
    parsed=parse_terraform(text,p.aws_region); pricing=PricingService(); costs=calculate(parsed["resources"],p.aws_region,workload_scenario,pricing=pricing); policy=evaluate_budget(costs["total_monthly_cost"],p.monthly_budget); recs=recommend(costs["resources"],costs["total_monthly_cost"],workload_scenario)
    report={**costs,"budget_policy":policy,"recommendations":recs,"unsupported_warnings":parsed["unsupported_warnings"],"scenario_comparison":compare_scenarios(parsed["resources"],p.aws_region,pricing),"pricing_effective_date":pricing.effective_date,"pricing_currency":pricing.currency,"pricing_source":pricing.source}
    item=Analysis(project_id=p.id,terraform_filename=filename,workload_scenario=workload_scenario,estimated_monthly_cost=float(costs["total_monthly_cost"]),budget_status=policy["status"],pricing_effective_date=pricing.effective_date,report_json=json.dumps(report)); db.add(item); db.flush()
    for row in costs["resources"]: db.add(ResourceEstimate(analysis_id=item.id,resource_type=row["resource_type"],resource_name=row["resource_name"],configuration_json=json.dumps(row["attributes"]),pricing_json=json.dumps({"rate":row["pricing_rate"],"formula":row["formula"]}),estimated_monthly_cost=float(row["estimated_cost"]),warnings_json=json.dumps(row["warnings"])))
    for rec in recs: db.add(Recommendation(analysis_id=item.id,resource_name=rec["resource_name"],recommendation_text=rec["suggestion"],current_cost=float(rec["current_estimated_cost"]),alternative_cost=rec["alternative_estimated_cost"],estimated_savings=rec["estimated_savings"],confidence_level=rec["confidence"]))
    db.commit(); db.refresh(item); return {"analysis_id":item.id,**report}
def own_analysis(aid,user,db):
    row=db.query(Analysis).join(Project).filter(Analysis.id==aid,Project.user_id==user.id).first()
    if not row: raise HTTPException(404,"Analysis not found")
    return row
@app.get("/api/analyses/{analysis_id}")
@app.get("/api/analyses/{analysis_id}/report")
def analysis(analysis_id:int,user=Depends(current),db:Session=Depends(get_db)): row=own_analysis(analysis_id,user,db); return {"analysis_id":row.id,**json.loads(row.report_json)}
@app.get("/api/analyses/{analysis_id}/recommendations")
def recommendations(analysis_id:int,user=Depends(current),db:Session=Depends(get_db)): return analysis(analysis_id,user,db)["recommendations"]
@app.get("/api/analyses/{analysis_id}/download/json")
def download_json(analysis_id:int,user=Depends(current),db:Session=Depends(get_db)): return JSONResponse(analysis(analysis_id,user,db),headers={"Content-Disposition":f"attachment; filename=analysis-{analysis_id}.json"})
@app.get("/api/analyses/{analysis_id}/download/csv")
def download_csv(analysis_id:int,user=Depends(current),db:Session=Depends(get_db)):
    report=analysis(analysis_id,user,db); out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=["resource_type","resource_name","estimated_cost","formula"]); writer.writeheader(); writer.writerows({k:r[k] for k in writer.fieldnames} for r in report["resources"]); return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=analysis-{analysis_id}.csv"})
@app.post("/api/projects/{project_id}/history/upload")
async def upload_history(project_id:int,file:UploadFile=File(...),user=Depends(current),db:Session=Depends(get_db)):
    project(project_id,user,db)
    try:
        raw=(await file.read()).decode(); rows=list(csv.DictReader(io.StringIO(raw)))
        parsed=[(row["date"],float(row["cost"])) for row in rows]
    except (UnicodeDecodeError,KeyError,ValueError) as exc: raise HTTPException(422,"CSV must be UTF-8 text with 'date' and 'cost' columns.") from exc
    for cost_date,actual_cost in parsed: db.add(HistoricalCost(project_id=project_id,cost_date=cost_date,actual_cost=actual_cost))
    db.commit(); return {"imported":len(parsed)}
def history(project_id,user,db): project(project_id,user,db); return [{"date":x.cost_date,"cost":x.actual_cost} for x in db.query(HistoricalCost).filter_by(project_id=project_id).all()]
@app.get("/api/projects/{project_id}/forecast")
def get_forecast(project_id:int,user=Depends(current),db:Session=Depends(get_db)):
    try: return forecast(history(project_id,user,db))
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@app.get("/api/projects/{project_id}/anomalies")
def anomalies(project_id:int,method:str="iqr",user=Depends(current),db:Session=Depends(get_db)):
    try: return detect(history(project_id,user,db),method)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@app.get("/api/pricing/regions")
def regions(): return {"regions":PricingService().regions()}
@app.get("/api/pricing/resources")
def resources(): return {"supported":["aws_instance","aws_ebs_volume","aws_s3_bucket","aws_db_instance"]}

# Serves the React production build from the same origin as the API. Only
# present when a build has actually been placed here (the Docker image
# copies it in; local `uvicorn --reload` development has no build here and
# runs the frontend separately via `npm run dev` instead).
FRONTEND_DIR=Path(os.getenv("FRONTEND_DIST_DIR","/app/static"))
if (FRONTEND_DIR/"index.html").is_file():
    app.mount("/assets",StaticFiles(directory=FRONTEND_DIR/"assets"),name="frontend-assets")
    INDEX_HTML=FRONTEND_DIR/"index.html"
    @app.get("/{full_path:path}")
    def spa(full_path:str):
        if full_path=="api" or full_path.startswith("api/"): raise HTTPException(404,"Not found")
        return FileResponse(INDEX_HTML)
