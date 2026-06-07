from database import engine
from sqlalchemy import text

def add_column():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(50)"))
            print("Successfully added 'phone' column to 'users' table.")
        except Exception as e:
            print(f"Column might already exist or error occurred: {e}")

if __name__ == "__main__":
    add_column()
