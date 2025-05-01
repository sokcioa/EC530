from flask import Flask
from api.base import base_bp
from api.places import places_bp
from api.directions import directions_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(base_bp)
    app.register_blueprint(places_bp)
    app.register_blueprint(directions_bp)
    
    return app
