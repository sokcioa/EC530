#!/usr/bin/env python3

import unittest
import os
import tempfile
from datetime import datetime, timedelta
from models import Base, User, Errand
from config.database_config import init_db, get_session, cleanup_session, Session
from EP_database import CalendarEvent

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Create a temporary directory for the test database
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_errands.db')
        
        # Ensure the directory exists and is writable
        os.makedirs(os.path.dirname(cls.test_db_path), exist_ok=True)
        
        # Initialize database with the full path
        cls.engine = init_db(cls.test_db_path)
        Base.metadata.create_all(cls.engine)
        cls.session = get_session()
        
        # Verify database was created
        if not os.path.exists(cls.test_db_path):
            raise Exception(f"Database file was not created at {cls.test_db_path}")
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cleanup_session(cls.session)
        # Remove the temporary directory and its contents
        if os.path.exists(cls.temp_dir):
            for file in os.listdir(cls.temp_dir):
                os.remove(os.path.join(cls.temp_dir, file))
            os.rmdir(cls.temp_dir)
            
    def setUp(self):
        """Set up test data"""
        # Clear all existing data
        self.session.query(CalendarEvent).delete()
        self.session.query(Errand).delete()
        self.session.query(User).delete()
        self.session.commit()
        
        # Create a test user
        self.user = User(
            name="Test User",
            email="test@example.com",
            home_address="123 Test St, Boston, MA",
            home_latitude=42.3601,
            home_longitude=-71.0589
        )
        self.session.add(self.user)
        self.session.commit()
        
    def tearDown(self):
        """Clean up test data"""
        self.session.rollback()
        
    def test_create_user(self):
        """Test user creation"""
        user = self.session.query(User).filter_by(email="test@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.home_address, "123 Test St, Boston, MA")
        
    def test_create_errand(self):
        """Test errand creation"""
        errand = Errand(
            user_id=self.user.id,
            title="Grocery Shopping",
            location_type="name",
            location_name="Whole Foods",
            location_address="123 Market St, Boston, MA",
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=60,
            repetition="none",
            priority=2
        )
        self.session.add(errand)
        self.session.commit()
        
        # Verify errand was created
        saved_errand = self.session.query(Errand).filter_by(title="Grocery Shopping").first()
        self.assertIsNotNone(saved_errand)
        self.assertEqual(saved_errand.location_name, "Whole Foods")
        self.assertEqual(saved_errand.priority, 2)
        
    def test_create_calendar_event(self):
        """Test calendar event creation"""
        # First create an errand
        errand = Errand(
            user_id=self.user.id,
            title="Doctor Appointment",
            location_type="name",
            location_name="City Hospital",
            location_address="456 Health St, Boston, MA",
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=90,
            repetition="none",
            priority=3
        )
        self.session.add(errand)
        self.session.commit()
        
        # Create a calendar event for the errand
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=90)
        event = CalendarEvent(
            user_id=self.user.id,
            errand_id=errand.id,
            google_calendar_event_id="test_event_123",
            start_time=start_time,
            end_time=end_time,
            date=start_time.date(),
            status="scheduled",
            notes="Bring insurance card"
        )
        self.session.add(event)
        self.session.commit()
        
        # Verify event was created
        saved_event = self.session.query(CalendarEvent).filter_by(
            google_calendar_event_id="test_event_123"
        ).first()
        self.assertIsNotNone(saved_event)
        self.assertEqual(saved_event.status, "scheduled")
        self.assertEqual(saved_event.notes, "Bring insurance card")
        
    def test_relationships(self):
        """Test database relationships"""
        # Create an errand
        errand = Errand(
            user_id=self.user.id,
            title="Test Errand",
            location_type="name",
            location_name="Test Location",
            location_address="Test Address",
            access_type="drive",
            valid_start_window="0900",
            valid_end_window="1700",
            estimated_duration=30,
            repetition="none",
            priority=1
        )
        self.session.add(errand)
        self.session.commit()
        
        # Create a calendar event
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        event = CalendarEvent(
            user_id=self.user.id,
            errand_id=errand.id,
            google_calendar_event_id="test_relationship_123",
            start_time=start_time,
            end_time=end_time,
            date=start_time.date()
        )
        self.session.add(event)
        self.session.commit()
        
        # Test relationships
        self.assertEqual(errand.user.id, self.user.id)
        self.assertEqual(event.user.id, self.user.id)
        self.assertEqual(event.errand.id, errand.id)
        self.assertIn(errand, self.user.errands)
        self.assertIn(event, self.user.calendar_events)
        self.assertIn(event, errand.calendar_events)

if __name__ == '__main__':
    unittest.main() 