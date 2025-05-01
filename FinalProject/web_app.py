from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from models import Session, init_db, get_session, cleanup_session
from models import User, Errand, CalendarEvent
from api.places import places_bp, PlacesAPI
from api.directions import directions_bp
from api.google_auth import google_auth_bp, GoogleAuth
from services import UserService, ErrandService
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ErrandPlanner')
logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Add file handler
file_handler = RotatingFileHandler('logs/errand_planner.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(file_handler)

# Initialize database
logger.info("Initializing database...")
init_db()
logger.info("Database initialized successfully")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Register blueprints
app.register_blueprint(places_bp)
app.register_blueprint(directions_bp)
app.register_blueprint(google_auth_bp)

# Initialize services with fresh database session
db_session = Session()
places_api = PlacesAPI()
google_auth = GoogleAuth()
user_service = UserService(db_session, places_api)
errand_service = ErrandService(db_session, places_api)

def get_current_user():
    """Get the current user from the session"""
    if 'user_id' not in session:
        logger.debug("No user_id in session")
        return None
    
    try:
        # Always get fresh data from the database
        user = user_service.get_user(session['user_id'])
        if not user:
            logger.warning(f"User not found in database for session user_id: {session['user_id']}")
            session.clear()  # Clear session if user not found
            return None
        logger.debug(f"Retrieved user from database - ID: {user.id}, Name: {user.name}, Address: {user.home_address}")
        return user
    except Exception as e:
        logger.error(f"Error retrieving user: {str(e)}")
        return None

@app.route('/')
def index():
    """Root route that redirects based on user state"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    elif not user.home_address:
        return redirect(url_for('personal_info'))
    return redirect(url_for('errands'))

@app.route('/login')
def login():
    """Initiate Google OAuth2 flow"""
    auth_url = google_auth.get_auth_url()
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Handle OAuth2 callback"""
    if 'state' not in session or session['state'] != request.args.get('state'):
        logger.warning("Invalid state parameter in OAuth callback")
        flash('Invalid state parameter', 'error')
        return redirect(url_for('personal_info'))
    
    try:
        logger.debug("Starting OAuth callback process")
        credentials = google_auth.get_credentials(request.url)
        user_info = google_auth.get_user_info(credentials)
        logger.debug(f"Retrieved user info from Google: {user_info.get('email')}")
        
        # Store user info in session
        session['google_user_info'] = user_info
        session['google_credentials'] = credentials.to_json()
        
        # Check if user exists in database
        try:
            logger.debug(f"Checking for existing user with email: {user_info['email']}")
            user = user_service.get_user_by_email(user_info['email'])
            if not user:
                logger.info(f"Creating new user for email: {user_info['email']}")
                user = user_service.create_user(
                    name=user_info.get('name', ''),
                    email=user_info['email'],
                    home_address='',
                    home_latitude=0,
                    home_longitude=0
                )
                logger.info(f"Successfully created new user with ID: {user.id}")
            else:
                logger.debug(f"Found existing user with ID: {user.id}")
            
            # Store user ID in session
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            logger.debug(f"Stored user ID {user.id} in session")
            
            # If user has home address, redirect to errands, otherwise to personal info
            if user.home_address:
                logger.debug(f"User {user.id} has home address, redirecting to errands")
                return redirect(url_for('errands'))
            else:
                logger.debug(f"User {user.id} has no home address, redirecting to personal info")
                return redirect(url_for('personal_info'))
        except Exception as e:
            logger.error(f"Error during user creation/retrieval: {str(e)}", exc_info=True)
            flash('Error during authentication', 'error')
            return redirect(url_for('personal_info'))
            
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}", exc_info=True)
        flash(f'Error during authentication: {str(e)}', 'error')
        return redirect(url_for('personal_info'))

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    google_auth.clear_credentials()
    session.clear()
    return redirect(url_for('personal_info'))

def get_address_display(address, user=None):
    """Get the display value for an address, with optional validation"""
    if not address:
        return ''
    
    try:
        # If user is provided and has a home address, use it for location bias
        location = None
        if user and user.home_address:
            home_validation = places_api.validate_address(user.home_address)
            if home_validation and 'location' in home_validation:
                location = (
                    home_validation['location']['latitude'],
                    home_validation['location']['longitude']
                )
        
        # Try to validate the address
        validation_result = places_api.validate_address(address, location=location)
        if validation_result:
            return validation_result['address']
        return address  # Return original address if validation fails
    except Exception as e:
        logger.error(f"Error getting address display: {str(e)}")
        return address  # Return original address if there's an error

def handle_db_error(e):
    """Handle database-related errors and redirect appropriately"""
    logger.error(f"Database error: {str(e)}")
    if isinstance(e, UnboundLocalError) and 'db_session' in str(e):
        logger.warning("Database session not initialized, redirecting to login")
        return redirect(url_for('login'))
    return render_template('error.html', error="An error occurred. Please try again.")

@app.route('/personal_info', methods=['GET', 'POST'])
def personal_info():
    try:
        user = get_current_user()
        if not user:
            logger.warning("No user found, redirecting to login")
            return redirect(url_for('login'))
        
        logger.debug(f"Personal info page accessed - User ID: {user.id}, Name: {user.name}, Address: {user.home_address}")
        
        if request.method == 'POST':
            name = request.form.get('name')
            home_address = request.form.get('home_address')
            
            logger.debug(f"Form submitted - Name: {name}, Address: {home_address}")
            
            if not name or not home_address:
                logger.warning("Missing required fields in form submission")
                return render_template('personal_info.html', 
                                    error="Please fill in all required fields",
                                    name=name,
                                    home_address=home_address)
            
            try:
                # Validate address
                validation_result = user_service.validate_address(home_address)
                if not validation_result["valid"]:
                    return render_template('personal_info.html', 
                                        error=validation_result["message"],
                                        name=name,
                                        home_address=home_address)
                
                # Update user information with validated address
                updated_user = user_service.update_user(
                    user_id=user.id,
                    name=name,
                    home_address=validation_result["address"],
                    home_latitude=validation_result["lat"],
                    home_longitude=validation_result["lng"]
                )
                
                if not updated_user:
                    raise Exception("Failed to update user information")
                
                # Update session with validated address
                session['user_address'] = updated_user.home_address
                
                flash("Personal information updated successfully!", "success")
                return redirect(url_for('errands'))
                
            except Exception as e:
                logger.error(f"Error updating personal information: {str(e)}")
                return render_template('personal_info.html', 
                                    error="An error occurred while updating your information. Please try again.",
                                    name=name,
                                    home_address=home_address)
        
        return render_template('personal_info.html', 
                             name=user.name,
                             home_address=user.home_address)
        
    except Exception as e:
        logger.error(f"Error in personal_info route: {str(e)}")
        return handle_db_error(e)

def validate_address_with_bias(address, user=None):
    """Validate an address with optional location bias from user's home address"""
    try:
        if not address:
            return {'valid': False, 'error': 'Address is required'}
        
        if len(address) < 2:  # Reduced minimum length to support short names
            return {'valid': False, 'error': 'Please enter a more complete address or location name'}
        
        # If user is provided and has a home address, use it for location bias
        location = None
        if user and user.home_address:
            home_validation = places_api.validate_address(user.home_address)
            if home_validation and 'location' in home_validation:
                location = (
                    home_validation['location']['latitude'],
                    home_validation['location']['longitude']
                )
        
        # First try to validate as a place name
        try:
            place_result = places_api.search_place(address, location=location)
            if place_result:
                return {
                    'valid': True,
                    'address': place_result['formatted_address'],
                    'location': place_result['location']
                }
        except Exception as e:
            logger.debug(f"Error searching place: {str(e)}")
        
        # If place search fails, try direct address validation
        validation_result = places_api.validate_address(address, location=location)
        if validation_result:
            return {
                'valid': True,
                'address': validation_result['formatted_address'],
                'location': validation_result['location']
            }
        
        return {'valid': False, 'error': 'Invalid address or location'}
    except Exception as e:
        logger.error(f"Error validating address: {str(e)}")
        return {'valid': False, 'error': 'Error validating address'}

@app.route('/validate_address', methods=['POST'])
def validate_address():
    db_session = None
    try:
        address = request.form.get('address')
        user = get_current_user()
        if not user:
            logger.warning("Validate address attempted with no user")
            return jsonify({'valid': False, 'error': 'User not found'})
        
        db_session = Session()
        return jsonify(validate_address_with_bias(address, user))
            
    except UnboundLocalError as e:
        if 'db_session' in str(e):
            return handle_db_error(e)
        raise
    except Exception as e:
        logger.error(f"Error in validate_address route: {str(e)}")
        if db_session:
            db_session.rollback()
        return jsonify({'valid': False, 'error': str(e)})
    finally:
        if db_session:
            db_session.close()

def serialize_errand(errand):
    """Serialize an errand object to JSON"""
    if not errand:
        return None
    
    return {
        'id': errand.id,
        'title': errand.title,
        'location_type': errand.location_type,
        'location_name': errand.location_name,
        'location_address': errand.location_address,
        'category': errand.category,
        'latitude': errand.latitude,
        'longitude': errand.longitude,
        'valid_start_window': errand.valid_start_window,
        'valid_end_window': errand.valid_end_window,
        'estimated_duration': errand.estimated_duration,
        'valid_days': errand.valid_days,
        'valid_days_week1': errand.valid_days_week1,
        'valid_days_week2': errand.valid_days_week2,
        'frequency': errand.frequency,
        'repetition_period': errand.repetition_period,
        'minimum_interval': errand.minimum_interval,
        'interval_unit': errand.interval_unit,
        'priority': errand.priority,
        'is_remote': errand.is_remote,
        'use_exact_location': errand.use_exact_location,
        'access_type': errand.access_type,
        'repetition': errand.repetition,
        'flexible_start_window': errand.flexible_start_window,
        'flexible_end_window': errand.flexible_end_window,
        'flexible_duration': errand.flexible_duration,
        'min_duration': errand.min_duration,
        'max_duration': errand.max_duration,
        'complementary_errands': errand.complementary_errands,
        'same_day_required': errand.same_day_required,
        'order_required': errand.order_required,
        'same_location_required': errand.same_location_required,
        'conflicting_errands': errand.conflicting_errands,
        'conflict_type': errand.conflict_type,
        'created_at': errand.created_at.isoformat() if errand.created_at else None,
        'updated_at': errand.updated_at.isoformat() if errand.updated_at else None
    }

@app.route('/errands', methods=['GET', 'POST'])
@app.route('/errands/<int:errand_id>', methods=['GET', 'PUT', 'DELETE'])
def errands(errand_id=None):
    """Handle errands operations"""
    db_session = None
    try:
        # Get current user
        user = get_current_user()
        if not user:
            logger.warning("No user found in session")
            return redirect(url_for('login'))
        
        # Initialize database session
        db_session = Session()
        
        # Handle GET request
        if request.method == 'GET':
            if errand_id:
                # Get specific errand for editing
                errand = errand_service.get_errand_by_id(errand_id)
                if not errand or errand.user_id != user.id:
                    logger.warning(f"Errand {errand_id} not found or not owned by user {user.id}")
                    return jsonify({'error': 'Errand not found'}), 404
                logger.info(f"Retrieved errand {errand_id} for editing")
                return render_template('errands.html', errand=errand, errands=errand_service.get_user_errands(user.id))
            else:
                # Get all errands
                errands = errand_service.get_user_errands(user.id)
                logger.info(f"Retrieved {len(errands)} errands for user {user.id}")
                return render_template('errands.html', errands=errands)
        
        # Handle POST request (create new errand)
        if request.method == 'POST':
            try:
                data = request.form.to_dict()
                logger.info(f"Creating new errand with data: {data}")
                
                # Validate required fields
                required_fields = ['title', 'location_type', 'access_type', 'valid_start_window', 
                                 'valid_end_window', 'estimated_duration']
                
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                    logger.warning(error_msg)
                    return jsonify({'error': error_msg}), 400
                
                # Process boolean fields
                boolean_fields = ['is_remote', 'use_exact_location', 'flexible_start_window', 
                                'flexible_end_window', 'flexible_duration', 'same_day_required',
                                'order_required', 'same_location_required']
                for field in boolean_fields:
                    if field in data:
                        data[field] = data[field].lower() == 'true'
                
                # Process complementary errands
                complementary_errands = []
                if 'complementary_errands[]' in request.form:
                    complementary_errands = request.form.getlist('complementary_errands[]')
                    # Filter out empty strings and convert to integers
                    complementary_errands = [int(x) for x in complementary_errands if x]
                
                # Process conflicting errands
                conflicting_errands = []
                if 'conflicting_errands[]' in request.form:
                    conflicting_errands = request.form.getlist('conflicting_errands[]')
                    # Filter out empty strings and convert to integers
                    conflicting_errands = [int(x) for x in conflicting_errands if x]
                
                # Validate remote errands
                if data.get('is_remote') and data.get('location_type') != 'name':
                    return jsonify({'error': 'Remote errands must use location type "name"'}), 400
                
                # Create errand
                errand = errand_service.create_errand(
                    user_id=user.id,
                    title=data['title'],
                    location_type=data['location_type'],
                    access_type=data['access_type'],
                    valid_start_window=data['valid_start_window'],
                    valid_end_window=data['valid_end_window'],
                    estimated_duration=int(data['estimated_duration']),
                    repetition=data.get('repetition'),
                    location_name=data.get('location_name'),
                    category=data.get('category'),
                    location_address=data.get('location_address'),
                    complementary_errands=complementary_errands,
                    conflicting_errands=conflicting_errands,
                    conflict_type=data.get('conflict_type'),
                    valid_days=','.join(data.getlist('valid_days')) if data.get('valid_days') else None,
                    valid_days_week1=','.join(data.getlist('valid_days_week1')) if data.get('valid_days_week1') else None,
                    valid_days_week2=','.join(data.getlist('valid_days_week2')) if data.get('valid_days_week2') else None,
                    starting_monday=data.get('starting_monday'),
                    frequency=int(data.get('frequency', 1)),
                    minimum_interval=int(data.get('minimum_interval', 24)),
                    interval_unit=data.get('interval_unit', 'hours'),
                    priority=int(data.get('priority', 3)),
                    is_remote=data.get('is_remote', False),
                    use_exact_location=data.get('use_exact_location', True),
                    flexible_start_window=data.get('flexible_start_window', False),
                    flexible_end_window=data.get('flexible_end_window', False),
                    flexible_duration=data.get('flexible_duration', False),
                    min_duration=int(data.get('min_duration', 0)) if data.get('min_duration') else None,
                    max_duration=int(data.get('max_duration', 0)) if data.get('max_duration') else None,
                    same_day_required=data.get('same_day_required', False),
                    order_required=data.get('order_required', False),
                    same_location_required=data.get('same_location_required', False)
                )
                
                if not errand:
                    raise Exception("Failed to create errand")
                    
                logger.info(f"Created new errand with ID: {errand.id}")
                return jsonify({'message': 'Errand created successfully'})
                
            except ValueError as e:
                logger.warning(f"Validation error creating errand: {str(e)}")
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Error creating errand: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Handle PUT request (update errand)
        if request.method == 'PUT':
            if not errand_id:
                return jsonify({'error': 'Errand ID required for update'}), 400
            
            try:
                data = request.form.to_dict()
                logger.info(f"Updating errand {errand_id} with data: {data}")
                
                # Process boolean fields
                boolean_fields = ['is_remote', 'use_exact_location', 'flexible_start_window', 
                                'flexible_end_window', 'flexible_duration', 'same_day_required',
                                'order_required', 'same_location_required']
                for field in boolean_fields:
                    if field in data:
                        data[field] = data[field].lower() == 'true'
                
                # Process complementary errands
                complementary_errands = []
                if 'complementary_errands[]' in request.form:
                    complementary_errands = request.form.getlist('complementary_errands[]')
                    # Filter out empty strings and convert to integers
                    complementary_errands = [int(x) for x in complementary_errands if x]
                
                # Process conflicting errands
                conflicting_errands = []
                if 'conflicting_errands[]' in request.form:
                    conflicting_errands = request.form.getlist('conflicting_errands[]')
                    # Filter out empty strings and convert to integers
                    conflicting_errands = [int(x) for x in conflicting_errands if x]
                
                # Validate remote errands
                if data.get('is_remote') and data.get('location_type') != 'name':
                    return jsonify({'error': 'Remote errands must use location type "name"'}), 400
                
                # Update errand
                errand = errand_service.update_errand(
                    errand_id=errand_id,
                    complementary_errands=complementary_errands,
                    conflicting_errands=conflicting_errands,
                    conflict_type=data.get('conflict_type'),
                    **{k: v for k, v in data.items() if k not in ['complementary_errands[]', 'conflicting_errands[]', 'errand_id', 'id']}
                )
                
                if not errand:
                    raise Exception("Failed to update errand")
                    
                logger.info(f"Updated errand {errand_id}")
                return jsonify({'message': 'Errand updated successfully'})
                
            except ValueError as e:
                logger.warning(f"Validation error updating errand: {str(e)}")
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"Error updating errand: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # Handle DELETE request
        if request.method == 'DELETE':
            if not errand_id:
                return jsonify({'error': 'Errand ID required for deletion'}), 400
            
            try:
                success = errand_service.delete_errand(errand_id)
                if not success:
                    raise Exception("Failed to delete errand")
                    
                logger.info(f"Deleted errand {errand_id}")
                return jsonify({'message': 'Errand deleted successfully'})
                
            except Exception as e:
                logger.error(f"Error deleting errand: {str(e)}")
                return jsonify({'error': str(e)}), 500
                
    except Exception as e:
        logger.error(f"Unexpected error in errands route: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if db_session:
            db_session.close()

@app.route('/calendar')
def calendar():
    db_session = None
    try:
        user = get_current_user()
        if not user:
            logger.warning("No user found, redirecting to personal_info")
            return redirect(url_for('personal_info'))
        
        db_session = Session()
        logger.debug("Accessing calendar route")
        logger.debug(f"Rendering calendar template for user: {user.id}")
        return render_template('calendar.html', user=user)
            
    except UnboundLocalError as e:
        if 'db_session' in str(e):
            return handle_db_error(e)
        raise
    except Exception as e:
        logger.error(f"Error in calendar route: {str(e)}")
        if db_session:
            db_session.rollback()
        return render_template('error.html', error="An error occurred. Please try again.")
    finally:
        if db_session:
            db_session.close()

@app.route('/delete_errand/<int:errand_id>', methods=['DELETE'])
def delete_errand(errand_id):
    """Delete an errand and its relationships"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get the errand
        errand = errand_service.get_errand_by_id(errand_id)
        if not errand:
            return jsonify({'error': 'Errand not found'}), 404
        
        # Verify ownership
        if errand.user_id != user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete the errand
        success = errand_service.delete_errand(errand_id)
        if not success:
            return jsonify({'error': 'Failed to delete errand'}), 500
        
        return jsonify({'message': 'Errand deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting errand: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/errands', methods=['POST'])
def create_errand():
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401

        # Get form data
        title = request.form.get('title')
        location_type = request.form.get('location_type')
        location_name = request.form.get('location_name')
        location_address = request.form.get('address')
        is_remote = request.form.get('is_remote') == 'true'
        use_exact_location = request.form.get('use_exact_location') == 'true'
        access_type = request.form.get('access_type')
        valid_start_window = request.form.get('valid_start_window')
        valid_end_window = request.form.get('valid_end_window')
        estimated_duration = request.form.get('estimated_duration')
        repetition = request.form.get('repetition')
        valid_days = request.form.getlist('valid_days')
        valid_days_week1 = request.form.getlist('valid_days_week1')
        valid_days_week2 = request.form.getlist('valid_days_week2')
        starting_monday = request.form.get('starting_monday')
        frequency = request.form.get('frequency')
        minimum_interval = request.form.get('minimum_interval')
        interval_unit = request.form.get('interval_unit')
        priority = request.form.get('priority', 3)
        flexible_start_window = request.form.get('flexible_start_window') == 'true'
        flexible_end_window = request.form.get('flexible_end_window') == 'true'
        flexible_duration = request.form.get('flexible_duration') == 'true'
        min_duration = request.form.get('min_duration')
        max_duration = request.form.get('max_duration')
        
        # Handle complementary errands properly
        complementary_errands = request.form.getlist('complementary_errands[]')
        if not complementary_errands:
            complementary_errands = request.form.get('complementary_errands[]')
            if complementary_errands:
                complementary_errands = [complementary_errands]
        
        logger.debug(f"Raw complementary errands: {request.form.getlist('complementary_errands[]')}")
        logger.debug(f"Processed complementary errands: {complementary_errands}")
        
        same_day_required = request.form.get('same_day_required') == 'true'
        order_required = request.form.get('order_required') == 'true'
        same_location_required = request.form.get('same_location_required') == 'true'
        logger.debug(f"Complementary settings - same_day: {same_day_required}, order: {order_required}, same_location: {same_location_required}")
        
        # Handle conflicting errands properly
        conflicting_errands = request.form.getlist('conflicting_errands[]')
        if not conflicting_errands:
            conflicting_errands = request.form.get('conflicting_errands[]')
            if conflicting_errands:
                conflicting_errands = [conflicting_errands]
        conflict_type = request.form.get('conflict_type')

        # Validate required fields
        required_fields = ['title', 'location_type', 'access_type', 'valid_start_window', 
                         'valid_end_window', 'estimated_duration', 'repetition']
        missing_fields = [field for field in required_fields if not request.form.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate access type
        valid_access_types = ['drive', 'walk', 'bike', 'transit']
        if access_type not in valid_access_types:
            return jsonify({'error': f'Invalid access type. Must be one of: {", ".join(valid_access_types)}'}), 400

        # Validate time format
        try:
            int(valid_start_window)
            int(valid_end_window)
        except ValueError:
            return jsonify({'error': 'Invalid time format. Use HHMM format'}), 400

        # Validate remote errands
        logger.debug(f"Validating remote errand - is_remote: {is_remote}, location_type: {location_type}, same_location_required: {same_location_required}")
        if is_remote and location_type != 'name':
            logger.warning(f"Remote errands must use location type 'name' - is_remote: {is_remote}, location_type: {location_type}")
            return jsonify({'error': 'Remote errands must use location type "name"'}), 400

        # Check for existing errand with same title
        existing_errand = session.query(Errand).filter_by(user_id=user.id, title=title).first()
        if existing_errand:
            # If alternative locations are provided, update the existing errand
            alternative_locations = request.form.get('alternative_locations')
            if alternative_locations:
                try:
                    new_locations = json.loads(alternative_locations)
                    existing_locations = json.loads(existing_errand.alternative_locations) if existing_errand.alternative_locations else []
                    combined_locations = existing_locations + [loc for loc in new_locations if loc not in existing_locations]
                    existing_errand.alternative_locations = json.dumps(combined_locations)
                    session.commit()
                    return jsonify({'message': 'Errand updated with additional alternative locations'}), 200
                except json.JSONDecodeError:
                    return jsonify({'error': 'Invalid alternative locations format'}), 400
            return jsonify({'error': 'An errand with this title already exists'}), 400

        # Create new errand
        errand = Errand(
            user_id=user.id,
            title=title,
            location_type=location_type,
            location_name=location_name,
            location_address=location_address,
            is_remote=is_remote,
            use_exact_location=use_exact_location,
            access_type=access_type,
            valid_start_window=valid_start_window,
            valid_end_window=valid_end_window,
            estimated_duration=int(estimated_duration),
            repetition=repetition,
            valid_days=','.join(valid_days) if valid_days else None,
            valid_days_week1=','.join(valid_days_week1) if valid_days_week1 else None,
            valid_days_week2=','.join(valid_days_week2) if valid_days_week2 else None,
            starting_monday=datetime.strptime(starting_monday, '%Y-%m-%d').date() if starting_monday else None,
            frequency=int(frequency) if frequency else None,
            minimum_interval=int(minimum_interval) if minimum_interval else None,
            interval_unit=interval_unit,
            priority=int(priority),
            flexible_start_window=flexible_start_window,
            flexible_end_window=flexible_end_window,
            flexible_duration=flexible_duration,
            min_duration=int(min_duration) if min_duration else None,
            max_duration=int(max_duration) if max_duration else None,
            complementary_errands=','.join(complementary_errands) if complementary_errands else None,
            same_day_required=same_day_required,
            order_required=order_required,
            same_location_required=same_location_required,
            conflicting_errands=','.join(conflicting_errands) if conflicting_errands else None,
            conflict_type=conflict_type
        )

        session.add(errand)
        session.commit()

        return jsonify({'message': 'Errand created successfully'}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Error creating errand: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Generate SSL context
    context = ('cert.pem', 'key.pem')  # certificate and key files
    logger.info("Starting Errand Planner application")
    app.run(host='127.0.0.1', port=5001, ssl_context=context, debug=True)  # Changed to localhost IPv4 