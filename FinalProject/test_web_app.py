import unittest
from flask import Flask
from flask.testing import FlaskClient
from web_app import app, get_current_user, validate_address_with_bias
from models import Base, User, Errand
from config.database_config import engine, Session
from EP_database import CalendarEvent
import json
import os
from datetime import datetime, date
import sqlalchemy
import time
from sqlalchemy.exc import OperationalError
from flask import session
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Add file handler
file_handler = RotatingFileHandler('logs/test_web_app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))

# Configure all loggers to only write to file
loggers = [
    logging.getLogger('TestWebApp'),
    logging.getLogger('ErrandPlanner'),
    logging.getLogger('api.places'),
    logging.getLogger('googleapiclient'),
    logging.getLogger('googleapiclient.discovery'),
    logging.getLogger('googleapiclient.discovery_cache')
]

for logger in loggers:
    logger.setLevel(logging.DEBUG)
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # Add file handler
    logger.addHandler(file_handler)
    # Disable propagation to prevent console output
    logger.propagate = False

# Also configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
root_logger.addHandler(file_handler)

# Create all tables before running tests
Base.metadata.create_all(engine)

def retry_on_db_lock(func, max_retries=3, delay=1):
    """Decorator to retry database operations on lock errors"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                raise
    return wrapper

class TestWebApp(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        logger.debug("Setting up test environment")
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        # Get database session from existing engine
        self.db_session = Session()
        
        # Clean up any existing test users and errands
        self.cleanup_test_data()
        
        # Create test user with unique email
        self.test_user = User(
            email=f'test_{datetime.now().timestamp()}@example.com',
            name='Test User',
            home_address='1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA',
            home_latitude=37.4220,
            home_longitude=-122.0841
        )
        self.db_session.add(self.test_user)
        self.db_session.commit()
        
        # Store user ID for session testing
        self.user_id = self.test_user.id
        logger.debug(f"Test user created with ID: {self.user_id}")

    def cleanup_test_data(self):
        """Clean up test data"""
        logger.debug("Cleaning up test data")
        try:
            # Delete all test users
            self.db_session.query(User).filter(User.email.like('test_%@example.com')).delete()
            # Delete all test errands
            self.db_session.query(Errand).filter(Errand.title.like('Test%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Initial%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Flexible%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Remote%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Grocery%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Pharmacy%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Bank%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Post%')).delete()
            self.db_session.query(Errand).filter(Errand.title.like('Office%')).delete()
            self.db_session.commit()
            logger.debug("Test data cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during test data cleanup: {str(e)}")
            self.db_session.rollback()
            raise e

    def tearDown(self):
        """Clean up after tests"""
        logger.debug("Tearing down test environment")
        try:
            self.cleanup_test_data()
        finally:
            self.db_session.close()

    def test_session_persistence(self):
        """Test that user session persists across requests"""
        logger.debug("Testing session persistence")
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
                logger.debug(f"Set session user_id to {self.user_id}")
            
            # Make a request that should maintain session
            response = client.get('/errands')
            self.assertEqual(response.status_code, 200)
            logger.debug("Session maintained across request")
            
            # Verify session still exists
            with client.session_transaction() as sess:
                self.assertIn('user_id', sess)
                self.assertEqual(sess['user_id'], self.user_id)
                logger.debug("Session verification successful")

    def test_address_persistence(self):
        """Test that user's address is properly saved and persisted"""
        logger.debug("Testing address persistence")
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
                logger.debug(f"Set session user_id to {self.user_id}")
            
            # Test address validation
            test_address = "1600 Amphitheatre Parkway, Mountain View, CA"
            logger.debug(f"Validating address: {test_address}")
            response = client.post('/validate_address', data={'address': test_address})
            self.assertEqual(response.status_code, 200)
            validation_result = json.loads(response.data)
            self.assertTrue(validation_result['valid'])
            logger.debug("Address validation successful")
            
            # Save address
            logger.debug("Saving address to user profile")
            response = client.post('/personal_info', data={
                'name': 'Test User',
                'home_address': test_address
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify address was saved
            db_session = Session()
            try:
                user = db_session.query(User).filter_by(id=self.user_id).first()
                self.assertEqual(user.home_address, "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA")
                self.assertIsNotNone(user.home_latitude)
                self.assertIsNotNone(user.home_longitude)
                logger.debug("Address saved and verified successfully")
            finally:
                db_session.close()
            
            # Verify session data
            with client.session_transaction() as sess:
                self.assertEqual(sess.get('user_address'), "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA")
                logger.debug("Session address data verified")

    def test_session_after_refresh(self):
        """Test that session persists after page refresh"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
                sess['user_name'] = 'Test User'
                sess['user_address'] = '1600 Amphitheatre Parkway, Mountain View, CA'
            
            # Simulate page refresh
            response = client.get('/errands')
            self.assertEqual(response.status_code, 200)
            
            # Verify session data
            with client.session_transaction() as sess:
                self.assertIn('user_id', sess)
                self.assertIn('user_name', sess)
                self.assertIn('user_address', sess)
                self.assertEqual(sess['user_id'], self.user_id)
                self.assertEqual(sess['user_name'], 'Test User')
                self.assertEqual(sess['user_address'], '1600 Amphitheatre Parkway, Mountain View, CA')

    def test_invalid_session_handling(self):
        """Test handling of invalid session data"""
        with self.app as client:
            # Simulate invalid session
            with client.session_transaction() as sess:
                sess['user_id'] = 999999  # Non-existent user ID
            
            # Should redirect to login
            response = client.get('/errands')
            self.assertEqual(response.status_code, 302)
            self.assertTrue('/login' in response.location)
            
            # Verify session was cleared
            with client.session_transaction() as sess:
                self.assertNotIn('user_id', sess)

    def test_address_update_consistency(self):
        """Test that address updates are consistent across database and session"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Update address
            new_address = "1 Hacker Way, Menlo Park, CA"
            response = client.post('/personal_info', data={
                'name': 'Test User',
                'home_address': new_address
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify database update
            db_session = Session()
            try:
                user = db_session.query(User).filter_by(id=self.user_id).first()
                self.assertEqual(user.home_address, "1 Hacker Wy, Menlo Park, CA 94025, USA")
            finally:
                db_session.close()
            
            # Verify session update
            with client.session_transaction() as sess:
                self.assertEqual(sess.get('user_address'), "1 Hacker Wy, Menlo Park, CA 94025, USA")
            
            # Verify persistence after new request
            response = client.get('/errands', follow_redirects=True)
            with client.session_transaction() as sess:
                self.assertEqual(sess.get('user_address'), "1 Hacker Wy, Menlo Park, CA 94025, USA")

    def test_home_address_validation(self):
        """Test home address validation and saving"""
        # Simulate login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.user_id
        
        # Test invalid address
        response = self.app.post('/personal_info', data={
            'name': 'Test User',
            'home_address': ' '
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid address', response.data)
        
        # Test valid address
        response = self.app.post('/personal_info', data={
            'name': 'Test User',
            'home_address': '1600 Amphitheatre Parkway, Mountain View, CA'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify address was saved
        user = self.db_session.query(User).filter_by(id=self.user_id).first()
        self.assertIsNotNone(user.home_address)
        self.assertIsNotNone(user.home_latitude)
        self.assertIsNotNone(user.home_longitude)
    
    def test_errand_creation(self):
        """Test errand creation with various scenarios"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Test basic errand creation
            response = client.post('/errands', data={
                'title': 'Test Errand Creation 1',
                'location_type': 'name',
                'location_name': 'Test Location',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '30',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Errand created successfully')
            
            # Verify errand was created
            errand = self.db_session.query(Errand).filter_by(title='Test Errand Creation 1').first()
            self.assertIsNotNone(errand)
            self.assertEqual(errand.location_type, 'name')
            self.assertEqual(errand.location_name, 'Test Location')
            self.assertEqual(errand.priority, 3)  # Default priority
            
            # Test errand creation with empty complementary errands
            response = client.post('/errands', data={
                'title': 'Test Errand 2',
                'location_type': 'name',
                'location_name': 'Test Location 2',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '30',
                'repetition': 'none',
                'complementary_errands[]': []
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Errand created successfully')
            
            # Verify errand was created with no complementary errands
            errand = self.db_session.query(Errand).filter_by(title='Test Errand 2').first()
            self.assertIsNotNone(errand)
            self.assertIsNone(errand.complementary_errands)
    
    def test_errand_relationships(self):
        """Test complementary errand relationships"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Create two errands with unique titles
            errand1 = Errand(
                user_id=self.user_id,
                title=f'Errand 1 - {datetime.now().timestamp()}',
                location_type='name',
                location_name='Location 1',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            errand2 = Errand(
                user_id=self.user_id,
                title=f'Errand 2 - {datetime.now().timestamp()}',
                location_type='name',
                location_name='Location 2',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            self.db_session.add(errand1)
            self.db_session.add(errand2)
            self.db_session.commit()
            
            # Store IDs for later use
            errand1_id = errand1.id
            errand2_id = errand2.id
            
            # Test setting complementary relationship
            response = client.put(f'/errands/{errand1_id}', data={
                'title': errand1.title,  # Use the same unique title
                'location_type': 'name',
                'location_name': 'Location 1',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '30',
                'repetition': 'none',
                'complementary_errands[]': [str(errand2_id)]
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify relationship was set up correctly
            new_session = Session()
            try:
                errand1 = new_session.query(Errand).filter_by(id=errand1_id).first()
                errand2 = new_session.query(Errand).filter_by(id=errand2_id).first()
                self.assertIn(str(errand2_id), errand1.complementary_errands.split(','))
                self.assertIn(str(errand1_id), errand2.complementary_errands.split(','))
            finally:
                new_session.close()
            
            # Test removing complementary relationship
            response = client.put(f'/errands/{errand1_id}', data={
                'title': errand1.title,  # Use the same unique title
                'location_type': 'name',
                'location_name': 'Location 1',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '30',
                'repetition': 'none',
                'complementary_errands[]': []
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify relationship was removed
            new_session = Session()
            try:
                errand1 = new_session.query(Errand).filter_by(id=errand1_id).first()
                errand2 = new_session.query(Errand).filter_by(id=errand2_id).first()
                self.assertTrue(errand1.complementary_errands is None)
                if errand2.complementary_errands is not None:
                    self.assertNotIn(str(errand1_id), errand2.complementary_errands.split(','))

            finally:
                new_session.close()
            
            # Clean up
            client.delete(f'/errands/{errand1_id}', follow_redirects=True)
            client.delete(f'/errands/{errand2_id}', follow_redirects=True)
    
    def test_errand_validation(self):
        """Test errand validation"""
        # Simulate login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.user_id
        
        # Test missing required fields
        response = self.app.post('/errands', data={
            'title': 'Test Errand',
            'location_type': 'name',
            'location_name': 'Test Location'
        })
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Missing required fields: access_type, valid_start_window, valid_end_window, estimated_duration')
        
        # Test invalid access type
        response = self.app.post('/errands', data={
            'title': 'Test Errand',
            'location_type': 'name',
            'location_name': 'Test Location',
            'access_type': 'invalid',
            'valid_start_window': '0900',
            'valid_end_window': '1700',
            'estimated_duration': '30',
            'repetition': 'none'
        })
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid access type')
        
        # Test invalid time format
        response = self.app.post('/errands', data={
            'title': 'Test Errand',
            'location_type': 'name',
            'location_name': 'Test Location',
            'access_type': 'drive',
            'valid_start_window': 'invalid',
            'valid_end_window': '1700',
            'estimated_duration': '30',
            'repetition': 'none'
        })
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid time format')
    
    def test_errand_deletion(self):
        """Test errand deletion and relationship cleanup"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Create two errands with complementary relationship
            errand1 = Errand(
                user_id=self.user_id,
                title='Errand 1',
                location_type='name',
                location_name='Location 1',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            errand2 = Errand(
                user_id=self.user_id,
                title='Errand 2',
                location_type='name',
                location_name='Location 2',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            self.db_session.add(errand1)
            self.db_session.add(errand2)
            self.db_session.commit()
            
            # Set up complementary relationship
            errand1.complementary_errands = str(errand2.id)
            errand2.complementary_errands = str(errand1.id)
            self.db_session.commit()
            
            # Store IDs before deletion
            errand1_id = errand1.id
            errand2_id = errand2.id
            
            # Delete first errand
            response = client.delete(f'/errands/{errand1_id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Refresh session and verify errand was deleted
            self.db_session.expire_all()
            self.assertIsNone(self.db_session.query(Errand).filter_by(id=errand1_id).first())
            
            # Verify relationship was cleaned up
            errand2 = self.db_session.query(Errand).filter_by(id=errand2_id).first()
            self.assertIsNotNone(errand2)
            self.assertIsNone(errand2.complementary_errands)

    def test_errand_comprehensive_update(self):
        """Test comprehensive errand updates and duplicate title validation"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Create initial errand
            errand = Errand(
                user_id=self.user_id,
                title=f'Initial Errand - {datetime.now().timestamp()}',
                location_type='name',
                location_name='Location 1',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            self.db_session.add(errand)
            self.db_session.commit()
            
            # Store ID for later use
            errand_id = errand.id
            
            # Test comprehensive update
            response = client.put(f'/errands/{errand_id}', data={
                'title': f'Updated Errand - {datetime.now().timestamp()}',
                'location_type': 'address',
                'location_address': '1 Hacker Way, Menlo Park, CA',
                'access_type': 'walk',
                'valid_start_window': '1000',
                'valid_end_window': '1800',
                'estimated_duration': '45',
                'repetition': 'weekly',
                'starting_monday': '2024-05-06'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify updates
            new_session = Session()
            try:
                updated_errand = new_session.query(Errand).filter_by(id=errand_id).first()
                self.assertIsNotNone(updated_errand)
                self.assertEqual(updated_errand.location_type, 'address')
                self.assertEqual(updated_errand.location_address, '1 Hacker Way, Menlo Park, CA')
                self.assertEqual(updated_errand.access_type, 'walk')
                self.assertEqual(updated_errand.valid_start_window, '1000')
                self.assertEqual(updated_errand.valid_end_window, '1800')
                self.assertEqual(updated_errand.estimated_duration, 45)
                self.assertEqual(updated_errand.repetition, 'weekly')
                self.assertEqual(updated_errand.starting_monday, date(2024, 5, 6))
            finally:
                new_session.close()
            
            # Clean up
            client.delete(f'/errands/{errand_id}', follow_redirects=True)

    def test_flexible_time_ranges(self):
        """Test flexible time range functionality"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Test errand with flexible start time
            response = client.post('/errands', data={
                'title': 'Flexible Start Test 1',
                'location_type': 'name',
                'location_name': 'Test Location',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'flexible_start_window': 'true',
                'estimated_duration': '30',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Errand created successfully')
            
            # Verify flexible start time was saved
            errand = self.db_session.query(Errand).filter_by(title='Flexible Start Test 1').first()
            self.assertIsNotNone(errand)
            self.assertTrue(errand.flexible_start_window)
            self.assertFalse(errand.flexible_end_window)
            self.assertFalse(errand.flexible_duration)
            
            # Test errand with flexible duration
            response = client.post('/errands', data={
                'title': 'Flexible Duration Test 1',
                'location_type': 'name',
                'location_name': 'Test Location',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'flexible_duration': 'true',
                'min_duration': '20',
                'max_duration': '40',
                'estimated_duration': '30',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Errand created successfully')
            
            # Verify flexible duration was saved
            errand = self.db_session.query(Errand).filter_by(title='Flexible Duration Test 1').first()
            self.assertIsNotNone(errand)
            self.assertTrue(errand.flexible_duration)
            self.assertEqual(errand.min_duration, 20)
            self.assertEqual(errand.max_duration, 40)
            
            # Test errand with all flexible times
            response = client.post('/errands', data={
                'title': 'Fully Flexible Test 1',
                'location_type': 'name',
                'location_name': 'Test Location',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'flexible_start_window': 'true',
                'flexible_end_window': 'true',
                'flexible_duration': 'true',
                'min_duration': '20',
                'max_duration': '40',
                'estimated_duration': '30',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['message'], 'Errand created successfully')
            
            # Verify all flexible times were saved
            errand = self.db_session.query(Errand).filter_by(title='Fully Flexible Test 1').first()
            self.assertIsNotNone(errand)
            self.assertTrue(errand.flexible_start_window)
            self.assertTrue(errand.flexible_end_window)
            self.assertTrue(errand.flexible_duration)
            self.assertEqual(errand.min_duration, 20)
            self.assertEqual(errand.max_duration, 40)
            
            # Clean up
            client.delete(f'/errands/{errand.id}', follow_redirects=True)
            errand = self.db_session.query(Errand).filter_by(title='Flexible Start Test 1').first()
            if errand:
                client.delete(f'/errands/{errand.id}', follow_redirects=True)
            errand = self.db_session.query(Errand).filter_by(title='Flexible Duration Test 1').first()
            if errand:
                client.delete(f'/errands/{errand.id}', follow_redirects=True)

    def test_location_type_refinements(self):
        """Test location type refinements functionality"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Test remote errand
            response = client.post('/errands', data={
                'title': 'Remote Meeting Test 1',
                'location_type': 'name',
                'location_name': 'Zoom Meeting',
                'is_remote': 'true',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1000',
                'estimated_duration': '60',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('message', data)
            
            # Test exact location vs store name
            response = client.post('/errands', data={
                'title': 'Grocery Shopping',
                'location_type': 'name',
                'location_name': 'Whole Foods',
                'use_exact_location': 'false',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1000',
                'estimated_duration': '60',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('message', data)
            
            # Test multiple location options
            alternative_locations = [
                {'name': 'Whole Foods', 'address': '123 Main St'},
                {'name': 'Trader Joes', 'address': '456 Oak St'}
            ]
            response = client.post('/errands', data={
                'title': 'Grocery Shopping',
                'location_type': 'name',
                'location_name': 'Whole Foods',
                'use_exact_location': 'false',
                'alternative_locations': json.dumps(alternative_locations),
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1000',
                'estimated_duration': '60',
                'repetition': 'none'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('message', data)
            
            # Test validation
            response = client.post('/errands', data={
                'title': 'Invalid Remote',
                'location_type': 'address',
                'location_address': '123 Main St',
                'is_remote': 'true',
                'access_type': 'drive',
                'valid_start_window': '0900',
                'valid_end_window': '1000',
                'estimated_duration': '60',
                'repetition': 'none'
            })
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertIn('error', data)
            self.assertIn('Remote errands must use location type "name"', data['error'])

    def test_complementary_errands(self):
        """Test complementary errand functionality"""
        logger.debug("Testing complementary errands functionality")
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
                logger.debug(f"Set session user_id to {self.user_id}")
            
            # Create first errand
            logger.debug("Creating first errand (Grocery Shopping)")
            response = client.post('/errands', data={
                'title': 'Grocery Shopping Test 1',
                'location_type': 'name',
                'location_name': 'Whole Foods',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '60',
                'repetition': 'weekly',
                'valid_days': 'monday,wednesday,friday',
                'access_type': 'drive'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('message', response.json)
            logger.debug("First errand created successfully")
            
            # Get the first errand ID from the database
            first_errand = self.db_session.query(Errand).filter_by(title='Grocery Shopping Test 1').first()
            self.assertIsNotNone(first_errand)
            first_errand_id = first_errand.id
            logger.debug(f"First errand ID: {first_errand_id}")
            
            # Create second errand with same-day requirement
            logger.debug("Creating second errand (Pharmacy Visit) with same-day requirement")
            response = client.post('/errands', data={
                'title': 'Pharmacy Visit Test 1',
                'location_type': 'name',
                'location_name': 'CVS',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '30',
                'repetition': 'weekly',
                'valid_days': 'monday,wednesday,friday',
                'access_type': 'drive',
                'complementary_errands[]': str(first_errand_id),
                'same_day_required': 'true'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertIn('message', response.json)
            logger.debug("Second errand created successfully")
            
            # Get the second errand ID from the database
            second_errand = self.db_session.query(Errand).filter_by(title='Pharmacy Visit Test 1').first()
            self.assertIsNotNone(second_errand)
            second_errand_id = second_errand.id
            logger.debug(f"Second errand ID: {second_errand_id}")
            
            # Create third errand with order requirement
            logger.debug("Creating third errand (Bank Visit) with order requirement")
            response = client.post('/errands', data={
                'title': 'Bank Visit Test 1',
                'location_type': 'name',
                'location_name': 'Bank of America',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '45',
                'repetition': 'weekly',
                'valid_days': 'monday,wednesday,friday',
                'access_type': 'drive',
                'complementary_errands[]': [str(first_errand_id), str(second_errand_id)],
                'order_required': 'true'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('message', response.json)
            logger.debug("Third errand created successfully")
            
            # Get the third errand ID from the database
            third_errand = self.db_session.query(Errand).filter_by(title='Bank Visit Test 1').first()
            self.assertIsNotNone(third_errand)
            third_errand_id = third_errand.id
            logger.debug(f"Third errand ID: {third_errand_id}")
            
            # Create fourth errand with same-location requirement
            logger.debug("Creating fourth errand (Grocery Shopping 2) with same-location requirement")
            response = client.post('/errands', data={
                'title': 'Grocery Shopping Test 2',
                'location_type': 'name',
                'location_name': 'Whole Foods',
                'valid_start_window': '0900',
                'valid_end_window': '1700',
                'estimated_duration': '60',
                'repetition': 'weekly',
                'valid_days': 'monday,wednesday,friday',
                'access_type': 'drive',
                'complementary_errands[]': [str(first_errand_id)],
                'same_location_required': 'true',
                'is_remote': 'false',
                'use_exact_location': 'true'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('message', response.json)
            logger.debug("Fourth errand created successfully")
            
            # Clean up
            logger.debug("Cleaning up test errands")
            client.delete(f'/errands/{first_errand_id}', follow_redirects=True)
            client.delete(f'/errands/{second_errand_id}', follow_redirects=True)
            client.delete(f'/errands/{third_errand_id}', follow_redirects=True)
            logger.debug("Test cleanup completed")

    def test_conflicting_errands(self):
        """Test conflicting errand functionality"""
        with self.app as client:
            # Simulate login
            with client.session_transaction() as sess:
                sess['user_id'] = self.user_id
            
            # Create first errand
            errand1 = Errand(
                user_id=self.user_id,
                title=f'Conflicting Errand 1 - {datetime.now().timestamp()}',
                location_type='name',
                location_name='Location 1',
                access_type='drive',
                valid_start_window='0900',
                valid_end_window='1700',
                estimated_duration=30,
                repetition='none'
            )
            self.db_session.add(errand1)
            self.db_session.commit()
            
            # Store errand ID for later use
            errand1_id = errand1.id
            
            # Create second errand with overlapping time
            response = client.post('/errands', data={
                'title': f'Conflicting Errand 2 - {datetime.now().timestamp()}',
                'location_type': 'name',
                'location_name': 'Location 2',
                'access_type': 'drive',
                'valid_start_window': '1000',
                'valid_end_window': '1800',
                'estimated_duration': '30',
                'repetition': 'none',
                'date': '2024-05-06'  # Add specific date to check conflicts
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Clean up - use the stored ID instead of the detached object
            response = client.delete(f'/errands/{errand1_id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify errand was deleted
            deleted_errand = self.db_session.query(Errand).filter_by(id=errand1_id).first()
            self.assertIsNone(deleted_errand)

    def test_index_redirects_to_errands(self):
        """Test that index redirects to errands when user is authenticated"""
        # Set up user with address
        self.test_user.home_address = "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
        self.test_user.home_latitude = 37.4220
        self.test_user.home_longitude = -122.0841
        self.db_session.commit()
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.user_id
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/errands')
    
    def test_index_redirects_to_personal_info(self):
        """Test that index redirects to personal info when user has no address"""
        # Clear user's address
        self.test_user.home_address = None
        self.test_user.home_latitude = None
        self.test_user.home_longitude = None
        self.db_session.commit()
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.user_id
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/personal_info')

if __name__ == '__main__':
    unittest.main() 