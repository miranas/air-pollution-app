import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Load environment variables from .env file and override inherited shell values.
# This prevents stale exported variables (e.g. old DB_PORT) from taking precedence.
load_dotenv(override=True)

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


# Build the connection string for PostgreSQL.
# The password is URL-encoded to handle special characters.
DATABASE_URL = f"postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}"


# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True, # Checks if connection is alive before using it
    pool_size=10, # conservative for container
    max_overflow=5, # Allow spikes
    connect_args={"connect_timeout": 5},
    #timeout=30, # 30 seconds timeout
    echo=True, # log all SQL queries
    future=True # use 2.0 style
    )

# Create session
SessionLocal = sessionmaker(bind=engine)





