import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from EP_database import init_db, Session

def upgrade():
    """Add priority column to errands table"""
    engine = init_db()
    session = Session()
    
    try:
        # Add priority column with default value 3
        session.execute(text("""
            ALTER TABLE errands 
            ADD COLUMN priority INTEGER DEFAULT 3
        """))
        session.commit()
        print("Successfully added priority column to errands table")
    except Exception as e:
        print(f"Error adding priority column: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    upgrade() 