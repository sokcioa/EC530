from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class CalendarEvent(Base):
    """Model for calendar events"""
    __tablename__ = 'calendar_events'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    errand_id = Column(Integer, ForeignKey('errands.id', ondelete='SET NULL'))
    title = Column(String, nullable=False)
    description = Column(String)
    google_calendar_event_id = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    date = Column(DateTime)
    location = Column(String)
    is_all_day = Column(Boolean, default=False)
    recurrence_rule = Column(String)
    status = Column(String, default='scheduled')  # scheduled, completed, cancelled
    notes = Column(String)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    user = relationship("User", back_populates="calendar_events")
    errand = relationship("Errand", back_populates="calendar_events")

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start_time='{self.start_time}')>" 