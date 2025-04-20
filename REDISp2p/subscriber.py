#!/usr/bin/env python3
import asyncio
import json
import sys
import argparse
import signal
from redis_connection import redis

async def subscribe_to_topic(topic, user_id="demo_user"):
    """Subscribe to a topic and print received messages"""
    # First, ensure the user has permission to subscribe
    sub_key = f"topic:{topic}:subscribers"
    await redis.sadd(sub_key, user_id)
    
    # Create a pubsub instance
    pubsub = redis.pubsub()
    await pubsub.subscribe(topic)
    
    print(f"✅ Subscribed to topic '{topic}'")
    print("Waiting for messages... (Press Ctrl+C to exit)")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                try:
                    data = json.loads(message['data'])
                    print(f"\n📨 New message in '{topic}':")
                    print(f"   From: {data.get('user', 'unknown')}")
                    print(f"   Content: {data.get('content', '')}")
                    print(f"   Time: {data.get('timestamp', '')}")
                except json.JSONDecodeError:
                    print(f"\n📨 Raw message: {message['data']}")
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print("\nUnsubscribing...")
    finally:
        await pubsub.unsubscribe(topic)
        await pubsub.close()

async def main():
    parser = argparse.ArgumentParser(description="Subscribe to a topic and receive messages")
    parser.add_argument("topic", help="Topic to subscribe to")
    parser.add_argument("--user", default="demo_user", help="User ID (default: demo_user)")
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful shutdown
    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    
    def signal_handler():
        stop.set_result(None)
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await asyncio.wait_for(subscribe_to_topic(args.topic, args.user), timeout=None)
    except asyncio.TimeoutError:
        pass
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)

if __name__ == "__main__":
    asyncio.run(main()) 