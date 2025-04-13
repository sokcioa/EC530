import socket
import threading
import json
from typing import Dict, List, Optional
import logging
import time
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectoryServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.users: Dict[str, dict] = {}  # username -> user_info
        self.ip_to_username: Dict[str, str] = {}  # ip:port -> username
        self.lock = threading.Lock()  # For thread-safe operations
        self.running = True  # Flag to control server loop
        
        # Create log directory if it doesn't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(script_dir, "directory_logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Initialize log file
        self.log_file = os.path.join(self.log_dir, f"directory_server_{time.strftime('%Y%m%d_%H%M%S')}.log")
        with open(self.log_file, 'w') as f:
            f.write(f"Directory Server Log - Started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
        # Registry file path
        self.registry_file = os.path.join(script_dir, "directory_registry.json")
        
        # Load existing registry if available
        self._load_registry()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self._log_event("SHUTDOWN", f"Received signal {signum}, initiating graceful shutdown")
        self.running = False
        # Close the server socket to stop accepting new connections
        try:
            self.server_socket.close()
        except:
            pass
        sys.exit(0)

    def _load_registry(self):
        """Load the registry from JSON file"""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    registry = json.load(f)
                    self.users = registry.get('users', {})
                    self.ip_to_username = registry.get('ip_to_username', {})
                logger.info(f"Loaded registry with {len(self.users)} users")
                self._log_event("REGISTRY_LOADED", f"Loaded registry with {len(self.users)} users")
            else:
                logger.info("No existing registry found, starting with empty registry")
                self._log_event("REGISTRY_EMPTY", "No existing registry found, starting with empty registry")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self._log_event("REGISTRY_LOAD_ERROR", f"Error loading registry: {e}")

    def _save_registry(self):
        """Save the registry to JSON file"""
        try:
            with open(self.registry_file, 'w') as f:
                json.dump({
                    'users': self.users,
                    'ip_to_username': self.ip_to_username
                }, f, indent=2)
            logger.info(f"Saved registry with {len(self.users)} users")
            self._log_event("REGISTRY_SAVED", f"Saved registry with {len(self.users)} users")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
            self._log_event("REGISTRY_SAVE_ERROR", f"Error saving registry: {e}")

    def start(self):
        """Start the directory server"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            logger.info(f"Directory server started on {self.host}:{self.port}")
            self._log_event("SERVER_START", f"Directory server started on {self.host}:{self.port}")

            while self.running:
                try:
                    # Set a timeout on accept so we can check self.running periodically
                    self.server_socket.settimeout(1.0)
                    client_socket, address = self.server_socket.accept()
                    logger.info(f"New connection from {address}")
                    self._log_event("NEW_CONNECTION", f"New connection from {address}")
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True  # Thread will exit when main thread exits
                    client_thread.start()
                except socket.timeout:
                    # Timeout occurred, check if we should continue running
                    continue
                except Exception as e:
                    if self.running:  # Only log errors if we're still supposed to be running
                        logger.error(f"Error accepting connection: {e}")
                        self._log_event("ACCEPT_ERROR", f"Error accepting connection: {e}")
        except Exception as e:
            logger.error(f"Server error: {e}")
            self._log_event("SERVER_ERROR", f"Server error: {e}")
        finally:
            self.server_socket.close()
            logger.info("Directory server shut down")
            self._log_event("SERVER_SHUTDOWN", "Directory server shut down")

    def _log_event(self, event_type, message):
        """Log an event to the log file"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}: {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
            
        logger.info(f"{event_type}: {message}")

    def _log_current_users(self):
        """Log detailed information about current users"""
        if not self.users:
            self._log_event("CURRENT_USERS", "No users currently registered")
            return
            
        user_details = []
        for username, user_info in self.users.items():
            user_details.append(f"{username} ({user_info['ip']}:{user_info['port']})")
            
        self._log_event("CURRENT_USERS", f"Current users ({len(self.users)}): {', '.join(user_details)}")

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle individual client connections"""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                request = json.loads(data)
                self._log_event("REQUEST_RECEIVED", f"From {address}: {request.get('action', 'unknown')}")
                response = self.process_request(request, address)
                client_socket.send(json.dumps(response).encode('utf-8'))
                self._log_event("RESPONSE_SENT", f"To {address}: {response.get('status', 'unknown')}")
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
            self._log_event("CLIENT_ERROR", f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Connection closed for {address}")
            self._log_event("CONNECTION_CLOSED", f"Connection closed for {address}")

    def process_request(self, request: dict, address: tuple) -> dict:
        """Process incoming requests"""
        action = request.get('action')
        if action == 'register':
            return self.register_user(request)
        elif action == 'query':
            return self.query_users(request, address)
        else:
            return {'status': 'error', 'message': 'Invalid action'}

    def register_user(self, request: dict) -> dict:
        """Register a new user or update existing user"""
        try:
            username = request.get('username')
            ip = request.get('ip')
            port = request.get('port')
            profile = request.get('profile', {})

            if not all([username, ip, port]):
                return {
                    'status': 'error',
                    'message': 'Missing required fields'
                }

            with self.lock:
                # Check if username is already taken by a different IP:port
                if username in self.users:
                    existing_user = self.users[username]
                    if f"{existing_user['ip']}:{existing_user['port']}" != f"{ip}:{port}":
                        # Username conflict - return error with specific code
                        logger.info(f"Username {username} already taken")
                        self._log_event("USERNAME_CONFLICT", f"Username {username} already taken")
                        
                        return {
                            'status': 'error',
                            'error_code': 'username_taken',
                            'message': f'Username {username} is already taken. Please choose a different username.'
                        }
                
                # Remove old IP mapping if user exists
                if username in self.users:
                    old_ip_port = f"{self.users[username]['ip']}:{self.users[username]['port']}"
                    if old_ip_port in self.ip_to_username:
                        del self.ip_to_username[old_ip_port]

                # Add new user info
                self.users[username] = {
                    'username': username,  # Include username in the user object
                    'ip': ip,
                    'port': port,
                    'profile': profile,
                    'last_seen': time.strftime("%Y-%m-%d %H:%M:%S")
                }
                # Add IP mapping
                self.ip_to_username[f"{ip}:{port}"] = username
                
                # Save registry after update
                self._save_registry()

            # Log user registration
            self._log_event("USER_REGISTERED", f"User {username} registered at {ip}:{port}")
            self._log_current_users()

            return {
                'status': 'success',
                'message': f'User {username} registered successfully'
            }
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self._log_event("REGISTRATION_ERROR", f"Registration error: {e}")
            return {'status': 'error', 'message': str(e)}

    def query_users(self, request: dict, address: tuple) -> dict:
        """Query registered users based on criteria"""
        try:
            # Get client IP for logging
            client_ip_port = f"{address[0]}:{address[1]}"
            username = self.ip_to_username.get(client_ip_port, "unknown")

            query_type = request.get('query_type', 'all')
            search_term = request.get('search_term', '').lower()

            with self.lock:
                if query_type == 'all':
                    users = list(self.users.values())
                elif query_type == 'name':
                    users = [
                        user for username, user in self.users.items()
                        if search_term in username.lower()
                    ]
                elif query_type == 'ip':
                    users = [
                        user for user in self.users.values()
                        if search_term in user['ip']
                    ]
                elif query_type == 'search':
                    users = [
                        user for username, user in self.users.items()
                        if search_term in username.lower() or search_term in user['ip']
                    ]
                else:
                    return {
                        'status': 'error',
                        'message': 'Invalid query type'
                    }

            # Log the query
            self._log_event("USER_QUERY", f"Query from {username}: {query_type} - {search_term}")
            self._log_event("QUERY_RESULTS", f"Query results: {len(users)} users found")
            
            # Log detailed query results
            if users:
                user_details = []
                for user in users:
                    user_details.append(f"{user.get('username', 'unknown')} ({user['ip']}:{user['port']})")
                self._log_event("QUERY_DETAILS", f"Found users: {', '.join(user_details)}")
            else:
                self._log_event("QUERY_DETAILS", "No users found matching criteria")

            return {
                'status': 'success',
                'users': users
            }
        except Exception as e:
            logger.error(f"Query error: {e}")
            self._log_event("QUERY_ERROR", f"Query error: {e}")
            return {'status': 'error', 'message': str(e)}

def main():
    server = DirectoryServer()
    server.start()

if __name__ == "__main__":
    main() 