#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from EP_database import User, Errand, CalendarEvent, Base

# Load environment variables
load_dotenv()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./errands.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Errands API",
    description="API for managing errands and calendar events",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request/response validation
from pydantic import BaseModel

class ErrandBase(BaseModel):
    title: str
    description: str
    location_name: str
    location_address: str
    location_latitude: float
    location_longitude: float
    estimated_duration: int
    priority: int

class ErrandCreate(ErrandBase):
    user_id: int

class ErrandUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    estimated_duration: Optional[int] = None
    priority: Optional[int] = None

class ErrandResponse(ErrandBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API Endpoints
@app.post("/errands/", response_model=ErrandResponse)
def create_errand(errand: ErrandCreate, db: Session = Depends(get_db)):
    """
    Create a new errand.
    
    - **title**: Title of the errand
    - **description**: Detailed description
    - **location_name**: Name of the location
    - **location_address**: Full address
    - **location_latitude**: Latitude coordinate
    - **location_longitude**: Longitude coordinate
    - **estimated_duration**: Duration in minutes
    - **priority**: Priority level (1-5)
    - **user_id**: ID of the user creating the errand
    """
    # Verify user exists
    user = db.query(User).filter(User.id == errand.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_errand = Errand(**errand.model_dump())
    db.add(db_errand)
    db.commit()
    db.refresh(db_errand)
    return db_errand

@app.get("/errands/", response_model=List[ErrandResponse])
def list_errands(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all errands, optionally filtered by user_id.
    
    - **user_id**: Filter errands by user ID
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    query = db.query(Errand)
    if user_id:
        query = query.filter(Errand.user_id == user_id)
    return query.offset(skip).limit(limit).all()

@app.get("/errands/{errand_id}", response_model=ErrandResponse)
def get_errand(errand_id: int, db: Session = Depends(get_db)):
    """
    Get a specific errand by ID.
    
    - **errand_id**: ID of the errand to retrieve
    """
    errand = db.query(Errand).filter(Errand.id == errand_id).first()
    if errand is None:
        raise HTTPException(status_code=404, detail="Errand not found")
    return errand

@app.put("/errands/{errand_id}", response_model=ErrandResponse)
def update_errand(
    errand_id: int,
    errand_update: ErrandUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing errand.
    
    - **errand_id**: ID of the errand to update
    - **errand_update**: Fields to update (all optional)
    """
    db_errand = db.query(Errand).filter(Errand.id == errand_id).first()
    if db_errand is None:
        raise HTTPException(status_code=404, detail="Errand not found")
    
    update_data = errand_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_errand, key, value)
    
    db_errand.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_errand)
    return db_errand

@app.delete("/errands/{errand_id}")
def delete_errand(errand_id: int, db: Session = Depends(get_db)):
    """
    Delete an errand.
    
    - **errand_id**: ID of the errand to delete
    """
    db_errand = db.query(Errand).filter(Errand.id == errand_id).first()
    if db_errand is None:
        raise HTTPException(status_code=404, detail="Errand not found")
    
    db.delete(db_errand)
    db.commit()
    return {"message": "Errand deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    # Create database tables
    Base.metadata.create_all(bind=engine)
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000) 