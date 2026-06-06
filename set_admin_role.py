import os
import sys

# Proje dizinini yola ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User

def set_admin():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == 'admin1').first()
        if user:
            user.role = 'admin'
            db.commit()
            print("Successfully updated admin1 to have 'admin' role.")
        else:
            print("User admin1 not found!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    set_admin()
