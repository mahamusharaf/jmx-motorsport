import os
import json
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from ROOT
load_dotenv()

# Cloudinary Config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# MongoDB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "motorsport_db")

def upload_and_update():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db["products"]

    images_folder = "src/assets/images/products"
    
    if not os.path.exists(images_folder):
        print(f"❌ Folder {images_folder} not found.")
        return

    print(f"🚀 Starting Cloudinary upload and DB update...")
    
    # We'll map filenames/paths to secure URLs
    url_map = {}

    # Recursive scan
    for root, dirs, files in os.walk(images_folder):
        for filename in files:
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                filepath = os.path.join(root, filename)
                # Key for map should be the path relative to the project root, 
                # or just the path as it appears in the JSON (e.g. src/assets/images/products/...)
                rel_path = os.path.relpath(filepath, ".").replace("\\", "/")
                
                try:
                    print(f"📤 Uploading {rel_path}...")
                    # Public ID based on filename
                    public_id = os.path.splitext(filename)[0]
                    result = cloudinary.uploader.upload(filepath, folder="products", public_id=public_id)
                    secure_url = result['secure_url']
                    url_map[rel_path] = secure_url
                    print(f"✅ {rel_path} → {secure_url}")
                except Exception as e:
                    print(f"❌ Failed to upload {rel_path}: {e}")

    # Now update the database
    print("\n🔄 Updating MongoDB with new Cloudinary URLs...")
    products = list(collection.find())
    
    for product in products:
        updated = False
        if "variants" in product:
            for variant in product["variants"]:
                new_images = []
                for img_path in variant.get("images", []):
                    # Check if the path is in our map
                    if img_path in url_map:
                        new_images.append(url_map[img_path])
                        updated = True
                    else:
                        new_images.append(img_path)
                variant["images"] = new_images
        
        if updated:
            collection.replace_one({"_id": product["_id"]}, product)
            print(f"✅ Updated {product['name']}")

    print("\n✨ All done!")
    client.close()

if __name__ == "__main__":
    upload_and_update()
