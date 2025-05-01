import tkinter as tk
from tkinter import ttk, messagebox
from EP_database import User

class PersonalInfoWindow:
    def __init__(self, parent, session, places_api):
        self.parent = parent
        self.session = session
        self.places_api = places_api
        
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
        self.address_validated = False
        self.last_validated_address = ""
        
        self.create_widgets()
        self.load_user_data()
    
    def create_widgets(self):
        """Create personal information page widgets"""
        # Create form
        ttk.Label(self.frame, text="Personal Information", font=("Arial", 16)).pack(pady=10)
        
        # Name
        ttk.Label(self.frame, text="Name:").pack()
        self.name_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.name_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Email
        ttk.Label(self.frame, text="Email:").pack()
        self.email_var = tk.StringVar()
        ttk.Entry(self.frame, textvariable=self.email_var).pack(fill=tk.X, padx=5, pady=2)
        
        # Home Address
        ttk.Label(self.frame, text="Home Address:").pack()
        self.address_var = tk.StringVar()
        
        def on_address_change(*args):
            if self.address_var.get() != self.last_validated_address:
                self.address_validated = False
        
        self.address_var.trace_add('write', on_address_change)
        
        address_entry = ttk.Entry(self.frame, textvariable=self.address_var)
        address_entry.pack(fill=tk.X, padx=5, pady=2)
        
        # Hidden coordinate variables
        self.home_lat_var = tk.DoubleVar()
        self.home_lng_var = tk.DoubleVar()
        
        # Validate address button
        ttk.Button(self.frame, text="Validate Address", 
                  command=self.validate_address).pack(pady=2)
        
        # Save button
        ttk.Button(self.frame, text="Save", command=self.save_personal_info).pack(pady=10)
    
    def validate_address(self):
        """Validate address using Places API"""
        if not self.places_api:
            messagebox.showwarning("Warning", "Places API not available")
            return True
        
        address = self.address_var.get()
        if not address:
            messagebox.showerror("Error", "Please enter an address")
            return False
        
        try:
            result = self.places_api.validate_address(address)
            if not result:
                messagebox.showerror("Error", "Could not validate address")
                return False
            
            if messagebox.askyesno("Confirm Address", 
                                 f"Did you mean:\n{result['name']}\n{result['address']}?"):
                self.address_var.set(result['address'])
                self.home_lat_var.set(result['location'].get('latitude', 0))
                self.home_lng_var.set(result['location'].get('longitude', 0))
                self.address_validated = True
                self.last_validated_address = result['address']
                return True
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Failed to validate address: {e}")
            return False
    
    def load_user_data(self):
        """Load existing user data"""
        try:
            user = self.session.query(User).first()
            if user:
                self.name_var.set(user.name)
                self.email_var.set(user.email)
                self.address_var.set(user.home_address)
        except Exception as e:
            print(f"Error loading user data: {e}")
    
    def save_personal_info(self):
        """Save personal information"""
        try:
            if self.address_var.get() and not self.address_validated:
                if not self.validate_address():
                    return
            
            user = self.session.query(User).first()
            if not user:
                user = User()
            
            user.name = self.name_var.get()
            user.email = self.email_var.get()
            user.home_address = self.address_var.get()
            user.home_latitude = self.home_lat_var.get()
            user.home_longitude = self.home_lng_var.get()
            
            self.session.add(user)
            self.session.commit()
            messagebox.showinfo("Success", "Personal information saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save personal information: {e}")
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def pack_forget(self):
        """Hide the frame"""
        self.frame.pack_forget() 