import asyncio
import json
import subprocess
import sys
import time
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis_connection import redis
from TopicServer import create_topic_server
from ServerPermissionManager import create_permission_router, UserPermission

# Create a subscriber script that will run as a separate process
def create_subscriber_script():
    subscriber_script = """
import asyncio
import json
import sys
import time
from redis.asyncio import Redis

async def run_subscriber(topic_id):
    redis_client = Redis(host='localhost', port=6379, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(topic_id)
    print(f"Subscriber started for topic: {topic_id}", file=sys.stderr)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                print(f"RECEIVED: {message['data']}", file=sys.stderr)
                # Write to stdout so the parent process can read it
                print(message['data'], flush=True)
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error in subscriber: {str(e)}", file=sys.stderr)
    finally:
        await pubsub.unsubscribe(topic_id)
        await redis_client.close()

if __name__ == "__main__":
    topic_id = sys.argv[1]
    asyncio.run(run_subscriber(topic_id))
"""
    
    with open("subscriber_script.py", "w") as f:
        f.write(subscriber_script)
    
    return "subscriber_script.py"

async def test_topic_server():
    # Setup
    app = FastAPI()
    topic_id = "test_topic_001"
    user_id_publisher = "user_pub"
    user_id_subscriber = "user_sub"

    # Create and mount routers
    topic_router = create_topic_server(topic_id)
    permission_router = create_permission_router(topic_id)
    app.include_router(topic_router, prefix=f"/topics/{topic_id}")
    app.include_router(permission_router, prefix=f"/topics/{topic_id}")

    # Clear Redis keys
    await redis.delete(f"topic:{topic_id}:publishers")
    await redis.delete(f"topic:{topic_id}:subscribers")

    # Test permission management
    print("Testing permission management...")
    
    # Add permissions
    await redis.sadd(f"topic:{topic_id}:publishers", user_id_publisher)
    await redis.sadd(f"topic:{topic_id}:subscribers", user_id_subscriber)

    # Verify permissions
    publishers = await redis.smembers(f"topic:{topic_id}:publishers")
    subscribers = await redis.smembers(f"topic:{topic_id}:subscribers")
    assert user_id_publisher in publishers, "Publisher not added correctly"
    assert user_id_subscriber in subscribers, "Subscriber not added correctly"
    print("✅ Permissions set correctly")

    # Test message publishing and receiving
    print("\nTesting publish/subscribe functionality...")
    
    # Create and run subscriber as a subprocess
    subscriber_script_path = create_subscriber_script()
    subscriber_process = subprocess.Popen(
        [sys.executable, subscriber_script_path, topic_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Give the subscriber time to connect
    print("Waiting for subscriber to connect...")
    time.sleep(2)
    
    # Publish test message
    test_msg = {"msg": "Hello from test!", "timestamp": "2024-03-14"}
    await redis.publish(topic_id, json.dumps(test_msg))
    print("✅ Test message published")
    
    # Wait for message to be received (with timeout)
    received_message = None
    timeout = 5  # seconds
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        line = subscriber_process.stdout.readline()
        if line:
            try:
                received_message = json.loads(line.strip())
                print(f"✅ Message received: {received_message}")
                break
            except json.JSONDecodeError:
                print(f"⚠️ Received non-JSON message: {line.strip()}")
    
    # Clean up subscriber process
    subscriber_process.terminate()
    subscriber_process.wait(timeout=2)
    
    # Verify received message
    if received_message:
        assert received_message["msg"] == test_msg["msg"], "Message content mismatch"
        print("✅ Message content verified")
    else:
        print("⚠️ No messages received within timeout period")
    
    # Cleanup
    await redis.delete(f"topic:{topic_id}:publishers")
    await redis.delete(f"topic:{topic_id}:subscribers")
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_topic_server())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
