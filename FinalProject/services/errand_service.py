from datetime import datetime, timedelta
from models import Errand
from api.places import PlacesAPI
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class ErrandService:
    def __init__(self, session: Session, places_api: PlacesAPI):
        self.session = session
        self.places_api = places_api

    def validate_location(self, location: str) -> Dict[str, Any]:
        """Validate a location using the Places API"""
        try:
            result = self.places_api.search_places(location)
            if result and len(result) > 0:
                place = result[0]
                return {
                    'valid': True,
                    'name': place['name'],
                    'address': place['formatted_address'],
                    'latitude': place['geometry']['location']['lat'],
                    'longitude': place['geometry']['location']['lng']
                }
            return {'valid': False, 'error': 'Location not found'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def validate_time_format(self, time_str: str) -> bool:
        """Validate time format (HHMM)"""
        try:
            if len(time_str) != 4:
                return False
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            return 0 <= hours <= 23 and 0 <= minutes <= 59
        except ValueError:
            return False

    def validate_errand(self, **kwargs) -> tuple[bool, Optional[str]]:
        """Validate errand data"""
        try:
            # Check required fields
            required_fields = ['title', 'location_type', 'access_type', 'valid_start_window', 
                             'valid_end_window', 'estimated_duration']
            
            # If date is provided, repetition is not required
            if not kwargs.get('date'):
                required_fields.append('repetition')
            
            missing_fields = [field for field in required_fields if not kwargs.get(field)]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Validate access type
            valid_access_types = ['drive', 'walk', 'bike', 'transit']
            if kwargs.get('access_type') not in valid_access_types:
                return False, "Invalid access type"
            
            # Validate time format
            try:
                int(kwargs.get('valid_start_window', ''))
                int(kwargs.get('valid_end_window', ''))
            except ValueError:
                return False, "Invalid time format"
            
            # Validate remote errands
            is_remote = kwargs.get('is_remote') == 'true' or kwargs.get('is_remote') is True
            if is_remote and kwargs.get('location_type') != 'name':
                return False, 'Remote errands must use location type "name"'
            
            # Validate location type and name/address
            location_type = kwargs.get('location_type')
            if location_type == 'name':
                if not kwargs.get('location_name'):
                    return False, 'Location name is required for location type "name"'
            elif location_type == 'address':
                if not kwargs.get('location_address'):
                    return False, 'Location address is required for location type "address"'
            else:
                return False, 'Invalid location type'
            
            # Validate conflicting errands
            conflicting_errands = kwargs.get('conflicting_errands')
            conflict_type = kwargs.get('conflict_type')
            if conflicting_errands and not conflict_type:
                return False, "Conflict type is required when specifying conflicting errands"
            if conflict_type and conflict_type not in ['time', 'location', 'both']:
                return False, "Invalid conflict type"
            
            return True, None
        except Exception as e:
            return False, str(e)

    def create_errand(self, **kwargs) -> Optional[Errand]:
        """Create a new errand"""
        try:
            # Handle alternative locations if provided
            alternative_locations = kwargs.pop('alternative_locations', None)
            if alternative_locations:
                try:
                    if isinstance(alternative_locations, str):
                        alternative_locations = json.loads(alternative_locations)
                    kwargs['alternative_locations'] = json.dumps(alternative_locations)
                except json.JSONDecodeError:
                    raise ValueError("Invalid alternative locations format")
            
            # Handle date fields
            date_fields = ['starting_monday']
            for field in date_fields:
                if field in kwargs:
                    if not kwargs[field]:  # If empty string or None
                        kwargs[field] = None
                    elif isinstance(kwargs[field], str):
                        try:
                            kwargs[field] = datetime.strptime(kwargs[field], '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError(f"Invalid {field} format. Use YYYY-MM-DD")
            
            # Validate the errand data
            is_valid, error = self.validate_errand(**kwargs)
            if not is_valid:
                raise ValueError(error)
            
            # Create the errand
            errand = Errand(**kwargs)
            self.session.add(errand)
            
            # Handle complementary errands if provided
            complementary_errands = kwargs.pop('complementary_errands', None)
            if complementary_errands is not None:
                success, error = errand.validate_complementary_errands(self.session, complementary_errands)
                if not success:
                    raise ValueError(error)
            
            # Handle conflicting errands if provided
            conflicting_errands = kwargs.pop('conflicting_errands', None)
            conflict_type = kwargs.pop('conflict_type', None)
            if conflicting_errands is not None:
                success, error = errand.validate_conflicting_errands(self.session, conflicting_errands)
                if not success:
                    raise ValueError(error)
                if conflict_type:
                    errand.conflict_type = conflict_type
            
            self.session.commit()
            return errand
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating errand: {str(e)}")
            raise e

    def update_errand(self, errand_id: int, complementary_errands: List[int] = None, **kwargs) -> Optional[Errand]:
        """Update an existing errand"""
        try:
            errand = self.get_errand_by_id(errand_id)
            if not errand:
                raise ValueError(f"Errand not found with ID: {errand_id}")
            
            # Handle date fields
            date_fields = ['starting_monday']
            for field in date_fields:
                if field in kwargs:
                    if not kwargs[field]:  # If empty string or None
                        kwargs[field] = None
                    elif isinstance(kwargs[field], str):
                        try:
                            kwargs[field] = datetime.strptime(kwargs[field], '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError(f"Invalid {field} format. Use YYYY-MM-DD")
            
            # Handle conflicting errands
            conflicting_errands = kwargs.pop('conflicting_errands', None)
            conflict_type = kwargs.pop('conflict_type', None)
            if conflicting_errands is not None:
                if isinstance(conflicting_errands, list):
                    if conflicting_errands:
                        errand.conflicting_errands = ','.join(str(id) for id in conflicting_errands)
                        if conflict_type:
                            errand.conflict_type = conflict_type
                    else:
                        errand.conflicting_errands = None
                        errand.conflict_type = None
                else:
                    errand.conflicting_errands = None
                    errand.conflict_type = None
            
            # Update the errand fields
            for key, value in kwargs.items():
                if hasattr(errand, key):
                    setattr(errand, key, value)
            
            # Handle complementary relationships in the same transaction
            if complementary_errands is not None:
                # First, remove this errand from all current complementary errands
                if errand.complementary_errands:
                    current_comps = [x for x in errand.complementary_errands.split(',') if x]
                    for comp_id in current_comps:
                        comp_errand = self.get_errand_by_id(int(comp_id))
                        if comp_errand:
                            comp_comps = [x for x in (comp_errand.complementary_errands or '').split(',') if x]
                            comp_comps = set(comp_comps)
                            comp_comps.discard(str(errand_id))
                            comp_errand.complementary_errands = None if not comp_comps else ','.join(comp_comps)
                            self.session.add(comp_errand)
                
                # Then update with new complementary errands
                if complementary_errands:
                    # Set new complementary errands
                    errand.complementary_errands = ','.join(str(id) for id in complementary_errands)
                    
                    # Add reciprocal relationships
                    for comp_id in complementary_errands:
                        comp_errand = self.get_errand_by_id(comp_id)
                        if comp_errand:
                            comp_comps = [x for x in (comp_errand.complementary_errands or '').split(',') if x]
                            comp_comps = set(comp_comps)
                            comp_comps.add(str(errand_id))
                            comp_errand.complementary_errands = ','.join(comp_comps)
                            self.session.add(comp_errand)
                else:
                    errand.complementary_errands = None
            
            self.session.commit()
            return errand
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating errand: {str(e)}")
            raise e

    def delete_errand(self, errand_id: int) -> bool:
        """Delete an errand and clean up its relationships"""
        try:
            errand = self.get_errand_by_id(errand_id)
            if not errand:
                raise ValueError(f"Errand not found with ID: {errand_id}")
            
            # Clean up complementary relationships
            if errand.complementary_errands:
                for comp_id in errand.complementary_errands.split(','):
                    if comp_id:
                        comp_errand = self.get_errand_by_id(int(comp_id))
                        if comp_errand:
                            comp_comps = set((comp_errand.complementary_errands or '').split(','))
                            comp_comps.discard(str(errand_id))
                            comp_comps.discard('')  # Remove any empty strings
                            comp_errand.complementary_errands = None if not comp_comps else ','.join(comp_comps)
                            self.session.add(comp_errand)
            
            # Clean up conflicting relationships
            if errand.conflicting_errands:
                for conflict_id in errand.conflicting_errands.split(','):
                    if conflict_id:
                        conflict_errand = self.get_errand_by_id(int(conflict_id))
                        if conflict_errand:
                            conflict_errands = set((conflict_errand.conflicting_errands or '').split(','))
                            conflict_errands.discard(str(errand.id))
                            conflict_errand.conflicting_errands = ','.join(conflict_errands) if conflict_errands else None
                            self.session.add(conflict_errand)
            
            self.session.delete(errand)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting errand: {str(e)}")
            raise e

    def get_errand_by_id(self, errand_id: int) -> Optional[Errand]:
        """Get an errand by ID"""
        return self.session.query(Errand).filter_by(id=errand_id).first()

    def get_user_errands(self, user_id: int) -> List[Errand]:
        """Get all errands for a user"""
        return self.session.query(Errand).filter_by(user_id=user_id).all()

    def add_complementary_errands(self, errand_id: int, complementary_ids: List[int]) -> bool:
        """Add complementary errands to an errand"""
        try:
            errand = self.get_errand_by_id(errand_id)
            if not errand:
                return False
            
            # Get current complementary errands, filtering out empty strings
            current_comps = [x for x in (errand.complementary_errands or '').split(',') if x]
            current_comps = set(current_comps)  # Convert to set after filtering
            
            # If no complementary IDs provided, clear all relationships
            if not complementary_ids:
                # First, clear reciprocal relationships
                if errand.complementary_errands:
                    # Get all complementary errands first
                    comp_ids = [x for x in errand.complementary_errands.split(',') if x]
                    
                    # Clear current errand's relationships
                    errand.complementary_errands = None
                    self.session.add(errand)
                    
                    # Update all complementary errands in a single transaction
                    for comp_id in comp_ids:
                        comp_errand = self.get_errand_by_id(int(comp_id))
                        if comp_errand:
                            # Remove this errand's ID from the complementary errand's list
                            comp_comps = [x for x in (comp_errand.complementary_errands or '').split(',') if x]
                            comp_comps = set(comp_comps)
                            comp_comps.discard(str(errand_id))
                            # If the set is empty after removal, set to None
                            comp_errand.complementary_errands = None if not comp_comps else ','.join(sorted(comp_comps))
                            self.session.add(comp_errand)
                    
                    # Commit all changes at once
                    try:
                        self.session.commit()
                        # Verify the changes were applied
                        for comp_id in comp_ids:
                            comp_errand = self.get_errand_by_id(int(comp_id))
                            if comp_errand:
                                # If complementary_errands is None or empty, that's fine
                                if comp_errand.complementary_errands and str(errand_id) in comp_errand.complementary_errands.split(','):
                                    self.session.rollback()
                                    logger.error(f"Failed to remove errand {errand_id} from complementary errand {comp_id}")
                                    return False
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"Error updating complementary relationships: {str(e)}")
                        return False
                else:
                    # If no complementary errands, just clear current errand
                    errand.complementary_errands = None
                    self.session.add(errand)
                    try:
                        self.session.commit()
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"Error clearing complementary relationships: {str(e)}")
                        return False
            else:
                # Convert new IDs to strings for comparison
                new_comps = set(str(id) for id in complementary_ids)
                
                # Find IDs to remove (in current but not in new)
                ids_to_remove = current_comps - new_comps
                
                # First, remove reciprocal relationships for IDs being removed
                for comp_id in ids_to_remove:
                    comp_errand = self.get_errand_by_id(int(comp_id))
                    if comp_errand:
                        # Explicitly remove this errand's ID from the complementary errand's list
                        comp_comps = [x for x in (comp_errand.complementary_errands or '').split(',') if x]
                        comp_comps = set(comp_comps)
                        comp_comps.discard(str(errand_id))
                        comp_errand.complementary_errands = None if not comp_comps else ','.join(comp_comps)
                        self.session.add(comp_errand)
                
                # Then update current errand's list with new IDs
                errand.complementary_errands = None if not new_comps else ','.join(new_comps)
                self.session.add(errand)
                
                # Finally, add reciprocal relationships for new IDs
                for comp_id in new_comps:
                    comp_errand = self.get_errand_by_id(int(comp_id))
                    if comp_errand:
                        comp_comps = [x for x in (comp_errand.complementary_errands or '').split(',') if x]
                        comp_comps = set(comp_comps)
                        comp_comps.add(str(errand_id))
                        comp_errand.complementary_errands = None if not comp_comps else ','.join(comp_comps)
                        self.session.add(comp_errand)
                
                # Commit all changes at once
                try:
                    self.session.commit()
                    # Verify the changes were applied
                    for comp_id in new_comps:
                        comp_errand = self.get_errand_by_id(int(comp_id))
                        if comp_errand:
                            if not comp_errand.complementary_errands or str(errand_id) not in comp_errand.complementary_errands.split(','):
                                self.session.rollback()
                                logger.error(f"Failed to add errand {errand_id} to complementary errand {comp_id}")
                                return False
                except Exception as e:
                    self.session.rollback()
                    logger.error(f"Error updating complementary relationships: {str(e)}")
                    return False
            
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding complementary errands: {str(e)}")
            return False

    def add_conflicting_errands(self, errand_id: int, conflicting_ids: List[int], conflict_type: str) -> bool:
        """Add conflicting errands to an errand"""
        try:
            errand = self.get_errand_by_id(errand_id)
            if not errand:
                return False
            
            # Validate conflict type
            if conflict_type not in ['time', 'location', 'both']:
                raise ValueError("Invalid conflict type")
            
            errand.conflicting_errands = ','.join(str(id) for id in conflicting_ids)
            errand.conflict_type = conflict_type
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e 