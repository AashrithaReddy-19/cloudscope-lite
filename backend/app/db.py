import json
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def build_database_url(secrets_client=None) -> str:
    """Resolve the database URL without logging or persisting credentials."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    secret_arn = os.getenv("DB_SECRET_ARN")
    host = os.getenv("DB_HOST")
    if not secret_arn or not host:
        return "sqlite:///./cloudscope.db"

    if secrets_client is None:
        import boto3

        secrets_client = boto3.client(
            "secretsmanager",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
        )

    secret_response = secrets_client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(secret_response["SecretString"])
    username = os.getenv("DB_USERNAME") or secret["username"]
    password = secret["password"]
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "cloudscope")

    return (
        f"postgresql+psycopg://{quote_plus(username)}:{quote_plus(password)}"
        f"@{host}:{port}/{quote_plus(database)}"
    )


URL = build_database_url()
engine = create_engine(
    URL,
    connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
