#!/usr/bin/env python3
import socket
import json
import os
import logging
import sys
import time
import select
from typing import Dict, Optional
from multiprocessing import Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ListenerProcess(Process):
    """Process that handles incoming connections and writes messages to user history"""
    
    def __init__(self, host: str, port: int, username: str, data_dir: str, message_queue=None):
        """
        Initialize the listener process
        
        Args:
            host: Host to bind the listener socket to
            port: Port to bind the listener socket to
            username: Username for this peer
            data_dir: Directory to store user data
            message_queue: Optional queue for communication with main process
        """
        super().__init__()  # Initialize the Process parent class
        self.host = host
        self.port = port
        self.username = username
        self.data_dir = data_dir
        self.message_queue = message_queue
        self.running = True
        self.socket = None
        
        # Path to message history file
        self.history_file = os.path.join(self.data_dir, f"{self.username}_history.json")
        
        # Load existing message history if available
        self.message_history = self._load_history()
    
    def _init_socket(self):
        """Initialize the listening socket"""
        try:
            # Close existing socket if it exists
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            # Create a new socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Try to bind to the specified host and port
            try:
                self.socket.bind((self.host, self.port))
            except OSError as e:
                # If the port is already in use, try to find an available port
                if e.errno == 98 or e.errno == 10048:  # Address already in use
                    logger.warning(f"Port {self.port} is already in use, trying to find an available port")
                    self.socket.bind((self.host, 0))  # Let the OS assign a port
                else:
                    raise
            
            # Start listening for connections
            self.socket.listen(5)
            
            # Get the actual port if it was auto-assigned
            if self.port == 0:
                self.port = self.socket.getsockname()[1]
                
            logger.info(f"Successfully initialized listening socket on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize socket: {e}")
            self.socket = None
            return False
    
    def _load_history(self) -> Dict:
        """Load message history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading message history: {e}")
        return {}
    
    def _save_history(self):
        """Save message history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.message_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving message history: {e}")
    
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
            data = client_socket.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            # Reset timeout
            client_socket.settimeout(None)
            
            if request['action'] != 'connect':
                logger.warning(f"Invalid connection request from {address}: {request}")
                response = {
                    'status': 'error',
                    'message': 'Invalid connection request'
                }
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
            
            peer_username = request['username']
            logger.info(f"Connection request from peer {peer_username} at {address}")
            
            # Accept connection
            response = {
                'status': 'success',
                'message': 'Connection accepted',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            client_socket.send(json.dumps(response).encode('utf-8'))
            logger.info(f"Connection accepted and response sent to {peer_username}")
            
            # Handle messages from this peer
            while self.running:
                try:
                    logger.info(f"Waiting for message from {peer_username}")
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        logger.info(f"Connection closed by peer {peer_username}")
                        break
                    
                    logger.info(f"Received data from {peer_username}: {data[:100]}...")
                    message_data = json.loads(data)
                    
                    if message_data['action'] != 'message':
                        logger.warning(f"Invalid message from {peer_username}: {message_data}")
                        continue
                    
                    content = message_data['content']
                    timestamp = message_data['timestamp']
                    
                    logger.info(f"Processing message from {peer_username}: {content[:50]}...")
                    
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
                    logger.info(f"Message history saved for {peer_username}")
                    
                    # Notify main process through message queue if available
                    if self.message_queue:
                        logger.info(f"Putting message in queue for main process: {content[:50]}...")
                        self.message_queue.put({
                            'type': 'message',
                            'from': peer_username,
                            'content': content,
                            'timestamp': timestamp
                        })
                        logger.info("Message added to queue successfully")
                    else:
                        logger.warning("Message queue not available, message not forwarded to main process")
                    
                    # Send acknowledgment
                    ack = {
                        'status': 'success',
                        'message': 'Message received',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    client_socket.send(json.dumps(ack).encode('utf-8'))
                    logger.info(f"Acknowledgment sent to {peer_username}")
                    
                    # Print message
                    print(f"\n[{peer_username}] {content}")
                    
                except socket.timeout:
                    logger.info(f"Timeout waiting for message from {peer_username}")
                    continue
                except Exception as e:
                    logger.error(f"Error handling message from {peer_username}: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Error handling incoming connection from {address}: {e}")
        finally:
            try:
                client_socket.close()
                logger.info(f"Connection to {address} closed")
            except:
                pass
    
    def run(self):
        """Override Process.run() to start the listener process"""
        logger.info(f"Starting listener process for {self.username} on {self.host}:{self.port}")
        
        # Initialize socket in the child process
        self._init_socket()
        
        # Use select to handle multiple connections efficiently
        while self.running:
            try:
                # Use select with a timeout to allow checking self.running periodically
                readable, _, _ = select.select([self.socket], [], [], 1.0)
                
                if self.socket in readable:
                    client_socket, address = self.socket.accept()
                    # Handle the connection in a non-blocking way
                    self._handle_incoming_connection(client_socket, address)
            except (socket.error, OSError) as e:
                if self.running:
                    logger.error(f"Socket error in listener process: {e}")
                    # Try to reinitialize the socket
                    try:
                        if self.socket:
                            self.socket.close()
                    except:
                        pass
                    
                    # Wait a bit before trying to reconnect
                    time.sleep(2)
                    
                    try:
                        logger.info("Attempting to reinitialize socket...")
                        self._init_socket()
                        logger.info("Socket reinitialized successfully")
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reinitialize socket: {reconnect_error}")
                        # If we can't reconnect after several attempts, we might need to exit
                        time.sleep(5)  # Wait longer before next attempt
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
                    time.sleep(1)  # Prevent tight loop on persistent errors
    
    def shutdown(self):
        """Shutdown the listener process"""
        logger.info("Shutting down listener process...")
        self.running = False
        
        try:
            if self.socket:
                self.socket.close()
        except Exception as e:
            logger.error(f"Error closing socket: {e}")
        
        logger.info("Listener process shutdown complete")

def main():
    """Main entry point for the listener process"""
    if len(sys.argv) != 5:
        print("Usage: listener_process.py <host> <port> <username> <data_dir>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]
    data_dir = sys.argv[4]
    
    listener = ListenerProcess(host, port, username, data_dir)
    
    try:
        listener.start()
        listener.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        listener.shutdown()

if __name__ == "__main__":
    main() 