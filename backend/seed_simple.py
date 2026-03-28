import json
from pathlib import Path
from pymongo import MongoClient

# Configuration
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "motorsport_brand"
SEED_FILE = Path(__file__).parent / "app" / "data" / "new_products.json"

def seed():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db["products"]

        # Clear existing data
        collection.drop()
        print("🗑️ Dropped existing products.")

        # Load new data
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)

        # Remove local 'id' for Mongo _id
        for p in products:
            p.pop("id", None)

        result = collection.insert_many(products)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} products!")

        client.close()
    except Exception as e:
        print(f"❌ Error seeding: {e}")

if __name__ == "__main__":
    seed()
