from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Errand(Base):
    __tablename__ = 'errands'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    location_type = Column(String, nullable=False)  # 'name' or 'address'
    location_name = Column(String)  # For store names or remote locations
    location_address = Column(String)  # For exact addresses
    latitude = Column(Float)
    longitude = Column(Float)
    category = Column(String)  # For categorizing errands
    is_remote = Column(Boolean, default=False)  # Whether this is a remote errand
    use_exact_location = Column(Boolean, default=True)  # Whether to use exact location or just store name
    alternative_locations = Column(String)  # JSON string of alternative locations
    access_type = Column(String, nullable=False)  # 'drive', 'walk', 'bike', 'transit'
    valid_start_window = Column(String, nullable=False)  # Format: HHMM
    valid_end_window = Column(String, nullable=False)  # Format: HHMM
    estimated_duration = Column(Integer, nullable=False)  # In minutes
    repetition = Column(String, nullable=False)  # 'none', 'daily', 'weekly', 'biweekly', 'monthly'
    repetition_period = Column(String)
    valid_days = Column(String)  # Comma-separated list of days
    valid_days_week1 = Column(String)  # For biweekly errands
    valid_days_week2 = Column(String)  # For biweekly errands
    starting_monday = Column(Date)  # For weekly/biweekly errands
    frequency = Column(Integer)  # For monthly errands
    minimum_interval = Column(Integer)  # Minimum days between occurrences
    interval_unit = Column(String)  # 'days', 'weeks', 'months'
    priority = Column(Integer, default=3)  # Default priority level
    flexible_start_window = Column(Boolean, default=False)
    flexible_end_window = Column(Boolean, default=False)
    flexible_duration = Column(Boolean, default=False)
    min_duration = Column(Integer)
    max_duration = Column(Integer)
    complementary_errands = Column(String)  # Comma-separated list of errand IDs that cannot be done on the same day
    same_day_required = Column(Boolean, default=False)  # Whether complementary errands must be done on the same day
    order_required = Column(Boolean, default=False)  # Whether complementary errands must be done in a specific order
    same_location_required = Column(Boolean, default=False)  # Whether complementary errands must be done at the same location
    conflicting_errands = Column(String)  # Comma-separated list of errand IDs that cannot be done on the same day
    conflict_type = Column(String)  # Type of conflict: 'time', 'location', 'access_type'
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Errand(id={self.id}, title='{self.title}', location_type='{self.location_type}')>"

    # Relationships
    user = relationship("User", back_populates="errands")
    calendar_events = relationship("CalendarEvent", back_populates="errand", cascade="all, delete-orphan")

    def validate_complementary_errands(self, db_session, new_complementary_ids):
        """Validate and update complementary errands relationships"""
        try:
            if not new_complementary_ids:
                # Remove this errand from all complementary errands
                if self.complementary_errands:
                    for comp_id in self.complementary_errands.split(','):
                        if comp_id:
                            comp_errand = db_session.query(Errand).filter_by(id=comp_id, user_id=self.user_id).first()
                            if comp_errand:
                                comp_errands = set((comp_errand.complementary_errands or '').split(','))
                                comp_errands.discard(str(self.id))
                                comp_errand.complementary_errands = ','.join(comp_errands) if comp_errands else None
                                db_session.add(comp_errand)
                self.complementary_errands = None
                return True, None
            
            # Convert to set for easier comparison
            new_complementary = set(str(id) for id in new_complementary_ids)
            current_complementary = set((self.complementary_errands or '').split(',')) if self.complementary_errands else set()
            
            # Remove empty strings and self-reference
            new_complementary.discard('')
            new_complementary.discard(str(self.id))
            current_complementary.discard('')
            current_complementary.discard(str(self.id))
            
            # Validate all complementary errands exist
            for comp_id in new_complementary:
                comp_errand = db_session.query(Errand).filter_by(id=comp_id, user_id=self.user_id).first()
                if not comp_errand:
                    return False, f"Complementary errand not found: {comp_id}"
            
            # Update complementary relationships
            self.complementary_errands = ','.join(new_complementary) if new_complementary else None
            
            # Update reciprocal relationships
            for comp_id in new_complementary:
                comp_errand = db_session.query(Errand).filter_by(id=comp_id, user_id=self.user_id).first()
                if comp_errand:
                    comp_errands = set((comp_errand.complementary_errands or '').split(','))
                    comp_errands.add(str(self.id))
                    comp_errands.discard('')
                    comp_errand.complementary_errands = ','.join(comp_errands) if comp_errands else None
                    db_session.add(comp_errand)
            
            return True, None
        except Exception as e:
            return False, f"Error validating complementary errands: {str(e)}"

    def validate_conflicting_errands(self, db_session, new_conflicting_ids):
        """Validate and update conflicting errands relationships"""
        try:
            if not new_conflicting_ids:
                # Remove this errand from all conflicting errands
                if self.conflicting_errands:
                    for conflict_id in self.conflicting_errands.split(','):
                        if conflict_id:
                            conflict_errand = db_session.query(Errand).filter_by(id=conflict_id, user_id=self.user_id).first()
                            if conflict_errand:
                                conflict_errands = set((conflict_errand.conflicting_errands or '').split(','))
                                conflict_errands.discard(str(self.id))
                                conflict_errand.conflicting_errands = ','.join(conflict_errands) if conflict_errands else None
                                conflict_errand.conflict_type = None
                                db_session.add(conflict_errand)
                self.conflicting_errands = None
                self.conflict_type = None
                return True, None
            
            # Convert to set for easier comparison
            new_conflicting = set(str(id) for id in new_conflicting_ids)
            current_conflicting = set((self.conflicting_errands or '').split(',')) if self.conflicting_errands else set()
            
            # Remove empty strings and self-reference
            new_conflicting.discard('')
            new_conflicting.discard(str(self.id))
            current_conflicting.discard('')
            current_conflicting.discard(str(self.id))
            
            # Validate all conflicting errands exist
            for conflict_id in new_conflicting:
                conflict_errand = db_session.query(Errand).filter_by(id=conflict_id, user_id=self.user_id).first()
                if not conflict_errand:
                    return False, f"Conflicting errand not found: {conflict_id}"
            
            # Update conflicting relationships
            self.conflicting_errands = ','.join(new_conflicting) if new_conflicting else None
            
            # Update reciprocal relationships
            for conflict_id in new_conflicting:
                conflict_errand = db_session.query(Errand).filter_by(id=conflict_id, user_id=self.user_id).first()
                if conflict_errand:
                    conflict_errands = set((conflict_errand.conflicting_errands or '').split(','))
                    conflict_errands.add(str(self.id))
                    conflict_errands.discard('')
                    conflict_errand.conflicting_errands = ','.join(conflict_errands) if conflict_errands else None
                    conflict_errand.conflict_type = self.conflict_type
                    db_session.add(conflict_errand)
            
            return True, None
        except Exception as e:
            return False, f"Error validating conflicting errands: {str(e)}" 