"""
upload_to_cloudinary.py
-----------------------
Uploads ALL product images (recursively) from src/assets/images/products/
to Cloudinary, then updates every matching image URL in the Atlas MongoDB.

Usage:
    .venv\\Scripts\\python.exe upload_to_cloudinary.py
"""

import os
import json
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ───────────────────────────────────────────────────────────────────
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

ATLAS_URL    = os.getenv("ATLAS_MONGODB_URL", "mongodb://localhost:27017")
DB_NAME      = os.getenv("DATABASE_NAME", "motorsport_db")
IMAGES_ROOT  = "src/assets/images/products"
CLOUDINARY_FOLDER = "jmx/products"
# ─────────────────────────────────────────────────────────────────────────────

def collect_images(root_folder):
    """Walk the folder recursively; return list of (abs_path, rel_path, public_id)."""
    items = []
    for dirpath, _, filenames in os.walk(root_folder):
        for fname in filenames:
            if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                abs_path = os.path.join(dirpath, fname)
                # relative path from project root, forward-slash
                rel_path = os.path.relpath(abs_path, ".").replace("\\", "/")
                # public_id preserves subfolder structure inside Cloudinary folder
                sub = os.path.relpath(dirpath, root_folder).replace("\\", "/")
                name_no_ext = os.path.splitext(fname)[0]
                public_id = f"{name_no_ext}" if sub == "." else f"{sub}/{name_no_ext}"
                items.append((abs_path, rel_path, public_id))
    return items


def upload_images(items):
    """Upload images to Cloudinary; return {rel_path: secure_url}."""
    url_map = {}
    total = len(items)
    for i, (abs_path, rel_path, public_id) in enumerate(items, 1):
        print(f"[{i}/{total}] Uploading {rel_path} ...")
        try:
            result = cloudinary.uploader.upload(
                abs_path,
                folder=CLOUDINARY_FOLDER,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            secure_url = result["secure_url"]
            url_map[rel_path] = secure_url
            print(f"  OK  -> {secure_url}")
        except Exception as e:
            print(f"  FAIL -> {e}")
    return url_map


def update_mongo(url_map):
    """Replace every local image path in Atlas with its Cloudinary URL."""
    client = MongoClient(ATLAS_URL, serverSelectionTimeoutMS=10000)
    db = client[DB_NAME]
    collection = db["products"]

    products = list(collection.find())
    print(f"\nUpdating {len(products)} product(s) in Atlas ...")

    updated_count = 0
    for product in products:
        changed = False

        # Top-level images array
        if "images" in product:
            new_imgs = []
            for img in product["images"]:
                mapped = url_map.get(img, img)
                new_imgs.append(mapped)
                if mapped != img:
                    changed = True
            product["images"] = new_imgs

        # Variants -> images
        if "variants" in product:
            for variant in product["variants"]:
                if "images" in variant:
                    new_imgs = []
                    for img in variant["images"]:
                        mapped = url_map.get(img, img)
                        new_imgs.append(mapped)
                        if mapped != img:
                            changed = True
                    variant["images"] = new_imgs

        if changed:
            collection.replace_one({"_id": product["_id"]}, product)
            print(f"  Updated: {product.get('name', product['_id'])}")
            updated_count += 1

    print(f"\nDone. {updated_count}/{len(products)} product(s) updated in Atlas.")
    client.close()


def main():
    print(f"Scanning {IMAGES_ROOT} ...")
    items = collect_images(IMAGES_ROOT)
    if not items:
        print("No images found. Exiting.")
        return
    print(f"Found {len(items)} image(s).\n")

    url_map = upload_images(items)
    print(f"\nUploaded {len(url_map)}/{len(items)} image(s) successfully.")

    update_mongo(url_map)
    print("\nAll done!")


if __name__ == "__main__":
    main()
