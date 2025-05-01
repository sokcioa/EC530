#!/usr/bin/env python3

import unittest
from flask import Flask
from flask.testing import FlaskClient
from api.base import base_bp, engine, Base, get_db
from EP_database import User, Errand, CalendarEvent
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from unittest.mock import patch

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and client"""
        # Create a test database
        cls.test_db = 'sqlite:///./errands.db'  # Use the same database as the API
        cls.engine = create_engine(cls.test_db)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=cls.engine)
        
        # Create Flask app and register blueprint
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.register_blueprint(base_bp)  # Remove url_prefix='/api'
        
        # Create a test user
        cls.db = cls.SessionLocal()
        cls.test_user = User(
            name="API Test User",
            email="api_test@example.com",
            home_address="123 API Test St, Boston, MA",
            home_latitude=42.3601,
            home_longitude=-71.0589
        )
        cls.db.add(cls.test_user)
        cls.db.commit()
        
        # Initialize test client
        cls.client = cls.app.test_client()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls.db.close()
        Base.metadata.drop_all(bind=cls.engine)
        if os.path.exists('test_api.db'):
            os.remove('test_api.db')
            
    def setUp(self):
        """Clear existing errands"""
        self.db.query(Errand).delete()
        self.db.commit()
        
    @patch('api.places.validate_address')
    def test_create_errand(self, mock_validate):
        """Test creating a new errand"""
        mock_validate.return_value = (42.3601, -71.0589)
        
        errand_data = {
            "user_id": self.test_user.id,
            "title": "Test Errand Create",
            "location_type": "address",
            "location_name": "Test Location",
            "location_address": "Test Address",
            "category": "test",
            "is_remote": False,
            "use_exact_location": True,
            "access_type": "drive",
            "valid_start_window": "0900",
            "valid_end_window": "1700",
            "estimated_duration": 30,
            "repetition": "none",
            "priority": 1
        }
        
        response = self.client.post("/errands/", json=errand_data)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["title"], errand_data["title"])
        self.assertEqual(data["user_id"], self.test_user.id)
        
    def test_list_errands(self):
        """Test listing errands"""
        # Create test errands
        errands = [
            Errand(
                user_id=self.test_user.id,
                title=f"Test Errand List {i}",
                location_type="address",
                location_name=f"Location {i}",
                location_address=f"Address {i}",
                category="test",
                is_remote=False,
                use_exact_location=True,
                access_type="drive",
                valid_start_window="0900",
                valid_end_window="1700",
                estimated_duration=30,
                repetition="none",
                priority=1
            ) for i in range(3)
        ]
        for errand in errands:
            self.db.add(errand)
        self.db.commit()
        
        # Test listing all errands
        response = self.client.get("/errands/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 3)
        
        # Test filtering by user_id
        response = self.client.get(f"/errands/?user_id={self.test_user.id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 3)
        
    def test_get_errand(self):
        """Test getting a specific errand"""
        # Create a test errand
        errand = Errand(
            user_id=self.test_user.id,
            title="Test Errand Get",
            location_type="address",
            location_name="Test Location",
            location_address="Test Address",
            category="test",
            is_remote=False,
            use_exact_location=True,
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=30,
            repetition="none",
            priority=1
        )
        self.db.add(errand)
        self.db.commit()
        
        # Test getting the errand
        response = self.client.get(f"/errands/{errand.id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["title"], errand.title)
        
        # Test getting non-existent errand
        response = self.client.get("/errands/999")
        self.assertEqual(response.status_code, 404)
        
    def test_update_errand(self):
        """Test updating an errand"""
        # Create a test errand
        errand = Errand(
            user_id=self.test_user.id,
            title="Test Errand Update",
            location_type="address",
            location_name="Test Location",
            location_address="Test Address",
            category="test",
            is_remote=False,
            use_exact_location=True,
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=30,
            repetition="none",
            priority=1
        )
        self.db.add(errand)
        self.db.commit()
        
        # Update the errand
        update_data = {
            "title": "Updated Title",
            "category": "updated",
            "priority": 2
        }
        
        response = self.client.put(f"/errands/{errand.id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["title"], update_data["title"])
        self.assertEqual(data["category"], update_data["category"])
        self.assertEqual(data["priority"], update_data["priority"])
        
    def test_delete_errand(self):
        """Test deleting an errand"""
        # Create a test errand
        errand = Errand(
            user_id=self.test_user.id,
            title="Test Errand Delete",
            location_type="address",
            location_name="Test Location",
            location_address="Test Address",
            category="test",
            is_remote=False,
            use_exact_location=True,
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=30,
            repetition="none",
            priority=1
        )
        self.db.add(errand)
        self.db.commit()
        
        # Delete the errand
        response = self.client.delete(f"/errands/{errand.id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify the errand is deleted
        response = self.client.get(f"/errands/{errand.id}")
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main() 