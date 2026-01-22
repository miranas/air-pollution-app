import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")


# Ensure db_password is provided so its type is known to be str before quoting
if db_password is None:
    raise RuntimeError("DB_PASSWORD environment variable is not set")

# URL-encode the password
safe_password = urllib.parse.quote(db_password)


DATABASE_URL = f"postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}?sslmode=require"



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





