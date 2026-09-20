import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"backend"))
from passlib.context import CryptContext
from app.db import Base,engine,SessionLocal
from app.models import User
Base.metadata.create_all(engine);db=SessionLocal();email=os.getenv("DEMO_EMAIL","demo@cloudscope.example.com");password=os.getenv("DEMO_PASSWORD","CloudScopeDemo1!")
if not db.query(User).filter_by(email=email).first():db.add(User(name="Demo Student",email=email,password_hash=CryptContext(schemes=["pbkdf2_sha256"]).hash(password)));db.commit()
print(f"Demo user ready: {email}. Password came from DEMO_PASSWORD or the documented local-only default.")
