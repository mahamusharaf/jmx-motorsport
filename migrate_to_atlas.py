import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Local source (Compass / local MongoDB)
LOCAL_URL  = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME    = os.getenv("DATABASE_NAME", "motorsport_db")

# Atlas destination — read from env var ATLAS_MONGODB_URL, or paste it here:
ATLAS_URL  = os.getenv(
    "ATLAS_MONGODB_URL",
    "PASTE_YOUR_ATLAS_CONNECTION_STRING_HERE"
)
# ────────────────────────────────────────────────────────────────────────────


async def migrate():
    if ATLAS_URL == "PASTE_YOUR_ATLAS_CONNECTION_STRING_HERE":
        print("❌  Please set ATLAS_MONGODB_URL in your .env or paste the string into this script.")
        return

    print(f"🔌  Connecting to LOCAL  → {LOCAL_URL}")
    local_client = AsyncIOMotorClient(LOCAL_URL, serverSelectionTimeoutMS=5000)

    print(f"🔌  Connecting to ATLAS  → {ATLAS_URL[:50]}...")
    atlas_client = AsyncIOMotorClient(ATLAS_URL, serverSelectionTimeoutMS=10000)

    local_db = local_client[DB_NAME]
    atlas_db = atlas_client[DB_NAME]

    # Get all collection names from local db
    collections = await local_db.list_collection_names()
    if not collections:
        print("⚠️  No collections found in local database. Is MongoDB running?")
        return

    print(f"\n📦  Found {len(collections)} collection(s): {', '.join(collections)}\n")

    total_migrated = 0

    for col_name in collections:
        local_col = local_db[col_name]
        atlas_col = atlas_db[col_name]

        # Fetch all documents from local
        docs = await local_col.find({}).to_list(length=100_000)
        count = len(docs)

        if count == 0:
            print(f"   ⏭  '{col_name}' — empty, skipping.")
            continue

        print(f"   ⬆  '{col_name}' — migrating {count} document(s)...")

        # Drop existing collection on Atlas to avoid duplicates
        await atlas_col.drop()

        # Insert all documents
        result = await atlas_col.insert_many(docs)
        print(f"   ✅  '{col_name}' — {len(result.inserted_ids)} document(s) inserted.")
        total_migrated += len(result.inserted_ids)

    print(f"\n🎉  Migration complete! {total_migrated} total document(s) migrated to Atlas.")

    local_client.close()
    atlas_client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
