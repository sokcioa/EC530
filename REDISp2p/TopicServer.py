from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Set, Dict
import asyncio
import json
from redis_connection import redis

# In-memory tracking of WebSocket connections per topic
topic_connections: Dict[str, Set[WebSocket]] = {}

# Dependency to simulate getting the current user ID (replace with auth later)
async def get_current_user_id():
    # Simulate user auth (replace with real logic)
    return "user_123"

def create_topic_server(topic_id: str) -> APIRouter:
    router = APIRouter()
    topic_key_pub = f"topic:{topic_id}:publishers"
    topic_key_sub = f"topic:{topic_id}:subscribers"

    if topic_id not in topic_connections:
        topic_connections[topic_id] = set()

    @router.post("/publish")
    async def publish_message(message: dict, user_id: str = Depends(get_current_user_id)):
        if not await redis.sismember(topic_key_pub, user_id):
            raise HTTPException(status_code=403, detail="User not allowed to publish")

        # Convert message to JSON string for consistency
        await redis.publish(topic_id, json.dumps(message))
        return {"status": "message published", "message": message}

    @router.websocket("/subscribe")
    async def subscribe(websocket: WebSocket, user_id: str = Depends(get_current_user_id)):
        await websocket.accept()

        if not await redis.sismember(topic_key_sub, user_id):
            await websocket.close(code=1008)
            return

        topic_connections[topic_id].add(websocket)
        pubsub = redis.pubsub()
        await pubsub.subscribe(topic_id)

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
                if message:
                    # Parse the JSON message before sending
                    try:
                        parsed_message = json.loads(message['data'])
                        await websocket.send_json(parsed_message)
                    except json.JSONDecodeError:
                        await websocket.send_text(message['data'])
                await asyncio.sleep(0.01)
        except WebSocketDisconnect:
            print(f"WebSocket disconnected for user {user_id}")
        except Exception as e:
            print(f"Error in WebSocket connection: {str(e)}")
        finally:
            topic_connections[topic_id].remove(websocket)
            await pubsub.unsubscribe(topic_id)
            await websocket.close()

    return router
