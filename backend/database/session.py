import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

raw_password = "mcrtJiIRdYj12"

# URL-encode the password
safe_password = urllib.parse.quote(raw_password)



DATABASE_URL = f"postgresql://postgres.wimojrbvaovnfzvggsdx:{safe_password}@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"



# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True, # Checks if connection is alive before using it
    pool_size=5, # matching my Nano Free tier limit
    max_overflow=0, # no overflow connections
    #timeout=30, # 30 seconds timeout
    echo=True, # log all SQL queries
    future=True # use 2.0 style
    )

# Create session
SessionLocal = sessionmaker(bind=engine)

# Test connection


session = None
try:
    session = SessionLocal()
    result = session.execute(text("SELECT 1"))
    print("Database connection successful, result:", result.scalar())

except Exception as e:
    print("Database connection failed", e)

finally:
    if session is not None:
        session.close()





