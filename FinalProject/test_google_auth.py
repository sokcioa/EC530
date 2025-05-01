#!/usr/bin/env python3

import unittest
import os
from api.google_auth import GoogleAuth, google_auth_bp
from flask import Flask, session, url_for, redirect, request
from unittest.mock import patch, MagicMock

class TestGoogleAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests"""
        # Create a test Flask app
        cls.app = Flask(__name__)
        cls.app.secret_key = 'test_secret_key'
        cls.client = cls.app.test_client()
        
        # Register the Blueprint
        cls.app.register_blueprint(google_auth_bp)
        
        # Initialize auth with test credentials file
        cls.auth = GoogleAuth(credentials_file='api/googleOauth2Credentials.json')
        
    def setUp(self):
        """Set up test fixtures before each test"""
        # Clear any existing credentials before tests
        self.auth.clear_credentials()
        
    def test_initialization(self):
        """Test initialization with default scopes"""
        self.assertEqual(self.auth.scopes, GoogleAuth.SCOPES)
        
    def test_custom_scopes(self):
        """Test initialization with custom scopes"""
        custom_scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        auth = GoogleAuth(scopes=custom_scopes)
        self.assertEqual(auth.scopes, custom_scopes)
        
    def test_get_auth_url(self):
        """Test getting authorization URL and OAuth flow"""
        with self.app.test_request_context():
            # Get auth URL - this will open the browser for actual sign-in
            auth_url = self.auth.get_auth_url()
            self.assertIsNotNone(auth_url)
            self.assertIn('https://accounts.google.com/o/oauth2', auth_url)
            self.assertIn('state', session)
            
            # Print instructions for manual testing
            print("\nTo complete the OAuth test:")
            print("1. Open this URL in your browser:", auth_url)
            print("2. Sign in with your Google account")
            print("3. After authorization, you'll be redirected back to the application")
            print("4. The test will verify the callback and credentials")
            
    def test_verify_calendar_access(self):
        """Test calendar access verification"""
        self.assertTrue(self.auth.verify_calendar_access())
        
    def test_clear_credentials(self):
        """Test clearing credentials"""
        # Set some test credentials
        self.auth.credentials = "test_credentials"
        self.auth.flow = "test_flow"
        
        # Clear credentials
        self.auth.clear_credentials()
        
        # Verify they are cleared
        self.assertIsNone(self.auth.credentials)
        self.assertIsNone(self.auth.flow)
            
    def test_credentials_file_path(self):
        """Test credentials file path handling"""
        # Test with default path
        auth = GoogleAuth()
        # Get the actual path that was set
        actual_path = auth.credentials_file
        # Verify it's an absolute path and ends with the correct filename
        self.assertTrue(os.path.isabs(actual_path))
        self.assertTrue(actual_path.endswith('api/googleOauth2Credentials.json'))
        
        # Test with custom path
        custom_path = 'custom_credentials.json'
        auth = GoogleAuth(credentials_file=custom_path)
        self.assertEqual(auth.credentials_file, custom_path)

if __name__ == '__main__':
    unittest.main() 