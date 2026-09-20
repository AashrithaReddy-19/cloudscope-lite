from datetime import datetime, timezone
from sqlalchemy import String,Float,DateTime,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from .db import Base
def utc_now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"; id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(100)); email:Mapped[str]=mapped_column(String(255),unique=True,index=True); password_hash:Mapped[str]=mapped_column(String(255)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc_now)
class Project(Base):
    __tablename__="projects"; id:Mapped[int]=mapped_column(primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id")); project_name:Mapped[str]=mapped_column(String(120)); aws_region:Mapped[str]=mapped_column(String(30)); monthly_budget:Mapped[float]=mapped_column(Float); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc_now); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc_now,onupdate=utc_now)
class Analysis(Base):
    __tablename__="analyses"; id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id")); terraform_filename:Mapped[str]=mapped_column(String(255)); workload_scenario:Mapped[str]=mapped_column(String(20)); estimated_monthly_cost:Mapped[float]=mapped_column(Float); budget_status:Mapped[str]=mapped_column(String(30)); pricing_effective_date:Mapped[str]=mapped_column(String(20)); report_json:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utc_now)
class ResourceEstimate(Base):
    __tablename__="resource_estimates"; id:Mapped[int]=mapped_column(primary_key=True); analysis_id:Mapped[int]=mapped_column(ForeignKey("analyses.id")); resource_type:Mapped[str]=mapped_column(String(60)); resource_name:Mapped[str]=mapped_column(String(120)); configuration_json:Mapped[str]=mapped_column(Text); pricing_json:Mapped[str]=mapped_column(Text); estimated_monthly_cost:Mapped[float]=mapped_column(Float); warnings_json:Mapped[str]=mapped_column(Text)
class Recommendation(Base):
    __tablename__="recommendations"; id:Mapped[int]=mapped_column(primary_key=True); analysis_id:Mapped[int]=mapped_column(ForeignKey("analyses.id")); resource_name:Mapped[str]=mapped_column(String(120)); recommendation_type:Mapped[str]=mapped_column(String(60),default="cost_review"); recommendation_text:Mapped[str]=mapped_column(Text); current_cost:Mapped[float|None]=mapped_column(Float); alternative_cost:Mapped[float|None]=mapped_column(Float); estimated_savings:Mapped[float|None]=mapped_column(Float); confidence_level:Mapped[str]=mapped_column(String(20))
class HistoricalCost(Base):
    __tablename__="historical_costs"; id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id")); cost_date:Mapped[str]=mapped_column(String(20)); actual_cost:Mapped[float]=mapped_column(Float); is_anomaly:Mapped[bool]=mapped_column(default=False); anomaly_method:Mapped[str|None]=mapped_column(String(30))
