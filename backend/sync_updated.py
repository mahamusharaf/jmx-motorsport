import os
import json
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Cloudinary Config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

DOWNLOADS_PATH = r"c:\Users\Maha\Downloads\products"
# Assuming we run from the project root
DATA_FILE = os.path.join(os.getcwd(), "backend", "app", "data", "new_products.json")

def sync_assets():
    if not os.path.exists(DOWNLOADS_PATH):
        print(f"❌ Error: {DOWNLOADS_PATH} not found!")
        # Try without the 'products' subfolder if not found
        alt_path = r"c:\Users\Maha\Downloads"
        print(f"🔍 Checking alternative path: {alt_path}")
        if os.path.exists(alt_path):
            # We'll just look for specific files in Downloads if the products folder isn't there
            pass
        else:
            return

    print(f"🚀 Scanning {DOWNLOADS_PATH}...")
    files = os.listdir(DOWNLOADS_PATH)
    
    # Map for size charts
    size_charts = {}
    
    # Final product mapping
    slug_to_images = {}
    
    # slugs mapping
    mapping = {
        "pink-hoodie": "armored-motorcycle-riding-hoodie",
        "pink-suit": "stealth-pro-race-suit-pink",
        "black-suit": "adventure-pro-suit-black",
        "redb-suit": "racing-leather-suit-pro-1pc",
        "white-shoe": "pro-race-boots-white-black",
        "black-shoe": "pro-race-boots-black",
        "pink-balaclava": "pink-performance-balaclava",
        "whiteblack-gloves": "pro-racing-gloves-white-black",
        "black-gloves": "pro-racing-gloves-black",
        "black-cap": "jmx-racing-logo-cap-black",
        "multicolor-caps": "jmx-multi-color-racing-caps"
    }

    # 1. Identify size charts and map images to slugs
    for filename in files:
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
            
        full_path = os.path.join(DOWNLOADS_PATH, filename)
        
        # Detect Size Charts
        if "size-chart" in filename.lower():
            if "suit" in filename.lower():
                print(f"📈 Found Suit Size Chart: {filename}")
                res = cloudinary.uploader.upload(full_path, folder="size_charts", public_id="suit_chart")
                size_charts["Suits"] = res["secure_url"]
            elif "glove" in filename.lower():
                print(f"📈 Found Glove Size Chart: {filename}")
                res = cloudinary.uploader.upload(full_path, folder="size_charts", public_id="glove_chart")
                size_charts["Gloves"] = res["secure_url"]
            elif "shoe" in filename.lower() or "boot" in filename.lower():
                print(f"📈 Found Shoe Size Chart: {filename}")
                res = cloudinary.uploader.upload(full_path, folder="size_charts", public_id="shoes_chart")
                size_charts["Boots"] = res["secure_url"]
            continue

        matched = False
        for key, val in mapping.items():
            if key in filename:
                if val not in slug_to_images:
                    slug_to_images[val] = []
                
                # Upload and store
                print(f"📤 Uploading {filename} for {val}...")
                public_id = filename.split('.')[0]
                res = cloudinary.uploader.upload(full_path, folder="products", public_id=public_id, overwrite=True)
                slug_to_images[val].append(res["secure_url"])
                matched = True
                break

    # 2. Update JSON
    print(f"📝 Updating {DATA_FILE}...")
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found!")
        return
        
    with open(DATA_FILE, 'r') as f:
        products = json.load(f)
        
    updated_count = 0
    for product in products:
        slug = product.get("slug")
        category = product.get("category")
        
        # Update images if we found new ones
        if slug in slug_to_images:
            # Custom sort: prioritize 'front' or 'main'
            imgs = slug_to_images[slug]
            imgs.sort(key=lambda x: (
                0 if "front" in x.lower() or "main" in x.lower() else 
                1 if "side" in x.lower() else 
                2 if "back" in x.lower() else 3,
                x.lower()
            ))
            product["images"] = imgs
            updated_count += 1
            
        # Add size chart if category matches
        if category in size_charts:
            product["size_chart"] = size_charts[category]
            print(f"✅ Added {category} size chart to {product['name']}")

    with open(DATA_FILE, 'w') as f:
        json.dump(products, f, indent=2)
        
    print(f"✨ Success! Updated {updated_count} products and added size charts.")

if __name__ == "__main__":
    sync_assets()
