import os
from auth import init_auth_db
import database
import models

def migrate():
    print("Starting migration process...")
    # 1. Auth DB Başlat
    init_auth_db()
    
    print(f"Connecting to database engine: {database.engine.name}")
    
    # 2. Modellerin tamamını yarat
    print("Creating all tables from models.Base.metadata...")
    models.Base.metadata.create_all(bind=database.engine)
    
    # 3. İhtiyaç varsa raw SQL query'leri çalıştır
    database.init_db()
    
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
