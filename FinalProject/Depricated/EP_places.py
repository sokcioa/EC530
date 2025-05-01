#!/usr/bin/env python3

import os
import socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import logging

# Configure socket to prefer IPv6 but use stable addresses
socket.AF_INET6 = socket.AF_INET6  # Revert back to IPv6
socket.IPPROTO_IPV6 = socket.IPPROTO_IPV6

logger = logging.getLogger(__name__)

class PlacesAPI:
    def __init__(self, api_key=None):
        """Initialize the Places API client"""
        load_dotenv()
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
            request = {
                'placeId': place_id,
                'fields': ['id', 'displayName', 'formattedAddress', 'location', 'website', 'phoneNumber']
            }
            
            response = self.service.places().get(name=f'places/{place_id}').execute()
            
            return {
                'name': response.get('displayName', {}).get('text', ''),
                'address': response.get('formattedAddress', ''),
                'location': response.get('location', {}),
                'website': response.get('website', ''),
                'phone': response.get('phoneNumber', '')
            }
        except HttpError as e:
            print(f"Error getting place details: {e}")
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
                return result
            
            # If no exact match, try more flexible search
            logger.debug(f"No exact match, trying flexible search for: {address}")
            result = self.search_place(address, location, strict=False)
            if result:
                logger.debug(f"Found flexible match for address: {address}")
                return result
            
            logger.debug(f"No matches found for address: {address}")
            return None
        except Exception as e:
            logger.error(f"Error validating address: {str(e)}")
            return None 