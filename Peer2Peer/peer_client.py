#!/usr/bin/env python3
import socket
import json
import threading
import time
import os
import sys
import logging
import argparse
import select
import datetime
import asyncio
import multiprocessing
from typing import Dict, List, Optional, Tuple, Union
from listener_process import ListenerProcess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('peer_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PeerClient:
    """Peer-to-Peer Client for the messaging system"""
    
    def __init__(self, username: str = None, host: str = '0.0.0.0', port: int = 0, 
                 directory_host: str = '127.0.0.1', directory_port: int = 5000,
                 test_mode: bool = False, data_dir: str = 'peer_data'):
        """
        Initialize the peer client
        
        Args:
            username: Username for this peer
            host: Host to bind the peer's socket to
            port: Port to bind the peer's socket to (0 for random port)
            directory_host: Directory server host
            directory_port: Directory server port
            test_mode: Whether to run in test mode (API-like interface)
            data_dir: Directory for storing data
        """
        self.username = username
        self.host = host
        self.port = port
        self.directory_host = directory_host
        self.directory_port = directory_port
        self.test_mode = test_mode
        self.data_dir = data_dir
        
        # Initialize socket with proper error handling
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the specified host and port
            self.socket.bind((self.host, self.port))
            self.port = self.socket.getsockname()[1]  # Get the actual port if 0 was specified
            
            # Start listening for incoming connections
            self.socket.listen(5)
            logger.info(f"Successfully initialized listening socket on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to initialize socket: {e}")
            raise
        
        # Store connected peers
        self.connected_peers: Dict[socket.socket, tuple] = {}  # socket -> (peer_username, peer_address)
        self.peer_usernames: Dict[socket.socket, str] = {}  # socket -> username
        
        # Store blocked and muted users
        self.blocked_users: set = set()
        self.muted_users: set = set()
        
        # Store message history
        self.message_history: Dict[str, List[Dict]] = {}  # username -> list of messages
        
        # Store local directory of contacts
        self.local_directory: Dict[str, Dict] = {}  # username -> user_info
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Path to user profile file
        self.profile_file = os.path.join(data_dir, f"{self.username}_profile.json") if self.username else None
        
        # Path to message history file
        self.history_file = os.path.join(data_dir, f"{self.username}_history.json") if self.username else None
        
        # Path to local directory file
        self.directory_file = os.path.join(data_dir, f"{self.username}_directory.json") if self.username else None
        
        # Load existing profile if available
        self._load_profile()
        
        # Load message history if available
        self._load_history()
            
        # Load local directory if available
        self._load_directory()
        
        # Flag to control the message receiving process
        self.running = True
        
        # Create a queue for communication between the main process and the asyncio process
        self.message_queue = multiprocessing.Queue()
        
        # Start the message receiving thread
        self.receive_thread = threading.Thread(target=self._receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        # Start listener process
        self.listener_process = None
        self.start_listener_process()
        
        # Start message handling thread
        self.message_thread = threading.Thread(target=self._handle_messages)
        self.message_thread.daemon = True
        self.message_thread.start()
        
        logger.info(f"Peer client initialized on {self.host}:{self.port}")
    
    def _load_profile(self):
        """Load user profile from file"""
        try:
            with open(self.profile_file, 'r') as f:
                profile = json.load(f)
                self.username = profile.get('username', self.username)
                self.host = profile.get('host', self.host)
                self.port = profile.get('port', self.port)
                self.blocked_users = set(profile.get('blocked_users', []))
                self.muted_users = set(username for username, expiry in profile.get('muted_users', {}).items())
                logger.info(f"Loaded profile for user {self.username}")
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
    
    def _save_profile(self):
        """Save user profile to file"""
        if not self.username:
            return
            
        try:
            profile = {
                'username': self.username,
                'host': self.host,
                'port': self.port,
                'blocked_users': list(self.blocked_users),
                'muted_users': {
                    username: expiry.isoformat()
                    for username, expiry in self.muted_users
                }
            }
            
            with open(self.profile_file, 'w') as f:
                json.dump(profile, f, indent=2)
                
            logger.info(f"Saved profile for user {self.username}")
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
    
    def _load_history(self):
        """Load message history from file"""
        if not self.username:
            return
            
        try:
            with open(self.history_file, 'r') as f:
                self.message_history = json.load(f)
                logger.info(f"Loaded message history for user {self.username}")
        except Exception as e:
            logger.error(f"Error loading message history: {e}")
    
    def _save_history(self):
        """Save message history to file"""
        if not self.username:
            return
            
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.message_history, f, indent=2)
                
            logger.info(f"Saved message history for user {self.username}")
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
    
    def _load_directory(self):
        """Load local directory from file"""
        if not self.username:
            return
            
        try:
            with open(self.directory_file, 'r') as f:
                self.local_directory = json.load(f)
                logger.info(f"Loaded local directory with {len(self.local_directory)} contacts")
        except Exception as e:
            logger.error(f"Error loading local directory: {e}")
    
    def _save_directory(self):
        """Save local directory to file"""
        if not self.username:
            return
            
        try:
            with open(self.directory_file, 'w') as f:
                json.dump(self.local_directory, f, indent=2)
                
            logger.info(f"Saved local directory with {len(self.local_directory)} contacts")
        except Exception as e:
            logger.error(f"Error saving local directory: {e}")
    
    def add_to_local_directory(self, user_info: Dict) -> bool:
        """
        Add a user to the local directory
        
        Args:
            user_info: User information to add
            
        Returns:
            bool: True if user was added successfully, False otherwise
        """
        try:
            # Extract username from user info
            username = user_info.get('username')
            if not username:
                logger.error("Cannot add user to local directory: username not found in user info")
                return False
                
            # Add user to local directory
            self.local_directory[username] = user_info
            
            # Save local directory
            self._save_directory()
            
            logger.info(f"Added {username} to local directory")
            return True
        except Exception as e:
            logger.error(f"Error adding user to local directory: {e}")
            return False
    
    def remove_from_local_directory(self, username: str) -> bool:
        """
        Remove a user from the local directory
        
        Args:
            username: Username of the user to remove
            
        Returns:
            bool: True if user was removed successfully, False otherwise
        """
        try:
            if username in self.local_directory:
                del self.local_directory[username]
                
                # Save local directory
                self._save_directory()
                
                logger.info(f"Removed {username} from local directory")
                return True
            else:
                logger.info(f"User {username} not found in local directory")
                return False
        except Exception as e:
            logger.error(f"Error removing user from local directory: {e}")
            return False
    
    def get_local_directory(self) -> Dict[str, Dict]:
        """
        Get the local directory
        
        Returns:
            Dict[str, Dict]: Local directory of contacts
        """
        return self.local_directory
    
    def _receive_messages(self):
        """Thread function to receive messages from connected peers"""
        while self.running:
            try:
                # Create a list of sockets to check for activity
                sockets_to_check = [self.socket] + list(self.connected_peers.keys())
                
                # Use select to check for activity without blocking
                readable, _, _ = select.select(sockets_to_check, [], [], 1.0)
                
                for sock in readable:
                    if sock == self.socket:
                        try:
                            # New connection
                            client_socket, address = sock.accept()
                            logger.info(f"New connection accepted from {address}")
                            threading.Thread(
                                target=self._handle_incoming_connection,
                                args=(client_socket, address)
                            ).start()
                        except Exception as e:
                            logger.error(f"Error accepting new connection: {e}")
                    else:
                        # Message from connected peer
                        try:
                            data = sock.recv(4096).decode('utf-8')
                            if not data:
                                # Connection closed by peer
                                peer_username, _ = self.connected_peers[sock]
                                logger.info(f"Connection closed by peer {peer_username}")
                                # Remove from connected_peers to prevent further attempts to use this socket
                                del self.connected_peers[sock]
                                sock.close()
                            else:
                                # Handle message
                                self._handle_message(sock, data)
                        except Exception as e:
                            # Handle broken connections
                            try:
                                peer_username, _ = self.connected_peers[sock]
                                logger.info(f"Connection to {peer_username} is broken")
                                # Remove from connected_peers to prevent further attempts to use this socket
                                del self.connected_peers[sock]
                                sock.close()
                            except:
                                # If we can't get the peer username, just close the socket
                                try:
                                    sock.close()
                                except:
                                    pass
            except Exception as e:
                logger.error(f"Error in receive messages loop: {e}")
                time.sleep(1)  # Prevent tight loop on persistent errors
    
    def register_with_directory(self) -> Dict:
        """
        Register with the directory server
        
        Returns:
            Dict: Response from the directory server
        """
        if not self.username:
            return {'status': 'error', 'message': 'Username not set'}
            
        dir_socket = None
        try:
            # Create a socket to connect to the directory server
            dir_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dir_socket.settimeout(5)  # Set a timeout for the connection
            dir_socket.connect((self.directory_host, self.directory_port))
            
            # Get the actual IP address for registration
            # If host is 0.0.0.0, we need to determine the actual IP address
            registration_ip = self.host
            if registration_ip == '0.0.0.0':
                # Try to determine the actual IP address
                try:
                    # Create a temporary socket to get the local IP
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    temp_socket.connect(('8.8.8.8', 80))  # Connect to a public IP
                    registration_ip = temp_socket.getsockname()[0]
                    temp_socket.close()
                    logger.info(f"Using actual IP address {registration_ip} for registration")
                except Exception as e:
                    logger.warning(f"Could not determine actual IP address: {e}")
                    registration_ip = '127.0.0.1'  # Fallback to localhost
            
            # Prepare registration request
            request = {
                'action': 'register',
                'username': self.username,
                'ip': registration_ip,
                'port': self.port,
                'profile': {
                    'status': 'online',
                    'last_seen': datetime.datetime.now().isoformat()
                }
            }
            
            # Send request
            dir_socket.send(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response_data = dir_socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)
            
            # Check if the directory server reported a username conflict
            if response['status'] == 'error' and response.get('error_code') == 'username_taken':
                logger.info(f"Username {self.username} is already taken")
                return response
            
            # Save profile after successful registration
            if response['status'] == 'success':
                self._save_profile()
                
            return response
        except socket.timeout:
            logger.error("Timeout while connecting to directory server")
            return {'status': 'error', 'message': 'Connection timeout'}
        except ConnectionRefusedError:
            logger.error("Connection refused by directory server")
            return {'status': 'error', 'message': 'Connection refused'}
        except Exception as e:
            logger.error(f"Error registering with directory: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if dir_socket:
                try:
                    dir_socket.shutdown(socket.SHUT_RDWR)
                    dir_socket.close()
                except:
                    pass
    
    def query_directory(self, query_type: str = 'all', search_term: str = '') -> Dict:
        """
        Query the directory server for users
        
        Args:
            query_type: Type of query ('all', 'name', 'ip', 'search')
            search_term: Search term for filtering results
            
        Returns:
            Dict: Response from the directory server
        """
        dir_socket = None
        try:
            # Create a socket to connect to the directory server
            dir_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dir_socket.settimeout(5)  # Set a timeout for the connection
            dir_socket.connect((self.directory_host, self.directory_port))
            
            # Prepare query request
            request = {
                'action': 'query',
                'query_type': query_type,
                'search_term': search_term
            }
            
            # Send request
            dir_socket.send(json.dumps(request).encode('utf-8'))
            
            # Receive response
            response_data = dir_socket.recv(4096).decode('utf-8')
            response = json.loads(response_data)
            
            return response
        except socket.timeout:
            logger.error("Timeout while connecting to directory server")
            return {'status': 'error', 'message': 'Connection timeout'}
        except ConnectionRefusedError:
            logger.error("Connection refused by directory server")
            return {'status': 'error', 'message': 'Connection refused'}
        except Exception as e:
            logger.error(f"Error querying directory: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            if dir_socket:
                try:
                    dir_socket.shutdown(socket.SHUT_RDWR)
                    dir_socket.close()
                except:
                    pass
    
    def connect_to_peer(self, peer_username: str) -> bool:
        """
        Connect to a peer
        
        Args:
            peer_username: Username of the peer to connect to
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Check if already connected
        if peer_username in self.connected_peers:
            logger.info(f"Already connected to {peer_username}")
            return True
            
        # Check if peer is blocked
        if peer_username in self.blocked_users:
            logger.warning(f"Cannot connect to blocked user {peer_username}")
            return False
            
        # Check if peer is muted
        if peer_username in self.muted_users:
            if datetime.datetime.now() < self.muted_users[peer_username]:
                logger.warning(f"Cannot connect to muted user {peer_username}")
                return False
            else:
                # Mute has expired, remove it
                self.muted_users.remove(peer_username)
                self._save_profile()
        
        try:
            # First check if peer is in local directory
            if peer_username in self.local_directory:
                peer_info = self.local_directory[peer_username]
                logger.info(f"Found {peer_username} in local directory: {peer_info}")
                
                # Check if the peer has been seen recently (within the last 5 minutes)
                last_seen = peer_info.get('last_seen')
                if last_seen:
                    try:
                        last_seen_time = datetime.datetime.fromisoformat(last_seen)
                        time_diff = datetime.datetime.now() - last_seen_time
                        if time_diff.total_seconds() > 300:  # 5 minutes
                            logger.info(f"Peer {peer_username} in local directory but last seen {time_diff.total_seconds():.0f} seconds ago, querying directory server")
                            # Peer in local directory but not seen recently, query directory server
                            response = self.query_directory('name', peer_username)
                            if response['status'] == 'success' and response['users']:
                                # Update local directory with latest info
                                for user in response['users']:
                                    if user['username'] == peer_username:
                                        self.add_to_local_directory(user)
                                        peer_info = user
                                        logger.info(f"Updated local directory with latest info for {peer_username}")
                                        break
                    except Exception as e:
                        logger.warning(f"Error checking last_seen for {peer_username}: {e}")
                        # Continue with local directory info
                
                # Use peer info from local directory
                peer_ip = peer_info['ip']
                peer_port = peer_info['port']
            else:
                # Peer not in local directory, query directory server
                logger.info(f"Peer {peer_username} not found in local directory, querying directory server")
                response = self.query_directory('name', peer_username)
                
                if response['status'] != 'success' or not response['users']:
                    logger.error(f"Failed to find peer {peer_username} in directory")
                    return False
                    
                # Find the peer in the results
                peer_info = None
                for user in response['users']:
                    if user['username'] == peer_username:
                        peer_info = user
                        break
                        
                if not peer_info:
                    logger.error(f"Peer {peer_username} not found in directory results")
                    return False
                    
                # Add to local directory
                self.add_to_local_directory(peer_info)
                
                peer_ip = peer_info['ip']
                peer_port = peer_info['port']
            
            # Get our own IP and port for logging
            our_ip = self.host
            if our_ip == '0.0.0.0':
                try:
                    # Create a temporary socket to get the local IP
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    temp_socket.connect(('8.8.8.8', 80))  # Connect to a public IP
                    our_ip = temp_socket.getsockname()[0]
                    temp_socket.close()
                except Exception as e:
                    logger.warning(f"Could not determine our IP address: {e}")
                    our_ip = '127.0.0.1'  # Fallback to localhost
            
            logger.info(f"Attempting to connect to {peer_username} at {peer_ip}:{peer_port} from {our_ip}:{self.port}")
            
            # Create a socket to connect to the peer
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(5)  # Set a timeout for the connection
            
            try:
                # Connect to the peer
                logger.info(f"Connecting to {peer_username} at {peer_ip}:{peer_port}")
                peer_socket.connect((peer_ip, peer_port))
                
                # Send connection request
                request = {
                    'action': 'connect',
                    'username': self.username,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
                logger.info(f"Sending connection request to {peer_username}: {request}")
                peer_socket.send(json.dumps(request).encode('utf-8'))
                
                # Wait for response
                logger.info(f"Waiting for connection response from {peer_username}")
                response_data = peer_socket.recv(4096).decode('utf-8')
                response = json.loads(response_data)
                
                logger.info(f"Received connection response from {peer_username}: {response}")
                
                if response['status'] != 'success':
                    logger.error(f"Connection to {peer_username} failed: {response['message']}")
                    peer_socket.close()
                    return False
                    
                # Store the connection
                self.connected_peers[peer_socket] = (peer_username, (peer_ip, peer_port))
                self.peer_usernames[peer_socket] = peer_username
                
                logger.info(f"Successfully connected to {peer_username}")
                return True
                
            except socket.timeout:
                logger.error(f"Timeout connecting to {peer_username}")
                peer_socket.close()
                return False
            except ConnectionRefusedError:
                logger.error(f"Connection refused by {peer_username}")
                peer_socket.close()
                return False
            except Exception as e:
                logger.error(f"Error connecting to {peer_username}: {e}")
                peer_socket.close()
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to peer {peer_username}: {e}")
            return False
    
    def send_message(self, peer_username: str, message: str) -> bool:
        """
        Send a message to a peer
        
        Args:
            peer_username: Username of the peer to send the message to
            message: Message content
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        # Check if peer is blocked
        if peer_username in self.blocked_users:
            logger.warning(f"Cannot send message to blocked user {peer_username}")
            return False
            
        # Check if peer is muted
        if peer_username in self.muted_users:
            if datetime.datetime.now() < self.muted_users[peer_username]:
                logger.warning(f"Cannot send message to muted user {peer_username}")
                return False
            else:
                # Mute has expired, remove it
                self.muted_users.remove(peer_username)
                self._save_profile()
        
        try:
            # Connect to the peer if not already connected
            if peer_username not in self.peer_usernames.values():
                logger.info(f"Not connected to {peer_username}, attempting to connect...")
                if not self.connect_to_peer(peer_username):
                    logger.error(f"Failed to connect to {peer_username}, cannot send message")
                    return False
                else:
                    logger.info(f"Successfully connected to {peer_username}, proceeding to send message")
            else:
                logger.info(f"Already connected to {peer_username}, proceeding to send message")
                    
            # Find the peer's socket
            peer_socket = None
            for sock, username in self.peer_usernames.items():
                if username == peer_username:
                    peer_socket = sock
                    break
                    
            if peer_socket is None:
                logger.error(f"Could not find socket for {peer_username}")
                return False
            
            # Prepare message with standardized format
            message_data = {
                'action': 'message',
                'from': self.username,
                'content': message,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            # Send message with timeout
            try:
                logger.info(f"Preparing to send message to {peer_username}: {message_data}")
                peer_socket.settimeout(5)
                logger.info(f"Sending message data to {peer_username}")
                peer_socket.send(json.dumps(message_data).encode('utf-8'))
                
                # Wait for acknowledgment
                logger.info(f"Waiting for acknowledgment from {peer_username}")
                ack_data = peer_socket.recv(4096).decode('utf-8')
                ack = json.loads(ack_data)
                
                logger.info(f"Received acknowledgment from {peer_username}: {ack}")
                
                if ack['status'] != 'success':
                    logger.error(f"Message to {peer_username} not acknowledged: {ack['message']}")
                    return False
                    
                logger.info(f"Message sent to {peer_username} and acknowledged")
                
                # Store message in history
                if peer_username not in self.message_history:
                    self.message_history[peer_username] = []
                    
                self.message_history[peer_username].append({
                    'direction': 'outgoing',
                    'content': message,
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
                # Save message history
                self._save_history()
                
                # Close the connection after successful message delivery
                logger.info(f"Closing connection to {peer_username} after successful message delivery")
                peer_socket.close()
                del self.connected_peers[peer_socket]
                del self.peer_usernames[peer_socket]
                
                return True
            except socket.timeout:
                logger.error(f"Timeout waiting for acknowledgment from {peer_username}")
                # Don't remove the connection, just return False
                return False
            except (socket.error, ConnectionError) as e:
                logger.error(f"Error sending message to {peer_username}: {e}")
                # Don't remove the connection, just return False
                return False
            
        except Exception as e:
            logger.error(f"Error sending message to {peer_username}: {e}")
            # Don't clean up the connection, just return False
            return False
    
    def block_user(self, peer_username: str) -> bool:
        """
        Block a user
        
        Args:
            peer_username: Username of the peer to block
            
        Returns:
            bool: True if user was blocked successfully, False otherwise
        """
        try:
            # Add user to blocked list
            if peer_username not in self.blocked_users:
                self.blocked_users.add(peer_username)
                
                # Close connection if exists
                if peer_username in self.connected_peers:
                    peer_socket, _ = self.connected_peers[peer_socket]
                    peer_socket.close()
                    del self.connected_peers[peer_socket]
                    del self.peer_usernames[peer_socket]
                
                # Save profile
                self._save_profile()
                
                logger.info(f"User {peer_username} blocked")
                return True
            else:
                logger.info(f"User {peer_username} is already blocked")
                return True
        except Exception as e:
            logger.error(f"Error blocking user {peer_username}: {e}")
            return False
    
    def mute_user(self, peer_username: str, hours: int) -> bool:
        """
        Mute a user for a specified number of hours
        
        Args:
            peer_username: Username of the peer to mute
            hours: Number of hours to mute the user
            
        Returns:
            bool: True if user was muted successfully, False otherwise
        """
        try:
            # Calculate mute expiration time
            expiry_time = datetime.datetime.now() + datetime.timedelta(hours=hours)
            
            # Add or update mute
            self.muted_users.add(peer_username)
            
            # Save profile
            self._save_profile()
            
            logger.info(f"User {peer_username} muted for {hours} hours")
            return True
        except Exception as e:
            logger.error(f"Error muting user {peer_username}: {e}")
            return False
    
    def _handle_incoming_connection(self, client_socket: socket.socket, address: tuple):
        """
        Handle an incoming connection
        
        Args:
            client_socket: Socket of the incoming connection
            address: Address of the incoming connection
        """
        try:
            logger.info(f"Handling incoming connection from {address}")
            
            # Set a timeout for receiving the connection request
            client_socket.settimeout(5)
            
            # Receive connection request
            logger.info(f"Waiting for connection request from {address}")
            data = client_socket.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            # Reset timeout
            client_socket.settimeout(None)
            
            logger.info(f"Received connection request from {address}: {request}")
            
            if request['action'] != 'connect':
                logger.warning(f"Invalid connection request from {address}: {request}")
                response = {
                    'status': 'error',
                    'message': 'Invalid connection request'
                }
                logger.info(f"Sending error response to {address}: {response}")
                client_socket.send(json.dumps(response).encode('utf-8'))
                # Don't close the socket
                return
                
            peer_username, _ = self.connected_peers[client_socket]
            logger.info(f"Connection request from peer {peer_username} at {address}")
            
            # Check if peer is blocked
            if peer_username in self.blocked_users:
                logger.warning(f"Connection from blocked user {peer_username} rejected")
                response = {
                    'status': 'error',
                    'message': 'Connection rejected: user is blocked'
                }
                logger.info(f"Sending rejection response to {peer_username}: {response}")
                client_socket.send(json.dumps(response).encode('utf-8'))
                # Don't close the socket
                return
                
            # Check if peer is muted
            if peer_username in self.muted_users:
                if datetime.datetime.now() < self.muted_users[peer_username]:
                    logger.warning(f"Connection from muted user {peer_username} rejected")
                    response = {
                        'status': 'error',
                        'message': 'Connection rejected: user is muted'
                    }
                    logger.info(f"Sending rejection response to {peer_username}: {response}")
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    # Don't close the socket
                    return
                else:
                    # Mute has expired, remove it
                    logger.info(f"Mute for {peer_username} has expired, removing")
                    self.muted_users.remove(peer_username)
                    self._save_profile()
            
            # Accept connection with standardized response format
            response = {
                'status': 'success',
                'message': 'Connection accepted',
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"Sending connection acceptance to {peer_username}: {response}")
            client_socket.send(json.dumps(response).encode('utf-8'))
            
            # Store the connection
            self.connected_peers[client_socket] = (peer_username, address)
            self.peer_usernames[client_socket] = peer_username
            
            # Get the actual IP address of the peer
            peer_ip, peer_port = address
            
            logger.info(f"Stored connection to {peer_username} at {peer_ip}:{peer_port}")
            
            # Add to local directory if not already there
            if peer_username not in self.local_directory:
                # Create a basic user info entry
                user_info = {
                    'username': peer_username,
                    'ip': peer_ip,
                    'port': peer_port,
                    'last_seen': datetime.datetime.now().isoformat()
                }
                logger.info(f"Adding {peer_username} to local directory: {user_info}")
                self.add_to_local_directory(user_info)
            else:
                # Update existing entry with latest information
                logger.info(f"Updating {peer_username} in local directory with latest information")
                self.local_directory[peer_username]['ip'] = peer_ip
                self.local_directory[peer_username]['port'] = peer_port
                self.local_directory[peer_username]['last_seen'] = datetime.datetime.now().isoformat()
                self._save_directory()
            
            logger.info(f"Successfully connected to {peer_username}")
        except socket.timeout:
            logger.error(f"Timeout waiting for connection request from {address}")
            # Don't close the socket
        except Exception as e:
            logger.error(f"Error handling incoming connection from {address}: {e}")
            # Don't close the socket
    
    def _handle_message(self, peer_socket: socket.socket, data: str):
        """
        Handle an incoming message
        
        Args:
            peer_socket: Socket of the peer that sent the message
            data: Message data
        """
        try:
            message_data = json.loads(data)
            
            if message_data['action'] != 'message':
                logger.warning(f"Invalid message from {self.peer_usernames[peer_socket]}")
                return
                
            peer_username, _ = self.connected_peers[peer_socket]
            content = message_data['content']
            timestamp = message_data['timestamp']
            
            # Add sender to local directory if not already there
            if peer_username not in self.local_directory:
                # Create a basic user info entry
                user_info = {
                    'username': peer_username,
                    'ip': peer_socket.getpeername()[0],
                    'port': peer_socket.getpeername()[1],
                    'last_seen': timestamp
                }
                self.add_to_local_directory(user_info)
            else:
                # Update existing entry with latest information
                self.local_directory[peer_username]['last_seen'] = timestamp
                self.local_directory[peer_username]['ip'] = peer_socket.getpeername()[0]
                self.local_directory[peer_username]['port'] = peer_socket.getpeername()[1]
                self._save_directory()
            
            # Store message in history
            if peer_username not in self.message_history:
                self.message_history[peer_username] = []
                
            self.message_history[peer_username].append({
                'direction': 'incoming',
                'content': content,
                'timestamp': timestamp
            })
            
            # Save message history
            self._save_history()
            
            # Send acknowledgment with standardized format
            ack = {
                'status': 'success',
                'message': 'Message received',
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            logger.info(f"Sending acknowledgment to {peer_username}")
            try:
                peer_socket.send(json.dumps(ack).encode('utf-8'))
                logger.info(f"Acknowledgment sent to {peer_username}")
            except Exception as e:
                logger.error(f"Error sending acknowledgment to {peer_username}: {e}")
            
            # Print message if not in test mode
            if not self.test_mode:
                print(f"\n[{peer_username}] {content}")
                
            logger.info(f"Message received from {peer_username}")
        except Exception as e:
            logger.error(f"Error handling message from {self.peer_usernames[peer_socket]}: {e}")
    
    def disconnect_from_peer(self, peer_username: str) -> bool:
        """
        Disconnect from a peer
        
        Args:
            peer_username: Username of the peer to disconnect from
            
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        try:
            if peer_username in self.connected_peers:
                peer_socket, _ = self.connected_peers[peer_username]
                peer_socket.close()
                del self.connected_peers[peer_socket]
                del self.peer_usernames[peer_socket]
                
                logger.info(f"Disconnected from {peer_username}")
                return True
            else:
                logger.info(f"Not connected to {peer_username}")
                return True
        except Exception as e:
            logger.error(f"Error disconnecting from {peer_username}: {e}")
            return False
    
    def disconnect_from_all_peers(self):
        """Disconnect from all peers"""
        for peer_socket in list(self.connected_peers.keys()):
            self.disconnect_from_peer(self.peer_usernames[peer_socket])
    
    def shutdown(self):
        """Shutdown the peer client"""
        logger.info("Shutting down peer client...")
        
        # Set running flag to False to stop threads
        self.running = False
        
        # Wait for threads to finish
        if hasattr(self, 'receive_thread') and self.receive_thread.is_alive():
            logger.info("Waiting for receive thread to finish...")
            self.receive_thread.join(timeout=5)
            
        if hasattr(self, 'message_thread') and self.message_thread.is_alive():
            logger.info("Waiting for message thread to finish...")
            self.message_thread.join(timeout=5)
            
        if hasattr(self, 'listener_monitor_thread') and self.listener_monitor_thread.is_alive():
            logger.info("Waiting for listener monitor thread to finish...")
            self.listener_monitor_thread.join(timeout=5)
        
        # Shutdown the listener process
        if hasattr(self, 'listener_process') and self.listener_process and self.listener_process.is_alive():
            logger.info("Shutting down listener process...")
            self.listener_process.shutdown()
            self.listener_process.join(timeout=5)
            if self.listener_process.is_alive():
                logger.warning("Listener process did not terminate gracefully, forcing termination")
                self.listener_process.terminate()
        
        # Close the socket
        if hasattr(self, 'socket') and self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        # Close the message queue
        if hasattr(self, 'message_queue') and self.message_queue:
            try:
                self.message_queue.close()
            except:
                pass
        
        logger.info("Peer client shutdown complete")
    
    def check_peer_online(self, peer_username: str) -> bool:
        """
        Check if a peer is online by querying the directory server
        
        Args:
            peer_username: Username of the peer to check
            
        Returns:
            bool: True if peer is online, False otherwise
        """
        try:
            # Query directory for peer's status
            response = self.query_directory('name', peer_username)
            
            if response['status'] != 'success' or not response['users']:
                logger.info(f"Peer {peer_username} not found in directory")
                return False
                
            # Find the peer in the results
            for user in response['users']:
                if user.get('username') == peer_username:
                    # Check if the peer has been seen recently (within the last 5 minutes)
                    last_seen = user.get('profile', {}).get('last_seen')
                    if last_seen:
                        try:
                            last_seen_time = datetime.datetime.fromisoformat(last_seen)
                            time_diff = datetime.datetime.now() - last_seen_time
                            if time_diff.total_seconds() < 300:  # 5 minutes
                                logger.info(f"Peer {peer_username} is online (last seen {time_diff.total_seconds():.0f} seconds ago)")
                                return True
                            else:
                                logger.info(f"Peer {peer_username} is offline (last seen {time_diff.total_seconds():.0f} seconds ago)")
                                return False
                        except:
                            pass
                    
                    # If we can't determine from last_seen, assume they're online if they're in the directory
                    logger.info(f"Peer {peer_username} is in the directory")
                    return True
            
            logger.info(f"Peer {peer_username} not found in directory results")
            return False
        except Exception as e:
            logger.error(f"Error checking if peer {peer_username} is online: {e}")
            return False
    
    def start_listener_process(self):
        """Start the listener process for handling incoming connections"""
        logger.info("Starting listener process...")
        
        # Ensure message queue is initialized
        if not hasattr(self, 'message_queue') or self.message_queue is None:
            logger.info("Initializing message queue")
            self.message_queue = multiprocessing.Queue()
        
        # Create and start the listener process
        logger.info(f"Creating listener process with host={self.host}, port={self.port}, username={self.username}")
        self.listener_process = ListenerProcess(
            host=self.host,
            port=self.port,
            username=self.username,
            data_dir=self.data_dir,
            message_queue=self.message_queue
        )
        
        logger.info("Starting listener process")
        self.listener_process.start()
        
        # Wait for the process to initialize and get the actual port
        logger.info("Waiting for listener process to initialize...")
        time.sleep(1)  # Give the process time to start
        
        if self.port == 0:  # If port was auto-assigned
            self.port = self.listener_process.port
            logger.info(f"Listener process started on port {self.port}")
        else:
            logger.info(f"Listener process started on specified port {self.port}")
            
        # Verify the process is running
        if self.listener_process.is_alive():
            logger.info("Listener process is running successfully")
        else:
            logger.error("Listener process failed to start")
            
        # Start a thread to monitor the listener process
        self.listener_monitor_thread = threading.Thread(target=self._monitor_listener_process)
        self.listener_monitor_thread.daemon = True
        self.listener_monitor_thread.start()
        
    def _monitor_listener_process(self):
        """Monitor the listener process and restart it if it goes offline"""
        logger.info("Starting listener process monitor thread")
        while self.running:
            try:
                # Check if the listener process is still alive
                if not self.listener_process.is_alive():
                    logger.warning("Listener process is not alive, attempting to restart...")
                    self.restart_listener_process()
                
                # Sleep for a bit before checking again
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error monitoring listener process: {e}")
                time.sleep(5)  # Sleep on error to prevent tight loop
                
    def restart_listener_process(self):
        """Restart the listener process if it has gone offline"""
        logger.info("Restarting listener process...")
        
        # Shutdown the existing process if it's still running
        if hasattr(self, 'listener_process') and self.listener_process and self.listener_process.is_alive():
            try:
                self.listener_process.shutdown()
                self.listener_process.join(timeout=5)
                if self.listener_process.is_alive():
                    logger.warning("Listener process did not terminate gracefully, forcing termination")
                    self.listener_process.terminate()
            except Exception as e:
                logger.error(f"Error shutting down listener process: {e}")
        
        # Start a new listener process
        self.start_listener_process()
    
    def _handle_messages(self):
        """Handle messages from the listener process"""
        logger.info("Message handling thread started")
        while self.running:  # Use the running flag to control the loop
            try:
                # Check for messages from the listener process
                if not self.message_queue.empty():
                    logger.info("Message found in queue, processing...")
                    message = self.message_queue.get()
                    logger.info(f"Retrieved message from queue: {message}")
                    
                    if message['type'] == 'message':
                        # Update message history
                        peer_username = message['from']
                        logger.info(f"Processing message from {peer_username}")
                        
                        if peer_username not in self.message_history:
                            self.message_history[peer_username] = []
                        
                        self.message_history[peer_username].append({
                            'direction': 'incoming',
                            'content': message['content'],
                            'timestamp': message['timestamp']
                        })
                        
                        # Save message history
                        self._save_history()
                        logger.info(f"Message history updated and saved for {peer_username}")
                        
                        # Print message if not in test mode
                        if not self.test_mode:
                            print(f"\n[{peer_username}] {message['content']}")
                            logger.info(f"Message displayed to user: {message['content'][:50]}...")
                    else:
                        logger.warning(f"Received unknown message type: {message['type']}")
                
                time.sleep(0.1)  # Prevent tight loop
            except Exception as e:
                logger.error(f"Error handling messages: {e}")
                time.sleep(1)  # Prevent tight loop on errors

def interactive_mode(client: PeerClient):
    """
    Run the peer client in interactive mode
    
    Args:
        client: PeerClient instance
    """
    print("\nPeer-to-Peer Client - Interactive Mode")
    print("=====================================")
    
    # Register with directory server
    print("\nRegistering with directory server...")
    
    # Keep trying to register until successful or user cancels
    while True:
        response = client.register_with_directory()
        
        # Check if username was taken
        if response['status'] == 'error' and response.get('error_code') == 'username_taken':
            print(f"\n{response['message']}")
            new_username = input("Please enter a new username (or 'cancel' to exit): ")
            
            if new_username.lower() == 'cancel':
                print("Registration cancelled. Exiting...")
                return
                
            # Update the client's username
            client.username = new_username
            print(f"Trying to register with username: {new_username}")
            continue
        elif response['status'] != 'success':
            print(f"Registration failed: {response['message']}")
            return
        else:
            # Registration successful
            break
    
    print("Registration successful!")
    
    while True:
        print("\nOptions:")
        print("1. Query directory for users")
        print("2. Send message to user")
        print("3. Block user")
        print("4. Mute user")
        print("5. View message history")
        print("6. Manage local directory")
        print("7. View profile information")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            print("\nQuery options:")
            print("1. All users")
            print("2. Search by username")
            print("3. Search by IP")
            print("4. General search")
            
            query_choice = input("\nEnter your choice (1-4): ")
            
            if query_choice == '1':
                response = client.query_directory('all')
            elif query_choice == '2':
                search_term = input("Enter username to search for: ")
                response = client.query_directory('name', search_term)
            elif query_choice == '3':
                search_term = input("Enter IP to search for: ")
                response = client.query_directory('ip', search_term)
            elif query_choice == '4':
                search_term = input("Enter search term: ")
                response = client.query_directory('search', search_term)
            else:
                print("Invalid choice")
                continue
                
            if response['status'] == 'success':
                print("\nUsers found:")
                for i, user in enumerate(response['users'], 1):
                    # Try to get username from the user object, fall back to 'unknown' if not found
                    username = user.get('username', 'unknown')
                    print(f"{i}. {username} ({user['ip']}:{user['port']})")
                
                # Ask if user wants to save any of these users to local directory
                save_choice = input("\nDo you want to save any users to your local directory? (y/n): ")
                if save_choice.lower() == 'y':
                    while True:
                        user_index = input("Enter the number of the user to save (or 'done' to finish): ")
                        if user_index.lower() == 'done':
                            break
                            
                        try:
                            index = int(user_index) - 1
                            if 0 <= index < len(response['users']):
                                user = response['users'][index]
                                if client.add_to_local_directory(user):
                                    print(f"User {user.get('username', 'unknown')} added to local directory")
                                else:
                                    print(f"Failed to add user to local directory")
                            else:
                                print("Invalid user number")
                        except ValueError:
                            print("Invalid input")
            else:
                print(f"Query failed: {response['message']}")
                
        elif choice == '2':
            # First check if there are users in the local directory
            local_directory = client.get_local_directory()
            if local_directory:
                print("\nLocal contacts:")
                for i, (username, user_info) in enumerate(local_directory.items(), 1):
                    print(f"{i}. {username} ({user_info['ip']}:{user_info['port']})")
                
                use_local = input("\nDo you want to send a message to a local contact? (y/n): ")
                if use_local.lower() == 'y':
                    try:
                        contact_index = int(input("Enter the number of the contact: ")) - 1
                        if 0 <= contact_index < len(local_directory):
                            peer_username = list(local_directory.keys())[contact_index]
                        else:
                            print("Invalid contact number")
                            continue
                    except ValueError:
                        print("Invalid input")
                        continue
                else:
                    peer_username = input("Enter username to send message to: ")
            else:
                peer_username = input("Enter username to send message to: ")
                
            # Check if peer is online before attempting to send message
            print(f"Checking if {peer_username} is online...")
            if not client.check_peer_online(peer_username):
                print(f"Error: {peer_username} is not online or not found in the directory.")
                print("The user may be offline, or there might be network connectivity issues.")
                print("You can try querying the directory to get updated information.")
                continue
                
            message = input("Enter message: ")
            
            print(f"Sending message to {peer_username}...")
            if client.send_message(peer_username, message):
                print(f"Message sent to {peer_username}")
            else:
                print(f"Failed to send message to {peer_username}")
                print("Possible reasons:")
                print("1. The user is offline or not accepting connections")
                print("2. There are network connectivity issues")
                print("3. A firewall is blocking the connection")
                print("4. The user's IP address or port has changed")
                print("\nTry querying the directory again to get updated information.")
                
        elif choice == '3':
            peer_username = input("Enter username to block: ")
            
            if client.block_user(peer_username):
                print(f"User {peer_username} blocked")
            else:
                print(f"Failed to block user {peer_username}")
                
        elif choice == '4':
            peer_username = input("Enter username to mute: ")
            try:
                hours = int(input("Enter number of hours to mute: "))
                if client.mute_user(peer_username, hours):
                    print(f"User {peer_username} muted for {hours} hours")
                else:
                    print(f"Failed to mute user {peer_username}")
            except ValueError:
                print("Invalid number of hours")
                
        elif choice == '5':
            if not client.message_history:
                print("No message history")
                continue
                
            print("\nMessage History:")
            for peer_username, messages in client.message_history.items():
                print(f"\nConversation with {peer_username}:")
                for message in messages:
                    direction = "Sent" if message['direction'] == 'outgoing' else "Received"
                    timestamp = datetime.datetime.fromisoformat(message['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] {direction}: {message['content']}")
                    
        elif choice == '6':
            print("\nLocal Directory Management:")
            print("1. View local directory")
            print("2. Remove contact from local directory")
            print("3. Back to main menu")
            
            dir_choice = input("\nEnter your choice (1-3): ")
            
            if dir_choice == '1':
                local_directory = client.get_local_directory()
                if not local_directory:
                    print("Local directory is empty")
                else:
                    print("\nLocal Directory:")
                    for i, (username, user_info) in enumerate(local_directory.items(), 1):
                        print(f"{i}. {username} ({user_info['ip']}:{user_info['port']})")
                        
            elif dir_choice == '2':
                local_directory = client.get_local_directory()
                if not local_directory:
                    print("Local directory is empty")
                else:
                    print("\nLocal Directory:")
                    for i, (username, user_info) in enumerate(local_directory.items(), 1):
                        print(f"{i}. {username} ({user_info['ip']}:{user_info['port']})")
                        
                    try:
                        contact_index = int(input("\nEnter the number of the contact to remove: ")) - 1
                        if 0 <= contact_index < len(local_directory):
                            peer_username = list(local_directory.keys())[contact_index]
                            if client.remove_from_local_directory(peer_username):
                                print(f"Contact {peer_username} removed from local directory")
                            else:
                                print(f"Failed to remove contact {peer_username}")
                        else:
                            print("Invalid contact number")
                    except ValueError:
                        print("Invalid input")
                        
            elif dir_choice == '3':
                continue
            else:
                print("Invalid choice")
                
        elif choice == '7':
            # Display profile information
            print("\nProfile Information:")
            print(f"Username: {client.username}")
            print(f"Host: {client.host}")
            print(f"Port: {client.port}")
            
            # Check port status
            port_open = False
            try:
                # Create a temporary socket to check if the port is in use
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                temp_socket.settimeout(1)
                result = temp_socket.connect_ex((client.host, client.port))
                temp_socket.close()
                
                if result == 0:
                    print("Port Status: Open and listening")
                    port_open = True
                else:
                    print("Port Status: Closed or not listening")
                    port_open = False
            except Exception as e:
                print(f"Port Status: Error checking port ({e})")
                port_open = False
            
            # Display connected peers
            print("\nConnected Peers:")
            if client.connected_peers:
                for peer_socket, _ in client.connected_peers.values():
                    print(f"- {client.peer_usernames[peer_socket]}")
            else:
                print("No connected peers")
                
            # Offer to open port if it's closed
            if not port_open:
                print("\nYour port appears to be closed or not listening.")
                print("This may prevent other peers from connecting to you.")
                open_port = input("Would you like to open the port for listening? (y/n): ")
                
                if open_port.lower() == 'y':
                    print("Attempting to open port for listening...")
                    
                    # Create a new socket for listening
                    try:
                        # Close the existing socket if it exists
                        if hasattr(client, 'socket') and client.socket:
                            try:
                                client.socket.close()
                            except:
                                pass
                        
                        # Create a new socket
                        client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        client.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        
                        # Bind to the specified host and port
                        client.socket.bind((client.host, client.port))
                        
                        # Start listening for incoming connections
                        client.socket.listen(5)
                        
                        print(f"Port {client.port} is now open and listening for connections.")
                        
                        # Update the client's running flag to ensure the receive thread continues
                        client.running = True
                        
                        # Re-register with the directory server to update the port information
                        print("Re-registering with directory server...")
                        response = client.register_with_directory()
                        if response['status'] == 'success':
                            print("Successfully re-registered with directory server.")
                        else:
                            print(f"Failed to re-register with directory server: {response['message']}")
                            
                    except Exception as e:
                        print(f"Error opening port: {e}")
                        print("Possible reasons:")
                        print("1. The port is already in use by another application")
                        print("2. You don't have permission to bind to this port")
                        print("3. A firewall is blocking the port")
                        print("\nTry using a different port or check your firewall settings.")
                
        elif choice == '8':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice")

def load_or_create_profile() -> Tuple[str, str, int]:
    """
    Load an existing profile or create a new one
    
    Returns:
        Tuple[str, str, int]: Username, host, port
    """
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "peer_data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Check for existing profiles
    profiles = [f for f in os.listdir(data_dir) if f.endswith('_profile.json')]
    
    if profiles:
        print("\nExisting profiles found:")
        for i, profile in enumerate(profiles, 1):
            username = profile.replace('_profile.json', '')
            print(f"{i}. {username}")
            
        print(f"{len(profiles) + 1}. Create new profile")
        
        choice = input("\nSelect a profile (or create new): ")
        
        try:
            choice = int(choice)
            if 1 <= choice <= len(profiles):
                # Load existing profile
                username = profiles[choice - 1].replace('_profile.json', '')
                profile_file = os.path.join(data_dir, profiles[choice - 1])
                
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                    
                # Check if the username might be taken
                print(f"\nNote: If the username '{username}' is already taken by another user,")
                print("you will be prompted to choose a different username during registration.")
                
                return username, '0.0.0.0', 0
            elif choice == len(profiles) + 1:
                # Create new profile
                username = input("Enter username: ")
                return username, '0.0.0.0', 0
            else:
                print("Invalid choice")
                return None, None, None
        except ValueError:
            print("Invalid choice")
            return None, None, None
    else:
        # Create new profile
        username = input("Enter username: ")
        return username, '0.0.0.0', 0

def main():
    """Main entry point for the peer client"""
    parser = argparse.ArgumentParser(description='Peer-to-Peer Client')
    parser.add_argument('--username', help='Username for this peer')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the peer\'s socket to')
    parser.add_argument('--port', type=int, default=0, help='Port to bind the peer\'s socket to')
    parser.add_argument('--directory-host', default='127.0.0.1', help='Directory server host')
    parser.add_argument('--directory-port', type=int, default=5000, help='Directory server port')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # If username not provided, load or create a profile
    if not args.username:
        username, host, port = load_or_create_profile()
        if not username:
            print("Failed to load or create profile")
            return 1
            
        args.username = username
        if host:
            args.host = host
        if port:
            args.port = port
    
    # Create the peer client
    client = PeerClient(
        username=args.username,
        host=args.host,
        port=args.port,
        directory_host=args.directory_host,
        directory_port=args.directory_port,
        test_mode=args.test_mode
    )
    
    try:
        if args.test_mode:
            # Test mode - just print a message and keep the client running
            print(f"Peer client started in test mode with username {args.username}")
            print("Use the client object to interact with the API")
            print("Press Ctrl+C to exit")
            
            # Keep the main thread alive
            while True:
                time.sleep(1)
        else:
            # Interactive mode
            interactive_mode(client)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.shutdown()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 