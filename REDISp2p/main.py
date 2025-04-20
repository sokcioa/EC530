from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socket
import sys
from TopicServer import create_topic_server
from ServerPermissionManager import create_permission_router

# Create the FastAPI app
app = FastAPI(
    title="P2P Chat Application",
    description="A P2P chat application using Redis for pub/sub messaging"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define available topics
TOPICS = ["general", "tech", "random"]

# Create and mount routers for each topic
for topic in TOPICS:
    topic_router = create_topic_server(topic)
    permission_router = create_permission_router(topic)
    app.include_router(topic_router, prefix=f"/topics/{topic}")
    app.include_router(permission_router, prefix=f"/topics/{topic}")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the P2P Chat Application",
        "topics": TOPICS
    }

@app.get("/topics")
async def list_topics():
    return {"topics": TOPICS}

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

if __name__ == "__main__":
    try:
        # Try to find an available port
        port = find_available_port()
        print(f"Starting server on port {port}")
        
        # Run the FastAPI app
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True
        )
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        sys.exit(1) 