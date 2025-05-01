#!/usr/bin/env python3

import os
import pickle
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from flask import session, redirect, url_for, Blueprint, request, flash
from models import Session, get_session, cleanup_session
from EP_database import User

# Create Blueprint
google_auth_bp = Blueprint('google_auth', __name__)

class GoogleAuth:
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid',
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly'
    ]

    def __init__(self, scopes=None, credentials_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api/googleOauth2Credentials.json')):
        """Initialize GoogleAuth with optional custom scopes"""
        self.scopes = scopes or self.SCOPES
        self.credentials = None
        # Use absolute path for credentials file
        self.credentials_file = credentials_file
        self.flow = None

    def get_auth_url(self):
        """Get the authorization URL for OAuth2 flow"""
        self.flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=self.scopes,
            redirect_uri=url_for('oauth2callback', _external=True)
        )
        authorization_url, state = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        return authorization_url

    def get_credentials(self, auth_response_url):
        """Get credentials from the OAuth2 callback"""
        if not self.flow:
            self.flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.scopes,
                redirect_uri=url_for('google_auth.oauth2callback', _external=True)
            )
        
        self.flow.fetch_token(authorization_response=auth_response_url)
        self.credentials = self.flow.credentials
        return self.credentials

    def get_user_info(self, credentials):
        """Get user information from Google"""
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info

    def clear_credentials(self):
        """Clear stored credentials"""
        if os.path.exists('token.pickle'):
            os.remove('token.pickle')
        self.credentials = None
        self.flow = None

    def verify_calendar_access(self):
        """
        Verify if we have the necessary calendar access
        
        Returns:
            bool: True if we have calendar access, False otherwise
        """
        calendar_scopes = [
            'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        return all(scope in self.scopes for scope in calendar_scopes)

@google_auth_bp.route('/logout')
def logout():
    """Logout user and clear session"""
    auth = GoogleAuth()
    auth.clear_credentials()
    session.clear()
    return redirect(url_for('personal_info'))

def get_google_auth_token(scopes=None):
    """
    Helper function to get Google API auth token
    
    Args:
        scopes (list, optional): List of Google API scopes needed. Defaults to DEFAULT_SCOPES
        
    Returns:
        str: Valid access token for Google API
    """
    auth = GoogleAuth(scopes)
    credentials = auth.get_credentials()
    return credentials.token

if __name__ == "__main__":
    # Example usage
    try:
        # Create auth handler with default scopes
        auth = GoogleAuth()
        
        # Get credentials and verify access
        credentials = auth.get_credentials()
        
        # Check what access we have
        if auth.verify_calendar_access():
            print("✓ Calendar access granted")
        else:
            print("✗ Calendar access not available")
        
        # Get the token
        token = credentials.token
        print("\nSuccessfully obtained auth token!")
        print(f"Token: {token[:50]}...")  # Only show first 50 chars for security
        
    except Exception as e:
        print(f"Error getting auth token: {e}") 