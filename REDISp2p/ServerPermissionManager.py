from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis_connection import redis

class UserPermission(BaseModel):
    user_id: str

def create_permission_router(topic_id: str) -> APIRouter:
    router = APIRouter()
    pub_key = f"topic:{topic_id}:publishers"
    sub_key = f"topic:{topic_id}:subscribers"

    @router.post("/permissions/publishers/add")
    async def add_publisher(permission: UserPermission):
        await redis.sadd(pub_key, permission.user_id)
        return {"status": "publisher added", "user_id": permission.user_id}

    @router.post("/permissions/publishers/remove")
    async def remove_publisher(permission: UserPermission):
        await redis.srem(pub_key, permission.user_id)
        return {"status": "publisher removed", "user_id": permission.user_id}

    @router.post("/permissions/subscribers/add")
    async def add_subscriber(permission: UserPermission):
        await redis.sadd(sub_key, permission.user_id)
        return {"status": "subscriber added", "user_id": permission.user_id}

    @router.post("/permissions/subscribers/remove")
    async def remove_subscriber(permission: UserPermission):
        await redis.srem(sub_key, permission.user_id)
        return {"status": "subscriber removed", "user_id": permission.user_id}

    @router.get("/permissions")
    async def list_permissions():
        publishers = await redis.smembers(pub_key)
        subscribers = await redis.smembers(sub_key)
        return {
            "publishers": list(publishers),
            "subscribers": list(subscribers),
        }

    return router
