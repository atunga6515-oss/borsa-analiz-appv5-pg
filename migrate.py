import os
from auth import init_auth_db
import database
import models

def migrate():
    print("Starting migration process...")
    # 1. Auth DB Başlat
    init_auth_db()
    
    print(f"Connecting to database engine: {database.engine.name}")
    
    # 2. Modellerin tamamını (ohlcv, vs) try-except ile KESMEDEN yarat
    print("Creating all tables from models.Base.metadata...")
    models.Base.metadata.create_all(bind=database.engine)
    
    # 3. İhtiyaç varsa raw SQL query'leri çalıştır (try-except içermez)
    database.init_db()
    
    # NOT: Eski SQLite manuel ALTER TABLE blokları ve hatayı yutan except blokları 
    # kullanıcının isteği doğrultusunda tamamen kaldırılmıştır.
    # Herhangi bir migration hatası doğrudan konsolda gösterilecektir.

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
