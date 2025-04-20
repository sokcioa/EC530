#!/usr/bin/env python3
import asyncio
import json
import sys
import argparse
import requests
from redis_connection import redis

async def publish_message(topic, message, user_id="demo_user"):
    """Publish a message to a topic"""
    # First, ensure the user has permission to publish
    pub_key = f"topic:{topic}:publishers"
    await redis.sadd(pub_key, user_id)
    
    # Publish the message
    await redis.publish(topic, json.dumps(message))
    print(f"✅ Message published to topic '{topic}': {message}")

async def main():
    parser = argparse.ArgumentParser(description="Publish messages to a topic")
    parser.add_argument("topic", help="Topic to publish to")
    parser.add_argument("message", nargs="+", help="Message to publish (can be multiple words)")
    parser.add_argument("--user", default="demo_user", help="User ID (default: demo_user)")
    
    args = parser.parse_args()
    
    # Join the message words into a single string
    message_text = " ".join(args.message)
    
    # Create a simple message
    message = {
        "content": message_text,
        "user": args.user,
        "timestamp": "now"
    }
    
    await publish_message(args.topic, message, args.user)

if __name__ == "__main__":
    asyncio.run(main()) 