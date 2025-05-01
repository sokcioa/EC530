from models import User
from api.places import PlacesAPI
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from flask import session
import re
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, session: Session, places_api: PlacesAPI):
        self.session = session
        self.places_api = places_api

    def standardize_address(self, address: str) -> str:
        """Standardize address format while preserving zip codes and country"""
        if not address:
            return address
            
        # First, try to validate and get the full address from Places API
        try:
            validated_address = self.places_api.validate_address(address)
            if validated_address:
                # Use the Places API's address which includes zip and country
                return validated_address.get('address', address)
        except Exception:
            pass
            
        # If Places API fails, do basic standardization
        address = address.replace("Way", "Wy")
        address = address.replace("Parkway", "Pkwy")
        address = address.replace("Street", "St")
        address = address.replace("Avenue", "Ave")
        address = address.replace("Boulevard", "Blvd")
        address = address.replace("Drive", "Dr")
        address = address.replace("Road", "Rd")
        address = address.replace("Lane", "Ln")
        address = address.replace("Circle", "Cir")
        address = address.replace("Court", "Ct")
        address = address.replace("Place", "Pl")
        address = address.replace("Square", "Sq")
        address = address.replace("Terrace", "Ter")
        address = address.replace("Trail", "Trl")
        address = address.replace("Highway", "Hwy")
        
        # Ensure USA suffix if not present
        if not address.endswith("USA"):
            address = f"{address}, USA"
            
        return address

    def validate_address(self, address: str) -> Dict[str, Any]:
        """Validate an address using the Places API"""
        try:
            if not address:
                return {
                    'valid': False,
                    'message': 'Address is required'
                }
            
            # Validate address using Places API
            result = self.places_api.validate_address(address)
            if not result:
                return {
                    'valid': False,
                    'message': 'Failed to validate address'
                }
            
            if not result['valid']:
                return result
            
            # Standardize the address
            standardized_address = self.standardize_address(result['address'])
            
            return {
                'valid': True,
                'address': standardized_address,
                'lat': result['lat'],
                'lng': result['lng']
            }
        except Exception as e:
            logger.error(f"Error validating address: {str(e)}")
            return {
                'valid': False,
                'message': str(e)
            }

    def get_user(self, user_id: Optional[int] = None) -> Optional[User]:
        """Get a user by ID or the first user if no ID is provided"""
        if user_id:
            return self.session.query(User).filter_by(id=user_id).first()
        return self.session.query(User).first()

    def create_user(self, email: str, name: str, home_address: Optional[str] = None,
                   home_latitude: Optional[float] = None, home_longitude: Optional[float] = None) -> User:
        """Create a new user"""
        if home_address:
            # Validate and standardize address
            validation_result = self.validate_address(home_address)
            if validation_result["valid"]:
                home_address = validation_result["address"]
                # Update coordinates if available
                if validation_result.get("location"):
                    home_latitude = validation_result["location"].get("latitude", home_latitude)
                    home_longitude = validation_result["location"].get("longitude", home_longitude)
            else:
                home_address = self.standardize_address(home_address)
            
        user = User(
            email=email,
            name=name,
            home_address=home_address,
            home_latitude=home_latitude,
            home_longitude=home_longitude
        )
        self.session.add(user)
        self.session.commit()
        
        # Update session with address if provided
        if home_address:
            session['user_address'] = home_address
            
        return user

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update a user with the given fields"""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    if key == 'home_address' and value:
                        # Validate and standardize address
                        validation_result = self.validate_address(value)
                        if validation_result["valid"]:
                            # Use the validated address
                            value = validation_result["address"]
                            # Update coordinates if available
                            if validation_result.get("location"):
                                user.home_latitude = validation_result["location"].get("latitude")
                                user.home_longitude = validation_result["location"].get("longitude")
                        else:
                            # If validation fails, use standardized address
                            value = self.standardize_address(value)
                    setattr(user, key, value)
            
            # Update session data if address is updated
            if 'home_address' in kwargs:
                session['user_address'] = user.home_address  # Use the final address value
            
            self.session.commit()
            return user
        return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID"""
        user = self.get_user(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return self.session.query(User).filter_by(id=user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return self.session.query(User).filter_by(email=email).first() 