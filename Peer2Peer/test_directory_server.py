import socket
import json
import time
import threading
import unittest
import os
import sys
import logging
from typing import Dict, List, Optional

# Add the current directory to the path so we can import the directory_server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from directory_server import DirectoryServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectoryServerTest(unittest.TestCase):
    """Test suite for the Directory Server"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests run"""
        # Get server host and port from environment variables or use defaults
        cls.server_host = os.environ.get('DIRECTORY_SERVER_HOST', '127.0.0.1')
        cls.server_port = int(os.environ.get('DIRECTORY_SERVER_PORT', '5000'))
        
        # Check if we should start our own server or use an existing one
        cls.start_server = os.environ.get('START_SERVER', 'false').lower() == 'true'
        
        if cls.start_server:
            # Create a test registry file path
            cls.test_registry_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "test_directory_registry.json"
            )
            
            # Start the directory server in a separate thread
            cls.server = DirectoryServer(host=cls.server_host, port=cls.server_port)
            cls.server_thread = threading.Thread(target=cls.server.start)
            cls.server_thread.daemon = True  # Thread will exit when main thread exits
            cls.server_thread.start()
            
            # Give the server time to start
            time.sleep(1)
            
            # Backup the original registry file if it exists
            cls.original_registry_file = cls.server.registry_file
            cls.server.registry_file = cls.test_registry_file
            
            # Clear any existing test registry
            if os.path.exists(cls.test_registry_file):
                os.remove(cls.test_registry_file)
            
            logger.info(f"Started test directory server at {cls.server_host}:{cls.server_port}")
        else:
            # We'll use an existing server
            cls.server = None
            logger.info(f"Using existing directory server at {cls.server_host}:{cls.server_port}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        if cls.start_server and cls.server:
            # Restore the original registry file path
            cls.server.registry_file = cls.original_registry_file
            
            # Remove the test registry file
            if os.path.exists(cls.test_registry_file):
                os.remove(cls.test_registry_file)
    
    def setUp(self):
        """Set up test environment before each test"""
        # Clear any existing users if we have access to the server
        if self.server:
            self.server.users = {}
            self.server.ip_to_username = {}
            self.server._save_registry()
    
    def send_request(self, request: dict) -> dict:
        """Helper method to send a request to the directory server and get a response"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.server_host, self.server_port))
            client_socket.send(json.dumps(request).encode('utf-8'))
            response_data = client_socket.recv(4096).decode('utf-8')
            return json.loads(response_data)
        finally:
            client_socket.close()
    
    def test_register_user(self):
        """Test user registration functionality"""
        # Test registering a new user
        request = {
            'action': 'register',
            'username': 'testuser1',
            'ip': '192.168.1.100',
            'port': 8000,
            'profile': {'status': 'online', 'bio': 'Test user 1'}
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        self.assertIn('testuser1', response['message'])
        
        # If we have access to the server object, verify the user was added to the registry
        if self.server:
            self.assertIn('testuser1', self.server.users)
            self.assertEqual(self.server.users['testuser1']['ip'], '192.168.1.100')
            self.assertEqual(self.server.users['testuser1']['port'], 8000)
        
        # Test registering the same user with different IP/port (update)
        request = {
            'action': 'register',
            'username': 'testuser1',
            'ip': '192.168.1.101',
            'port': 8001,
            'profile': {'status': 'online', 'bio': 'Test user 1 updated'}
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        
        # If we have access to the server object, verify the user was updated
        if self.server:
            self.assertEqual(self.server.users['testuser1']['ip'], '192.168.1.101')
            self.assertEqual(self.server.users['testuser1']['port'], 8001)
        
        # Test registering with missing fields
        request = {
            'action': 'register',
            'username': 'testuser2',
            'ip': '192.168.1.102'
            # Missing port
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'error')
        self.assertIn('Missing required fields', response['message'])
    
    def test_query_users(self):
        """Test user querying functionality"""
        # Register multiple test users
        users = [
            {'username': 'alice', 'ip': '192.168.1.100', 'port': 8000},
            {'username': 'bob', 'ip': '192.168.1.101', 'port': 8001},
            {'username': 'charlie', 'ip': '192.168.1.102', 'port': 8002},
            {'username': 'dave', 'ip': '10.0.0.100', 'port': 9000}
        ]
        
        for user in users:
            request = {
                'action': 'register',
                'username': user['username'],
                'ip': user['ip'],
                'port': user['port']
            }
            self.send_request(request)
        
        # Test querying all users
        request = {
            'action': 'query',
            'query_type': 'all'
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        
        # We can't assume the exact number of users since we might be using an existing server
        # that already has users registered
        self.assertGreaterEqual(len(response['users']), 4)
        
        # Test querying by name
        request = {
            'action': 'query',
            'query_type': 'name',
            'search_term': 'alice'
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        self.assertGreaterEqual(len(response['users']), 1)
        
        # Test querying by IP
        request = {
            'action': 'query',
            'query_type': 'ip',
            'search_term': '10.0.0'
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        self.assertGreaterEqual(len(response['users']), 1)
        
        # Test general search
        request = {
            'action': 'query',
            'query_type': 'search',
            'search_term': 'bob'
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'success')
        self.assertGreaterEqual(len(response['users']), 1)
        
        # Test invalid query type
        request = {
            'action': 'query',
            'query_type': 'invalid_type'
        }
        
        response = self.send_request(request)
        self.assertEqual(response['status'], 'error')
        self.assertIn('Invalid query type', response['message'])
    
    @unittest.skipIf(lambda: os.environ.get('START_SERVER', 'false').lower() != 'true', 
                    "Skipping registry persistence test when using existing server")
    def test_registry_persistence(self):
        """Test that the registry is properly saved and loaded"""
        # Register a test user
        request = {
            'action': 'register',
            'username': 'persistuser',
            'ip': '192.168.1.200',
            'port': 8000
        }
        
        self.send_request(request)
        
        # Verify the registry file was created
        self.assertTrue(os.path.exists(self.test_registry_file))
        
        # Create a new server instance to test loading
        new_server = DirectoryServer(host=self.server_host, port=self.server_port + 1)
        new_server.registry_file = self.test_registry_file
        
        # Load the registry
        new_server._load_registry()
        
        # Verify the user was loaded
        self.assertIn('persistuser', new_server.users)
        self.assertEqual(new_server.users['persistuser']['ip'], '192.168.1.200')
        self.assertEqual(new_server.users['persistuser']['port'], 8000)
    
    @unittest.skipIf(lambda: os.environ.get('START_SERVER', 'false').lower() != 'true', 
                    "Skipping logging test when using existing server")
    def test_logging(self):
        """Test that events are properly logged"""
        # Register a user to generate logs
        request = {
            'action': 'register',
            'username': 'loguser',
            'ip': '192.168.1.300',
            'port': 8000
        }
        
        self.send_request(request)
        
        # Verify log file was created
        self.assertTrue(os.path.exists(self.server.log_file))
        
        # Read the log file
        with open(self.server.log_file, 'r') as f:
            log_content = f.read()
        
        # Check for log entries
        self.assertIn('USER_REGISTERED', log_content)
        self.assertIn('loguser', log_content)
        self.assertIn('192.168.1.300', log_content)
        self.assertIn('8000', log_content)
        
        # Query users to generate more logs
        request = {
            'action': 'query',
            'query_type': 'all'
        }
        
        self.send_request(request)
        
        # Read the log file again
        with open(self.server.log_file, 'r') as f:
            log_content = f.read()
        
        # Check for query log entries
        self.assertIn('USER_QUERY', log_content)
        self.assertIn('QUERY_RESULTS', log_content)

if __name__ == "__main__":
    unittest.main() 