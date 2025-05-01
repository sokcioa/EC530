#!/usr/bin/env python3

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Import from original location
from EP_database import User, Errand, CalendarEvent
from models import Base, get_session, cleanup_session

# Load environment variables
load_dotenv()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./errands.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Flask Blueprint
base_bp = Blueprint('base', __name__)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@base_bp.route('/errands/', methods=['POST'])
def create_errand():
    """
    Create a new errand.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Verify user exists
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    errand = Errand(**data)
    db.add(errand)
    db.commit()
    db.refresh(errand)
    
    # Convert SQLAlchemy object to dictionary, excluding SQLAlchemy-specific attributes
    errand_dict = {
        'id': errand.id,
        'user_id': errand.user_id,
        'title': errand.title,
        'location_type': errand.location_type,
        'location_name': errand.location_name,
        'location_address': errand.location_address,
        'category': errand.category,
        'is_remote': errand.is_remote,
        'use_exact_location': errand.use_exact_location,
        'access_type': errand.access_type,
        'valid_start_window': errand.valid_start_window,
        'valid_end_window': errand.valid_end_window,
        'estimated_duration': errand.estimated_duration,
        'repetition': errand.repetition,
        'priority': errand.priority
    }
    
    return jsonify(errand_dict), 201

@base_bp.route('/errands/', methods=['GET'])
def list_errands():
    """
    List all errands, optionally filtered by user_id.
    """
    db = next(get_db())
    user_id = request.args.get('user_id')
    
    query = db.query(Errand)
    if user_id:
        query = query.filter(Errand.user_id == user_id)
    errands = query.all()
    
    # Convert SQLAlchemy objects to dictionaries, excluding SQLAlchemy-specific attributes
    errands_data = []
    for errand in errands:
        errand_dict = {
            'id': errand.id,
            'user_id': errand.user_id,
            'title': errand.title,
            'location_type': errand.location_type,
            'location_name': errand.location_name,
            'location_address': errand.location_address,
            'category': errand.category,
            'is_remote': errand.is_remote,
            'use_exact_location': errand.use_exact_location,
            'access_type': errand.access_type,
            'valid_start_window': errand.valid_start_window,
            'valid_end_window': errand.valid_end_window,
            'estimated_duration': errand.estimated_duration,
            'repetition': errand.repetition,
            'priority': errand.priority
        }
        errands_data.append(errand_dict)
    
    return jsonify(errands_data)

@base_bp.route('/errands/<int:errand_id>', methods=['GET'])
def get_errand(errand_id):
    """
    Get a specific errand by ID.
    """
    db = next(get_db())
    errand = db.query(Errand).filter(Errand.id == errand_id).first()
    
    if not errand:
        return jsonify({"error": "Errand not found"}), 404
    
    # Convert SQLAlchemy object to dictionary, excluding SQLAlchemy-specific attributes
    errand_dict = {
        'id': errand.id,
        'user_id': errand.user_id,
        'title': errand.title,
        'location_type': errand.location_type,
        'location_name': errand.location_name,
        'location_address': errand.location_address,
        'category': errand.category,
        'is_remote': errand.is_remote,
        'use_exact_location': errand.use_exact_location,
        'access_type': errand.access_type,
        'valid_start_window': errand.valid_start_window,
        'valid_end_window': errand.valid_end_window,
        'estimated_duration': errand.estimated_duration,
        'repetition': errand.repetition,
        'priority': errand.priority
    }
    
    return jsonify(errand_dict)

@base_bp.route('/errands/<int:errand_id>', methods=['PUT'])
def update_errand(errand_id):
    """
    Update an existing errand.
    """
    db = next(get_db())
    errand = db.query(Errand).filter(Errand.id == errand_id).first()
    
    if not errand:
        return jsonify({"error": "Errand not found"}), 404
    
    data = request.get_json()
    
    # Update only the fields that are provided in the request
    for field in ['title', 'location_type', 'location_name', 'location_address',
                 'category', 'is_remote', 'use_exact_location', 'access_type',
                 'valid_start_window', 'valid_end_window', 'estimated_duration',
                 'repetition', 'priority']:
        if field in data:
            setattr(errand, field, data[field])
    
    try:
        db.commit()
        # Refresh the errand to get the updated state
        db.refresh(errand)
        
        # Convert SQLAlchemy object to dictionary
        errand_dict = {
            'id': errand.id,
            'user_id': errand.user_id,
            'title': errand.title,
            'location_type': errand.location_type,
            'location_name': errand.location_name,
            'location_address': errand.location_address,
            'category': errand.category,
            'is_remote': errand.is_remote,
            'use_exact_location': errand.use_exact_location,
            'access_type': errand.access_type,
            'valid_start_window': errand.valid_start_window,
            'valid_end_window': errand.valid_end_window,
            'estimated_duration': errand.estimated_duration,
            'repetition': errand.repetition,
            'priority': errand.priority
        }
        
        return jsonify(errand_dict)
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

@base_bp.route('/errands/<int:errand_id>', methods=['DELETE'])
def delete_errand(errand_id):
    """
    Delete an errand.
    """
    db = next(get_db())
    errand = db.query(Errand).filter(Errand.id == errand_id).first()
    if errand is None:
        return jsonify({"error": "Errand not found"}), 404
    
    db.delete(errand)
    db.commit()
    return jsonify({"message": "Errand deleted successfully"})

if __name__ == "__main__":
    # Create database tables
    Base.metadata.create_all(bind=engine) 