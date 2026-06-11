from database import engine
from sqlalchemy import text
from datetime import datetime
with engine.connect() as conn:
    rows = conn.execute(text("SELECT username, subscription_expires_at, is_active FROM users")).fetchall()
    for r in rows:
        print(r)
