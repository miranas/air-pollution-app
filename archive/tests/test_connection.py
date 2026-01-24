from sqlalchemy import create_engine
import urllib.parse

raw_password = "mcrtJiIRdYj12"

# URL-encode the password
safe_password = urllib.parse.quote(raw_password)


DATABASE_URL = f"postgresql://postgres.wimojrbvaovnfzvggsdx:{safe_password}@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"


engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:        
        print("Success, path to the cloud is open")


except Exception as e:
    print(f"Database connection failed {e}")