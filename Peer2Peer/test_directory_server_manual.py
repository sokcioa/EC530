#!/usr/bin/env python3
import socket
import json
import sys
import os
import time
import threading
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectoryServerClient:
    """Client for interacting with the Directory Server"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
    
    def send_request(self, request):
        """Send a request to the directory server and return the response"""
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.host, self.port))
            client_socket.send(json.dumps(request).encode('utf-8'))
            response_data = client_socket.recv(4096).decode('utf-8')
            return json.loads(response_data)
        finally:
            client_socket.close()
    
    def register_user(self, username, ip, port, profile=None):
        """Register a user with the directory server"""
        if profile is None:
            profile = {}
            
        request = {
            'action': 'register',
            'username': username,
            'ip': ip,
            'port': port,
            'profile': profile
        }
        
        return self.send_request(request)
    
    def query_users(self, query_type='all', search_term=''):
        """Query users from the directory server"""
        request = {
            'action': 'query',
            'query_type': query_type,
            'search_term': search_term
        }
        
        return self.send_request(request)
    
    def print_users(self, users):
        """Print user information in a readable format"""
        if not users:
            print("No users found.")
            return
            
        print(f"Found {len(users)} users:")
        print("-" * 50)
        for i, user in enumerate(users, 1):
            print(f"{i}. IP: {user['ip']}:{user['port']}")
            if 'profile' in user and user['profile']:
                print(f"   Profile: {user['profile']}")
            print()

def interactive_menu():
    """Display an interactive menu for testing the directory server"""
    parser = argparse.ArgumentParser(description='Interactive Directory Server Test Client')
    parser.add_argument('--host', default='127.0.0.1', help='Directory server host')
    parser.add_argument('--port', type=int, default=5000, help='Directory server port')
    
    args = parser.parse_args()
    
    client = DirectoryServerClient(args.host, args.port)
    
    print("Directory Server Test Client")
    print("============================")
    
    while True:
        print("\nOptions:")
        print("1. Register a user")
        print("2. Query all users")
        print("3. Query users by name")
        print("4. Query users by IP")
        print("5. Search users")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            username = input("Enter username: ")
            ip = input("Enter IP address: ")
            port = int(input("Enter port: "))
            status = input("Enter status (optional): ")
            bio = input("Enter bio (optional): ")
            
            profile = {}
            if status:
                profile['status'] = status
            if bio:
                profile['bio'] = bio
                
            response = client.register_user(username, ip, port, profile)
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
        elif choice == '2':
            response = client.query_users()
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            if response['status'] == 'success':
                client.print_users(response['users'])
                
        elif choice == '3':
            search_term = input("Enter name to search for: ")
            response = client.query_users('name', search_term)
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            if response['status'] == 'success':
                client.print_users(response['users'])
                
        elif choice == '4':
            search_term = input("Enter IP to search for: ")
            response = client.query_users('ip', search_term)
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            if response['status'] == 'success':
                client.print_users(response['users'])
                
        elif choice == '5':
            search_term = input("Enter search term: ")
            response = client.query_users('search', search_term)
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            if response['status'] == 'success':
                client.print_users(response['users'])
                
        elif choice == '6':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please try again.")

def main():
    """Main entry point for the manual test client"""
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 