#!/usr/bin/env python3

import os
import requests
import logging
from typing import Dict, Optional, Union, List
from flask import Blueprint, jsonify, request
from api.base import get_db
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create Blueprint
directions_bp = Blueprint('directions', __name__)

class DirectionsAPI:
    """Handles Google Directions API calls for route planning and accessibility testing"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Directions API client"""
        self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable is required")
        
        self.base_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.logger = logging.getLogger('ErrandPlanner.DirectionsAPI')
        
    def get_directions(self, 
                      origin: str, 
                      destination: str, 
                      mode: str = 'driving',
                      transit_mode: Optional[List[str]] = None,
                      alternatives: bool = False) -> Optional[Dict]:
        """
        Get directions between two locations using specified travel mode
        
        Args:
            origin: Starting location (address or coordinates)
            destination: Ending location (address or coordinates)
            mode: Travel mode (driving, walking, bicycling, transit)
            transit_mode: List of specific transit types to use (bus, subway, train, tram, rail)
            alternatives: Whether to return alternative routes
            
        Returns:
            Dict containing route information or None if no route found
        """
        try:
            params = {
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'alternatives': alternatives,
                'key': self.api_key
            }
            
            # Add transit mode filter if specified
            if mode == 'transit' and transit_mode:
                params['transit_mode'] = '|'.join(transit_mode)
            
            self.logger.debug(f"Requesting directions: {params}")
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                self.logger.warning(f"Directions API returned status: {data['status']}")
                return None
                
            # Extract relevant route information
            route = data['routes'][0]
            legs = route['legs'][0]
            
            result = {
                'distance': legs['distance']['value'] / 1609.34,  # Convert meters to miles
                'duration': legs['duration']['value'] / 60,  # Convert seconds to minutes
                'start_address': legs['start_address'],
                'end_address': legs['end_address'],
                'steps': legs['steps']
            }
            
            if mode == 'transit':
                # Add transit-specific information
                transit_details = []
                for step in legs['steps']:
                    if step['travel_mode'] == 'TRANSIT':
                        transit_details.append({
                            'line': step['transit_details']['line']['name'],
                            'type': step['transit_details']['line']['vehicle']['type'],
                            'departure_stop': step['transit_details']['departure_stop']['name'],
                            'arrival_stop': step['transit_details']['arrival_stop']['name']
                        })
                result['transit_details'] = transit_details
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error getting directions: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error parsing directions response: {str(e)}")
            return None
            
    def get_transit_directions(self,
                             origin: str,
                             destination: str,
                             transit_types: List[str],
                             alternatives: bool = False) -> Optional[Dict]:
        """
        Get directions using specific transit types
        
        Args:
            origin: Starting location
            destination: Ending location
            transit_types: List of transit types to use (bus, subway, train, tram, rail)
            alternatives: Whether to return alternative routes
            
        Returns:
            Dict containing route information or None if no route found
        """
        return self.get_directions(
            origin=origin,
            destination=destination,
            mode='transit',
            transit_mode=transit_types,
            alternatives=alternatives
        )
            
    def is_accessible(self, 
                     origin: str, 
                     destination: str, 
                     mode: str,
                     max_distance: Optional[float] = None) -> bool:
        """
        Check if a destination is accessible from origin using specified mode
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode to check
            max_distance: Optional maximum distance in miles
            
        Returns:
            bool indicating if destination is accessible
        """
        result = self.get_directions(origin, destination, mode)
        if not result:
            return False
            
        if max_distance and result['distance'] > max_distance:
            return False
            
        return True
        
    def get_accessible_modes(self, 
                           origin: str, 
                           destination: str,
                           max_distances: Dict[str, float] = None) -> Dict[str, bool]:
        """
        Check which travel modes are accessible between two locations
        
        Args:
            origin: Starting location
            destination: Ending location
            max_distances: Optional dict of max distances per mode in miles
            
        Returns:
            Dict mapping travel modes to accessibility status
        """
        if max_distances is None:
            max_distances = {
                'walking': 2.0,
                'bicycling': 5.0,
                'transit': 10.0,
                'driving': 50.0
            }
            
        modes = ['walking', 'bicycling', 'transit', 'driving']
        results = {}
        
        for mode in modes:
            results[mode] = self.is_accessible(
                origin, 
                destination, 
                mode,
                max_distances.get(mode)
            )
            
        return results

# API Routes
@directions_bp.route('/api/directions', methods=['GET'])
def get_directions():
    """Get directions between two locations"""
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        mode = request.args.get('mode', 'driving')
        transit_mode = request.args.getlist('transit_mode')
        alternatives = request.args.get('alternatives', 'false').lower() == 'true'
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
            
        # Validate travel mode
        valid_modes = ['driving', 'walking', 'bicycling', 'transit']
        if mode not in valid_modes:
            return jsonify({'error': f'Invalid travel mode. Must be one of: {", ".join(valid_modes)}'}), 400
            
        api = DirectionsAPI()
        result = api.get_directions(origin, destination, mode, transit_mode, alternatives)
        
        if not result:
            return jsonify({'error': 'No route found'}), 404
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_directions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@directions_bp.route('/api/directions/transit', methods=['GET'])
def get_transit_directions():
    """Get transit directions between two locations"""
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        transit_types = request.args.getlist('transit_types')
        alternatives = request.args.get('alternatives', 'false').lower() == 'true'
        
        if not origin or not destination or not transit_types:
            return jsonify({'error': 'Origin, destination, and transit_types are required'}), 400
            
        api = DirectionsAPI()
        result = api.get_transit_directions(origin, destination, transit_types, alternatives)
        
        if not result:
            return jsonify({'error': 'No route found'}), 404
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_transit_directions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@directions_bp.route('/api/directions/accessible', methods=['GET'])
def check_accessibility():
    """Check if a destination is accessible from origin"""
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        mode = request.args.get('mode', 'driving')
        max_distance = request.args.get('max_distance', type=float)
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
            
        api = DirectionsAPI()
        is_accessible = api.is_accessible(origin, destination, mode, max_distance)
        
        return jsonify({'accessible': is_accessible})
        
    except Exception as e:
        logger.error(f"Error in check_accessibility: {str(e)}")
        return jsonify({'error': str(e)}), 500

@directions_bp.route('/api/directions/accessible_modes', methods=['GET'])
def get_accessible_modes():
    """Get all accessible travel modes between two locations"""
    try:
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
            
        api = DirectionsAPI()
        result = api.get_accessible_modes(origin, destination)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_accessible_modes: {str(e)}")
        return jsonify({'error': str(e)}), 500 