"""
MongoDB connection and collection helpers.
Uses Motor (async MongoDB driver) for non-blocking operations with FastAPI.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "motorsport_db")

client: AsyncIOMotorClient | None = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    print(f"✅ Connected to MongoDB → {DATABASE_NAME}")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")


def get_database():
    return db


def get_products_collection():
    return db["products"]