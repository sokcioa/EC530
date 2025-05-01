import tkinter as tk
from tkinter import ttk, messagebox
from EP_database import Errand

class ErrandsWindow:
    def __init__(self, parent, session, places_api):
        self.parent = parent
        self.session = session
        self.places_api = places_api
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        self.frame = scrollable_frame
        self.errand_loc_validated = False
        self.last_validated_errand_loc = ""
        
        self.create_widgets()
        self.load_errands()
    
    def create_widgets(self):
        """Create errands management page widgets"""
        # Create form
        ttk.Label(self.frame, text="Manage Errands", font=("Arial", 16)).pack(pady=10)
        
        # Errand title
        ttk.Label(self.frame, text="Title:").pack()
        self.errand_title_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.errand_title_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Description
        ttk.Label(self.frame, text="Description:").pack()
        self.errand_desc_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.errand_desc_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Category
        ttk.Label(self.frame, text="Category:").pack()
        self.errand_category_var = tk.StringVar()
        categories = ["Shopping", "Medical", "Work", "Personal", "Education", "Other"]
        category_menu = ttk.OptionMenu(self.frame, self.errand_category_var, categories[0], *categories)
        category_menu.pack(fill=tk.X, padx=5, pady=2)
        
        # Location
        ttk.Label(self.frame, text="Location:").pack()
        self.errand_loc_var = tk.StringVar()
        
        def on_errand_loc_change(*args):
            if self.errand_loc_var.get() != self.last_validated_errand_loc:
                self.errand_loc_validated = False
        
        self.errand_loc_var.trace_add('write', on_errand_loc_change)
        
        location_entry = ttk.Entry(self.frame, textvariable=self.errand_loc_var)
        location_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Hidden coordinate variables
        self.errand_lat_var = tk.DoubleVar()
        self.errand_lng_var = tk.DoubleVar()
        
        # Validate location button
        ttk.Button(self.frame, text="Validate Location", 
                  command=self.validate_location).pack(pady=2)
        
        # Time window selection
        time_frame = ttk.LabelFrame(self.frame, text="Valid Start Time Window (24-hour format)")
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Start time
        start_frame = ttk.Frame(time_frame)
        start_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(start_frame, text="Earliest Start:").pack()
        self.start_time_var = tk.StringVar()
        self.start_time_var.set("1530")  # Default to 3:30 PM
        start_entry = ttk.Entry(start_frame, textvariable=self.start_time_var, width=6)
        start_entry.pack()
        
        # End time
        end_frame = ttk.Frame(time_frame)
        end_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(end_frame, text="Latest Start:").pack()
        self.end_time_var = tk.StringVar()
        self.end_time_var.set("1800")  # Default to 6:00 PM
        end_entry = ttk.Entry(end_frame, textvariable=self.end_time_var, width=6)
        end_entry.pack()
        
        # Estimated duration
        duration_frame = ttk.LabelFrame(self.frame, text="Estimated Duration")
        duration_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.duration_var = tk.StringVar()
        self.duration_var.set("30")  # Default to 30 minutes
        
        ttk.Label(duration_frame, text="Minutes:").pack(side=tk.LEFT, padx=5)
        duration_spinbox = ttk.Spinbox(duration_frame, from_=15, to=480, increment=15,
                                     textvariable=self.duration_var, width=5)
        duration_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Days of the week selection
        days_frame = ttk.LabelFrame(self.frame, text="Days of the Week")
        days_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.days_vars = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            var = tk.BooleanVar()
            self.days_vars[day] = var
            cb = ttk.Checkbutton(days_frame, text=day, variable=var)
            cb.grid(row=i//4, column=i%4, sticky='w', padx=5, pady=2)
        
        # Frequency and repetition options
        freq_frame = ttk.LabelFrame(self.frame, text="Frequency and Repetition")
        freq_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Frequency
        freq_subframe = ttk.Frame(freq_frame)
        freq_subframe.pack(fill=tk.X, padx=5, pady=2)
        
        self.freq_var = tk.StringVar()
        self.freq_var.set("1")  # Default to once
        
        ttk.Label(freq_subframe, text="Occurrences:").pack(side=tk.LEFT, padx=5)
        freq_spinbox = ttk.Spinbox(freq_subframe, from_=1, to=7, textvariable=self.freq_var, width=3)
        freq_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Repetition period
        self.rep_period_var = tk.StringVar()
        self.rep_period_var.set("week")  # Default to week
        
        rep_periods = ["week", "2 weeks", "month", "year"]
        rep_period_menu = ttk.OptionMenu(freq_subframe, self.rep_period_var, *rep_periods)
        rep_period_menu.pack(side=tk.LEFT, padx=5)
        
        # Minimum interval
        interval_frame = ttk.LabelFrame(self.frame, text="Minimum Time Between Occurrences")
        interval_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.interval_var = tk.StringVar()
        self.interval_var.set("24")  # Default to 24 hours
        
        ttk.Label(interval_frame, text="Minimum:").pack(side=tk.LEFT, padx=5)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=1000, 
                                     textvariable=self.interval_var, width=4)
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        
        self.interval_unit_var = tk.StringVar()
        self.interval_unit_var.set("hours")  # Default to hours
        
        interval_units = ["hours", "days", "weeks", "months"]
        interval_unit_menu = ttk.OptionMenu(interval_frame, self.interval_unit_var, *interval_units)
        interval_unit_menu.pack(side=tk.LEFT, padx=5)
        
        # Priority
        ttk.Label(self.frame, text="Priority (1-5):").pack()
        self.errand_priority_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.errand_priority_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Add", command=self.add_errand).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=self.delete_errand).pack(side=tk.LEFT, padx=5)
        
        # Errands list with scrollbar
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbar
        self.errands_list = ttk.Treeview(list_frame, columns=("title", "category", "description", "location", 
                                                             "time_window", "duration", "days", "frequency", 
                                                             "interval", "priority"), show="headings")
        
        # Add scrollbar to treeview
        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.errands_list.yview)
        self.errands_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.errands_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure columns
        self.errands_list.heading("title", text="Title")
        self.errands_list.heading("category", text="Category")
        self.errands_list.heading("description", text="Description")
        self.errands_list.heading("location", text="Location")
        self.errands_list.heading("time_window", text="Valid Start Time")
        self.errands_list.heading("duration", text="Duration")
        self.errands_list.heading("days", text="Days")
        self.errands_list.heading("frequency", text="Frequency")
        self.errands_list.heading("interval", text="Min Interval")
        self.errands_list.heading("priority", text="Priority")
    
    def validate_location(self):
        """Validate location using Places API"""
        if not self.places_api:
            messagebox.showwarning("Warning", "Places API not available")
            return True
        
        location = self.errand_loc_var.get()
        if not location:
            messagebox.showerror("Error", "Please enter a location")
            return False
        
        try:
            result = self.places_api.validate_address(location)
            if not result:
                messagebox.showerror("Error", "Could not validate location")
                return False
            
            if messagebox.askyesno("Confirm Location", 
                                 f"Did you mean:\n{result['name']}\n{result['address']}?"):
                self.errand_loc_var.set(result['address'])
                self.errand_lat_var.set(result['location'].get('latitude', 0))
                self.errand_lng_var.set(result['location'].get('longitude', 0))
                self.errand_loc_validated = True
                self.last_validated_errand_loc = result['address']
                return True
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to validate location: {e}")
            return False
    
    def validate_time_format(self, time_str):
        """Validate 24-hour time format (HHMM)"""
        if not time_str.isdigit() or len(time_str) != 4:
            return False
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    
    def add_errand(self):
        """Add a new errand"""
        try:
            if self.errand_loc_var.get() and not self.errand_loc_validated:
                if not self.validate_location():
                    return
            
            # Get selected days
            selected_days = [day for day, var in self.days_vars.items() if var.get()]
            if not selected_days:
                messagebox.showerror("Error", "Please select at least one day of the week")
                return
            
            # Validate time window
            start_time = self.start_time_var.get()
            end_time = self.end_time_var.get()
            if not self.validate_time_format(start_time) or not self.validate_time_format(end_time):
                messagebox.showerror("Error", "Invalid time format. Please use 24-hour format (HHMM)")
                return
            
            if int(start_time) >= int(end_time):
                messagebox.showerror("Error", "Start time must be earlier than end time")
                return
            
            priority = int(self.errand_priority_var.get())
            if not 1 <= priority <= 5:
                raise ValueError("Priority must be between 1 and 5")
            
            errand = Errand(
                title=self.errand_title_var.get(),
                description=self.errand_desc_var.get(),
                category=self.errand_category_var.get(),
                location_name=self.errand_loc_var.get(),
                location_latitude=self.errand_lat_var.get(),
                location_longitude=self.errand_lng_var.get(),
                days_of_week=','.join(selected_days),
                frequency_per_week=int(self.freq_var.get()),
                repetition=self.rep_period_var.get(),
                minimum_interval=int(self.interval_var.get()),
                interval_unit=self.interval_unit_var.get(),
                valid_start_window=start_time,
                valid_end_window=end_time,
                estimated_duration=int(self.duration_var.get()),
                priority=priority
            )
            
            self.session.add(errand)
            self.session.commit()
            
            # Clear form
            self.errand_title_var.set("")
            self.errand_desc_var.set("")
            self.errand_loc_var.set("")
            self.errand_priority_var.set("")
            self.errand_category_var.set("Shopping")
            self.start_time_var.set("1530")
            self.end_time_var.set("1800")
            self.duration_var.set("30")
            for var in self.days_vars.values():
                var.set(False)
            self.freq_var.set("1")
            self.rep_period_var.set("week")
            self.interval_var.set("24")
            self.interval_unit_var.set("hours")
            
            # Refresh list
            self.load_errands()
            
            messagebox.showinfo("Success", "Errand added successfully!")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add errand: {e}")
    
    def delete_errand(self):
        """Delete selected errand"""
        try:
            selection = self.errands_list.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an errand to delete")
                return
            
            if messagebox.askyesno("Confirm", "Are you sure you want to delete this errand?"):
                for item in selection:
                    values = self.errands_list.item(item)["values"]
                    errand = self.session.query(Errand).filter_by(title=values[0]).first()
                    if errand:
                        self.session.delete(errand)
                
                self.session.commit()
                self.load_errands()
                messagebox.showinfo("Success", "Errand(s) deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete errand: {e}")
    
    def load_errands(self):
        """Load existing errands"""
        try:
            for item in self.errands_list.get_children():
                self.errands_list.delete(item)
            
            errands = self.session.query(Errand).all()
            for errand in errands:
                time_window = f"{errand.valid_start_window}-{errand.valid_end_window}"
                interval = f"{errand.minimum_interval} {errand.interval_unit}"
                self.errands_list.insert("", "end", values=(
                    errand.title,
                    errand.category,
                    errand.description,
                    errand.location_name,
                    time_window,
                    f"{errand.estimated_duration} min",
                    errand.days_of_week,
                    f"{errand.frequency_per_week} per {errand.repetition}",
                    interval,
                    errand.priority
                ))
        except Exception as e:
            print(f"Error loading errands: {e}")
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the frame"""
        self.frame.pack_forget() 