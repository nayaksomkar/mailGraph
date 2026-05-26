# Async MongoDB connection using Motor

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Singleton client connected to the mailgraph database
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client.mailgraph

def get_db():
    return db
