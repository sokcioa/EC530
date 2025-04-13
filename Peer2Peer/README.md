# Peer-to-Peer Communication System

A decentralized messaging system that enables direct peer-to-peer communication between users, with a central server only handling user discovery and IP address management.

## Project Overview

This project implements a peer-to-peer communication system using IPv4 sockets and threading. The system is designed to be decentralized, with message data stored locally on each peer's machine. A central server is used only for user discovery and IP address management.

## Technical Stack

- Programming Language: Python
- Network Protocol: IPv4
- Communication: Socket-based TCP/IP
- Threading: Python's threading module
- Data Storage: Local file system

## Project Phases

### Phase 1: Basic Peer-to-Peer Chat System
- Implement basic socket communication between peers
- Create a simple user interface for sending/receiving messages
- Establish direct peer-to-peer connections
- Implement basic message handling and display
- Set up local message storage
- Basic error handling and connection management

### Phase 2: API-based Messaging System
- Design and implement a RESTful API for message handling
- Create message queuing system
- Implement message delivery confirmation
- Add support for offline message storage
- Implement message history and search functionality
- Add basic user profiles and status updates

### Phase 3: Special Messages for Subscribers
- Implement subscription-based messaging features
- Add support for group messages
- Create broadcast message functionality
- Implement message categories and tags
- Add support for rich text formatting
- Implement message priority levels

### Phase 4: Security & Enhancements
- Implement end-to-end encryption
- Add user authentication and authorization
- Implement message signing and verification
- Add support for file sharing
- Implement rate limiting and spam protection
- Add network resilience features
- Implement connection recovery mechanisms

## Architecture

### Components
1. **Central Server**
   - User registration and discovery
   - IP address management
   - Online status tracking
   - User directory service

2. **Peer Client**
   - Direct peer-to-peer communication
   - Local message storage
   - Message encryption/decryption
   - User interface
   - Connection management

### Network Flow
1. User connects to central server for registration
2. Server maintains list of active users and their IP addresses
3. Peers establish direct connections for messaging
4. All message data is transmitted directly between peers
5. Central server is only contacted for user discovery and status updates

## Getting Started

### Running the Directory Server

To start the directory server:

```bash
python directory_server.py
```

The server will start on the default port 5000. You can modify the host and port in the code if needed.

### Testing the Directory Server

We provide several tools for testing the directory server:

#### Automated Tests

The test suite can run against an existing directory server or start its own server for testing.

To run tests against an existing server (default behavior):

```bash
# Make sure the directory server is running first
python directory_server.py

# In another terminal, run the tests
python run_tests.py
```

To specify a different host or port:

```bash
python run_tests.py --host 127.0.0.1 --port 5000
```

To start a new server for testing (instead of using an existing one):

```bash
python run_tests.py --start-server
```

For verbose output:

```bash
python run_tests.py --verbose
```

To run a specific test file:

```bash
python run_tests.py --test test_directory_server.py
```

#### Manual Testing

For interactive testing of the directory server:

```bash
python test_directory_server_manual.py
```

This provides a menu-driven interface to:
- Register users
- Query all users
- Query users by name
- Query users by IP
- Search users

You can specify a different host or port:

```bash
python test_directory_server_manual.py --host 127.0.0.1 --port 5000
```

## Security Considerations

- End-to-end encryption for all messages
- Secure user authentication
- Protection against common network attacks
- Data privacy and local storage security
- Rate limiting and spam protection

## Future Enhancements

- Voice and video communication
- Cross-platform support
- Mobile applications
- Advanced file sharing capabilities
- Message backup and sync features
