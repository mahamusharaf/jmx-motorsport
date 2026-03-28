import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "motorsport_brand")
JSON_FILE = "backend/app/data/new_products.json"

def sync_json_to_db():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["products"]

    # Map for shortening categories to match frontend filters
    CAT_MAP = {
        "Motorcycle Suits": "Suits",
        "Armored Hoodies": "Hoodies",
        "Motorcycle Jackets": "Jackets",
        "Motorcycle Gloves": "Gloves",
        "Motorcycle Boots": "Boots",
        "Motorcycle Balaclavas": "Balaclavas",
        "Motorcycle Bags & Caps": "Accessories",
        "Motorcycle Apparel": "Apparel"
    }

    products = list(collection.find())
    json_data = []

    for p in products:
        # Clean up for JSON
        p_id = str(p["_id"])
        del p["_id"]
        p["id"] = p_id # Add string ID for frontend consistency if needed

        # Correct Category for Frontend
        orig_cat = p.get("category", "")
        if orig_cat in CAT_MAP:
            p["category"] = CAT_MAP[orig_cat]

        json_data.append(p)

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    print(f"✅ Synced {len(json_data)} products to {JSON_FILE} with updated URLs and shortened categories.")
    client.close()

if __name__ == "__main__":
    sync_json_to_db()
