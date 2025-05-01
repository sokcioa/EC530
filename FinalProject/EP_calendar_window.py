import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from EP_database import CalendarEvent

class CalendarWindow:
    def __init__(self, parent, session):
        self.parent = parent
        self.session = session
        
        # Create main frame with scrollbar
        self.main_frame = ttk.Frame(parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.frame = self.scrollable_frame
        self.current_date = datetime.now()
        self.current_view = "month"  # Default view
        
        self.create_widgets()
        self.load_calendar_events()
    
    def create_widgets(self):
        """Create calendar view page widgets"""
        # View selection
        view_frame = ttk.Frame(self.frame)
        view_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(view_frame, text="Day", command=lambda: self.set_view("day")).pack(side=tk.LEFT, padx=5)
        ttk.Button(view_frame, text="Week", command=lambda: self.set_view("week")).pack(side=tk.LEFT, padx=5)
        ttk.Button(view_frame, text="Month", command=lambda: self.set_view("month")).pack(side=tk.LEFT, padx=5)
        
        # Navigation
        nav_frame = ttk.Frame(self.frame)
        nav_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(nav_frame, text="<", command=self.previous_period).pack(side=tk.LEFT, padx=5)
        self.date_label = ttk.Label(nav_frame, text="")
        self.date_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text=">", command=self.next_period).pack(side=tk.LEFT, padx=5)
        
        # Calendar display
        self.calendar_frame = ttk.Frame(self.frame)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)
        
        self.update_calendar_display()
    
    def set_view(self, view):
        """Set the calendar view (day, week, or month)"""
        self.current_view = view
        self.update_calendar_display()
    
    def previous_period(self):
        """Move to previous period based on current view"""
        if self.current_view == "day":
            self.current_date -= timedelta(days=1)
        elif self.current_view == "week":
            self.current_date -= timedelta(weeks=1)
        else:  # month
            self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.update_calendar_display()
    
    def next_period(self):
        """Move to next period based on current view"""
        if self.current_view == "day":
            self.current_date += timedelta(days=1)
        elif self.current_view == "week":
            self.current_date += timedelta(weeks=1)
        else:  # month
            self.current_date = (self.current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        self.update_calendar_display()
    
    def update_calendar_display(self):
        """Update the calendar display based on current view"""
        # Clear existing widgets
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Update date label
        if self.current_view == "day":
            self.date_label.config(text=self.current_date.strftime("%B %d, %Y"))
            self.show_day_view()
        elif self.current_view == "week":
            start_date = self.current_date - timedelta(days=self.current_date.weekday())
            end_date = start_date + timedelta(days=6)
            self.date_label.config(text=f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}")
            self.show_week_view()
        else:  # month
            self.date_label.config(text=self.current_date.strftime("%B %Y"))
            self.show_month_view()
    
    def show_day_view(self):
        """Display day view"""
        # Create time slots
        for hour in range(24):
            time_frame = ttk.Frame(self.calendar_frame)
            time_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(time_frame, text=f"{hour:02d}:00", width=5).pack(side=tk.LEFT)
            ttk.Frame(time_frame, height=50, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def show_week_view(self):
        """Display week view"""
        # Create header with days
        header_frame = ttk.Frame(self.calendar_frame)
        header_frame.pack(fill=tk.X)
        
        start_date = self.current_date - timedelta(days=self.current_date.weekday())
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            ttk.Label(header_frame, text=day_date.strftime("%a\n%d"), width=10).pack(side=tk.LEFT)
        
        # Create time slots
        for hour in range(24):
            time_frame = ttk.Frame(self.calendar_frame)
            time_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(time_frame, text=f"{hour:02d}:00", width=5).pack(side=tk.LEFT)
            for i in range(7):
                ttk.Frame(time_frame, height=50, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def show_month_view(self):
        """Display month view"""
        # Get first day of month and number of days
        first_day = self.current_date.replace(day=1)
        days_in_month = (first_day.replace(month=first_day.month % 12 + 1, day=1) - timedelta(days=1)).day
        
        # Create header with days
        header_frame = ttk.Frame(self.calendar_frame)
        header_frame.pack(fill=tk.X)
        
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            ttk.Label(header_frame, text=day, width=10).pack(side=tk.LEFT)
        
        # Create calendar grid
        grid_frame = ttk.Frame(self.calendar_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add empty cells for days before first day
        first_weekday = first_day.weekday()
        for _ in range(first_weekday):
            ttk.Frame(grid_frame, height=50, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add day cells
        for day in range(1, days_in_month + 1):
            cell = ttk.Frame(grid_frame, height=50, relief=tk.SUNKEN)
            cell.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
            ttk.Label(cell, text=str(day)).pack()
    
    def load_calendar_events(self):
        """Load calendar events"""
        try:
            events = self.session.query(CalendarEvent).all()
            for event in events:
                # TODO: Display events in appropriate calendar cells
                pass
        except Exception as e:
            print(f"Error loading calendar events: {e}")
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.main_frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the frame"""
        self.main_frame.pack_forget() 