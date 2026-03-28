import os
import json
import time
import hmac
import hashlib
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "motorsport_brand")

def get_signature(params, secret):
    # Sort params alphabetically
    sorted_params = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    return hashlib.sha1((sorted_params + secret).encode('utf-8')).hexdigest()

def upload_and_update():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["products"]

    images_folder = "src/assets/images/products"
    if not os.path.exists(images_folder):
        print(f"❌ Folder {images_folder} not found.")
        return

    print(f"🚀 Starting direct Cloudinary upload (via requests)...")
    url_map = {}

    for filename in os.listdir(images_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            filepath = os.path.join(images_folder, filename)
            try:
                print(f"📤 Uploading {filename}...")
                timestamp = int(time.time())
                public_id = os.path.splitext(filename)[0]
                
                params = {
                    "public_id": public_id,
                    "timestamp": timestamp,
                    "folder": "products"
                }
                
                signature = get_signature(params, API_SECRET)
                
                files = {"file": open(filepath, "rb")}
                data = {
                    "api_key": API_KEY,
                    "timestamp": timestamp,
                    "public_id": public_id,
                    "signature": signature,
                    "folder": "products"
                }
                
                response = requests.post(
                    f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    secure_url = response.json()['secure_url']
                    url_map[filename] = secure_url
                    print(f"✅ {filename} → {secure_url}")
                else:
                    print(f"❌ Failed {filename}: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error uploading {filename}: {e}")

    # Update MongoDB
    print("\n🔄 Updating MongoDB...")
    for product in collection.find():
        new_images = []
        updated = False
        for img_path in product.get("images", []):
            fname = os.path.basename(img_path)
            if fname in url_map:
                new_images.append(url_map[fname])
                updated = True
            else:
                new_images.append(img_path)
        
        if updated:
            collection.update_one({"_id": product["_id"]}, {"$set": {"images": new_images}})
            print(f"✅ Updated {product['name']}")

    print("\n✨ Done!")
    client.close()

if __name__ == "__main__":
    upload_and_update()
