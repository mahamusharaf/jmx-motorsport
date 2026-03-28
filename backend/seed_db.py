"""
Seed script — populates MongoDB with sample product data.

Run once:
    cd backend
    python seed_db.py
"""

import asyncio
import json
import os
from pathlib import Path
# from dotenv import load_dotenv  # Temporarily disabled to bypass environment issues
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
# load_dotenv()

MONGO_URI = "mongodb://localhost:27017" # os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = "motorsport_db" # os.getenv("DATABASE_NAME", "motorsport_db")
SEED_FILE = Path(__file__).parent / "app" / "data" / "new_products.json"


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["products"]

    # Check if products already exist
    count = await collection.count_documents({})
    if count > 0:
        print(f"⚠️  Database already has {count} products. Dropping and re-seeding...")
        await collection.drop()

    # Load seed data
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Remove the "id" field — MongoDB will generate its own _id
    for p in products:
        p.pop("id", None)

    result = await collection.insert_many(products)
    print(f"✅ Inserted {len(result.inserted_ids)} products into '{DATABASE_NAME}.products'")

    # Create useful indexes
    await collection.create_index("category")
    await collection.create_index("subcategory")
    await collection.create_index("slug", unique=True)
    await collection.create_index("is_featured")
    await collection.create_index([("name", "text"), ("description", "text")])
    print("📇 Created indexes on: category, subcategory, slug, is_featured, text(name+description)")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
