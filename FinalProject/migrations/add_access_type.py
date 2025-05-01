import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EP_database import Session, Errand
from sqlalchemy import text
import logging

logger = logging.getLogger('ErrandPlanner')

def migrate():
    """Add access_type field to errands table"""
    db_session = Session()
    try:
        # Add access_type column with default value 'drive'
        db_session.execute(text("""
            ALTER TABLE errands 
            ADD COLUMN access_type VARCHAR(20) NOT NULL DEFAULT 'drive'
        """))
        db_session.commit()
        logger.info("Successfully added access_type column to errands table")
    except Exception as e:
        logger.error(f"Error adding access_type column: {str(e)}")
        db_session.rollback()
        raise
    finally:
        db_session.close()

if __name__ == '__main__':
    migrate() 