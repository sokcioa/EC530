
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
