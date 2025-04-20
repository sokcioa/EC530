# Redis P2P Chat Application

A peer-to-peer chat application using Redis for message brokering and FastAPI for the backend.

## Features

- Create and manage chat topics
- Subscribe to topics
- Publish messages to topics
- Real-time message delivery
- User profiles with persistent subscriptions
- Terminal-based interface
- GUI interface for easy interaction

## Prerequisites

- Python 3.9 or higher
- Redis server
- Docker (optional, for containerized deployment)

## Installation

### Option 1: Local Installation

1. Install Redis:
   ```bash
   # On macOS
   brew install redis
   
   # On Ubuntu/Debian
   sudo apt-get install redis-server
   ```

2. Create and activate a conda environment:
   ```bash
   conda create -n redisp2p python=3.9
   conda activate redisp2p
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Docker Container

1. Build the Docker image:
   ```bash
   docker build -t redis-p2p-chat .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -p 6379:6379 redis-p2p-chat
   ```

## Running the Application

### Local Execution

1. Start the server:
   ```bash
   ./start_chat.sh
   ```

2. Run the terminal chat client:
   ```bash
   python terminal_chat.py
   ```

### Docker Execution

The application will automatically start when you run the container. You can access:
- FastAPI server at `http://localhost:8000`
- Redis server at `localhost:6379`

## Using the Terminal Interface

1. When you first run the application, you'll be prompted to:
   - Create a new profile, or
   - Select an existing profile

2. Main menu options:
   - Create Topic: Create a new chat topic
   - Subscribe to Topic: Join an existing topic
   - Publish to Topic: Send a message to a topic
   - See Topics: View messages in subscribed topics
   - Unsubscribe from Topic: Leave a topic
   - Exit: Save profile and quit

3. Features:
   - New messages are highlighted in yellow
   - Your messages are shown in cyan
   - Topic list shows number of new messages
   - Profiles are automatically saved on exit

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test script to verify the functionality:
```bash
python TestTopicServer.py
```

## Project Structure

- `main.py`: FastAPI application entry point
- `TopicServer.py`: Topic server implementation
- `ServerPermissionManager.py`: User permission management
- `redis_connection.py`: Redis connection handling
- `terminal_chat.py`: Terminal-based chat interface
- `chat_gui.py`: GUI-based chat interface
- `start_chat.sh`: Startup script
- `requirements.txt`: Python dependencies
- `profiles/`: Directory for user profiles 