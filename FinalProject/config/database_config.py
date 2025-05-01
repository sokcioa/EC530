import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'errands.db')
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def get_session():
    """Get a new database session"""
    return Session()

def cleanup_session(session):
    """Clean up a database session"""
    session.close()
    Session.remove()

def init_db(db_path=None):
    """Initialize the database with the given path or default path"""
    if db_path:
        global DATABASE_PATH, DATABASE_URL, engine, session_factory, Session
        DATABASE_PATH = db_path
        DATABASE_URL = f'sqlite:///{DATABASE_PATH}'
        engine = create_engine(DATABASE_URL, echo=False)
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
    
    # Import Base here to avoid circular imports
    from models import Base
    
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    return engine 