from sqlalchemy import text
from src.utils.db import LocalSession, engine
from src.Projects.models import Base

def migrate():
    Base.metadata.create_all(bind=engine)
    db = LocalSession()
    try:
        # Drop generated_html from projects if it exists
        db.execute(text('ALTER TABLE projects DROP COLUMN IF EXISTS generated_html;'))
        db.commit()
        print("Migration complete!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
