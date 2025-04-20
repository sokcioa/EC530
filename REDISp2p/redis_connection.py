from redis.asyncio import Redis

# Create a shared Redis instance
redis = Redis(host='localhost', port=6379, decode_responses=True) 