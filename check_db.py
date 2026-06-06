import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')
safe_password = urllib.parse.quote_plus(db_password)
DATABASE_URL = f'postgresql://{db_user}:{safe_password}@{db_host}:{db_port}/{db_name}'

engine = create_engine(DATABASE_URL)
with engine.begin() as conn:
    # Get all users
    res = conn.execute(text("SELECT username FROM users"))
    users = [r[0] for r in res]
    print("All users:", users)
    
    # Try the admin query to see if it fails
    try:
        conn.execute(text("""
            SELECT u.username, u.email, u.role, u.is_active, u.last_active, u.created_at, COUNT(a.id) AS alarm_count
            FROM users u
            LEFT JOIN user_alarms a ON a.username = u.username AND a.status = 'active'
            GROUP BY u.username, u.email, u.role, u.is_active, u.last_active, u.created_at
            ORDER BY u.created_at DESC
        """))
        print("Admin query successful.")
    except Exception as e:
        print("Admin query failed:", str(e))
