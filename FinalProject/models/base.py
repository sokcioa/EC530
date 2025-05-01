from sqlalchemy.ext.declarative import declarative_base
from config.database_config import engine, get_session, cleanup_session, Session, session_factory

Base = declarative_base()

# Re-export the database configuration
init_db = engine 