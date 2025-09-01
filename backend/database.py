from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ⚠️ Replace with your own credentials
DATABASE_URL = "postgresql://postgres.aksrgmazvczrqchtfgmc:wildwood=$20023@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
