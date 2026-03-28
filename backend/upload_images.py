# upload_images.py
print("🚀 Starting upload script...")
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

images_folder = "src/assets/images/products"
print(f"📂 Checking folder: {images_folder}")
if not os.path.exists(images_folder):
    print(f"❌ Error: {images_folder} not found!")
else:
    print(f"✅ Folder found with {len(os.listdir(images_folder))} files.")

for filename in os.listdir(images_folder):
    if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        filepath = os.path.join(images_folder, filename)
        result = cloudinary.uploader.upload(filepath, folder="products")
        print(f"{filename} → {result['secure_url']}")