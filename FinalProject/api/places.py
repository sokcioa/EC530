#!/usr/bin/env python3

import os
import socket
import logging
from flask import Blueprint, jsonify, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, List, Optional, Tuple
from api.base import get_db
from EP_database import User
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logs_dir = os.path.join(project_root, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Add file handler
file_handler = RotatingFileHandler(
    os.path.join(logs_dir, 'places_api.log'),
    maxBytes=10240,
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(file_handler)

# Configure socket to prefer IPv6 but use stable addresses
socket.AF_INET6 = socket.AF_INET6  # Revert back to IPv6
socket.IPPROTO_IPV6 = socket.IPPROTO_IPV6

# Load environment variables
load_dotenv()

class PlacesAPI:
    def __init__(self, api_key=None):
        """Initialize the Places API client"""
        self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("Google Places API key is required")
        
        # Configure the API client with IPv6 support
        self.service = build('places', 'v1', 
                           developerKey=self.api_key,
                           static_discovery=True,  # Use static discovery to avoid dynamic IP issues
                           cache_discovery=True)   # Enable caching to maintain stable connections
    
    def search_place(self, query, location=None, strict=True):
        """
        Search for a place using the Places API
        
        Args:
            query (str): The search query
            location (tuple): Optional (latitude, longitude) for location bias
            strict (bool): Whether to use strict matching
        
        Returns:
            dict: Place information or None if not found
        """
        try:
            logger.debug(f"Searching for place: {query}")
            request = {
                'textQuery': query,
                'maxResultCount': 1
            }
            
            if location:
                request['locationBias'] = {
                    'circle': {
                        'center': {
                            'latitude': location[0],
                            'longitude': location[1]
                        },
                        'radius': 5000  # 5km radius
                    }
                }
            
            response = self.service.places().searchText(
                body=request,
                fields='places.displayName,places.formattedAddress,places.location'
            ).execute()
            
            if not response or 'places' not in response or not response['places']:
                logger.debug(f"No places found for query: {query}")
                return None
            
            place = response['places'][0]
            logger.debug(f"Found place: {place.get('displayName', {}).get('text', '')}")
            
            return {
                'formatted_address': place.get('formattedAddress', ''),
                'location': place.get('location', {})
            }
        except Exception as e:
            logger.error(f"Error searching place: {str(e)}")
            return None
    
    def get_place_details(self, place_id):
        """
        Get detailed information about a specific place
        
        Args:
            place_id (str): The Google Places ID of the location
        
        Returns:
            dict: Detailed place information
        """
        try:
            response = self.service.places().get(
                name=f'places/{place_id}',
                fields='id,displayName,formattedAddress,location,website,phoneNumber'
            ).execute()
            
            return {
                'name': response.get('displayName', {}).get('text', ''),
                'address': response.get('formattedAddress', ''),
                'location': response.get('location', {}),
                'website': response.get('website', ''),
                'phone': response.get('phoneNumber', '')
            }
        except HttpError as e:
            logger.error(f"Error getting place details: {e}")
            return None
    
    def validate_address(self, address, location=None):
        """
        Validate an address using the Places API
        
        Args:
            address (str): The address to validate
            location (tuple): Optional (latitude, longitude) for location bias
        
        Returns:
            dict: Validation result with formatted address and location
        """
        try:
            logger.debug(f"Validating address: {address}")
            # First try exact address search
            result = self.search_place(address, location, strict=True)
            if result:
                logger.debug(f"Found exact match for address: {address}")
                return {
                    'valid': True,
                    'address': result['formatted_address'],
                    'lat': result['location'].get('latitude', 0),
                    'lng': result['location'].get('longitude', 0)
                }
            
            # If no exact match, try more flexible search
            logger.debug(f"No exact match, trying flexible search for: {address}")
            result = self.search_place(address, location, strict=False)
            if result:
                logger.debug(f"Found flexible match for address: {address}")
                return {
                    'valid': True,
                    'address': result['formatted_address'],
                    'lat': result['location'].get('latitude', 0),
                    'lng': result['location'].get('longitude', 0)
                }
            
            logger.debug(f"No matches found for address: {address}")
            return {
                'valid': False,
                'message': 'Address not found'
            }
        except Exception as e:
            logger.error(f"Error validating address: {str(e)}")
            return {
                'valid': False,
                'message': str(e)
            }

# Initialize Places API client
places_api = PlacesAPI()

places_bp = Blueprint('places', __name__)

@places_bp.route('/api/places/search', methods=['GET'])
def search_places():
    """Search for places using Google Places API"""
    query = request.args.get('query')
    location = request.args.get('location')
    strict = request.args.get('strict', 'true').lower() == 'true'
    
    if not query or not location:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Convert location string to lat,lng tuple
        lat, lng = map(float, location.split(','))
        
        # Search for places
        result = places_api.search_place(query, (lat, lng), strict)
        
        if not result:
            return jsonify({'error': 'No places found'}), 404
        
        return jsonify(result)
    
    except ValueError as e:
        logger.error(f"Error in search_places: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error in search_places: {str(e)}")
        return jsonify({'error': str(e)}), 500

@places_bp.route('/api/places/details', methods=['GET'])
def get_place_details():
    """Get detailed information about a place"""
    place_id = request.args.get('place_id')
    
    if not place_id:
        return jsonify({'error': 'Missing place_id parameter'}), 400
    
    try:
        result = places_api.get_place_details(place_id)
        
        if not result:
            return jsonify({'error': 'Place not found'}), 404
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_place_details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@places_bp.route('/api/places/validate_address', methods=['POST'])
def validate_address():
    """Validate and geocode a user's address"""
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
        
    data = request.get_json()
    address = data.get('address')
    user_id = data.get('user_id')
    location = data.get('location')
    
    if not address or not user_id:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Convert location string to tuple if provided
        location_tuple = None
        if location:
            try:
                lat, lng = map(float, location.split(','))
                location_tuple = (lat, lng)
            except ValueError:
                return jsonify({'error': 'Invalid location format'}), 400
        
        # Validate address
        result = places_api.validate_address(address, location_tuple)
        
        if not result:
            return jsonify({'error': 'Address not found'}), 404
        
        # Update user's address in database
        db = next(get_db())
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            user.home_address = result['address']
            user.home_latitude = result['lat']
            user.home_longitude = result['lng']
            db.commit()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in validate_address: {str(e)}")
        return jsonify({'error': str(e)}), 500 