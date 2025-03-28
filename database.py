from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import quote_plus

# Get DATABASE_URL from environment (required in production)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Fail fast if DATABASE_URL is not set (remove fallback for strict production)
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required in production")

# Convert 'postgres://' to 'postgresql://' if needed
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# URL-encode credentials for safety
try:
    if "://" in SQLALCHEMY_DATABASE_URL:
        protocol, rest = SQLALCHEMY_DATABASE_URL.split("://", 1)
        user_pass, host_db = rest.split("@", 1)
        user, password = user_pass.split(":", 1)
        encoded_url = f"{protocol}://{quote_plus(user)}:{quote_plus(password)}@{host_db}"
        SQLALCHEMY_DATABASE_URL = encoded_url
except ValueError as e:
    print(f"WARNING: Could not parse DATABASE_URL: {e}")

# Create engine with production settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,              # Smaller pool for lightweight apps
    max_overflow=10,          # Allow some overflow
    pool_timeout=30,          # Timeout for connection attempts
    pool_recycle=1800,        # Recycle connections every 30 minutes
    pool_pre_ping=True        # Check connection health
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
