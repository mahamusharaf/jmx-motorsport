import os
import json
import re

# PATHS
IMAGE_DIR = r"c:\Users\Maha\.gemini\antigravity\scratch\motorsport-brand\src\assets\images\products"
OUTPUT_JSON = r"c:\Users\Maha\.gemini\antigravity\scratch\motorsport-brand\backend\app\data\new_products.json"

def get_category(name):
    name = name.lower()
    if 'suit' in name: return "Leather Suits"
    if 'hoodie' in name: return "Jackets & Hoodies"
    if 'jacket' in name: return "Jackets & Hoodies"
    if 'glove' in name: return "Gloves"
    if 'shoe' in name or 'boot' in name: return "Boots"
    if 'protector' in name: return "Protectors"
    if 'balaclava' in name or 'headwear' in name: return "Headwear"
    if 'baselayer' in name: return "Baselayer"
    if 'bag' in name or 'cap' in name: return "Bags & Accessories"
    return "Accessories"

def get_sku_prefix(category):
    mapping = {
        "Leather Suits": "LS",
        "Jackets & Hoodies": "JH",
        "Gloves": "GL",
        "Boots": "BT",
        "Protectors": "PR",
        "Headwear": "HW",
        "Baselayer": "BL",
        "Bags & Accessories": "BA"
    }
    return mapping.get(category, "AC")

def clean_name(prefix):
    # prefix is already stripped of extension and suffix
    return prefix.replace('-', ' ').title()

def get_color_from_filename(filename):
    # filename is like "black-flower-leather-suit-front.png"
    name_no_ext = re.sub(r'(\.png|\.jpg|\.jpeg)$', '', filename, flags=re.I)
    # Strip common suffixes
    base = re.sub(r'-(front|back|main|oneside|side|inside)$', '', name_no_ext, flags=re.I)
    
    # Try to find color in the beginning
    colors = ["Black", "White", "Red", "Blue", "Green", "Pink", "Yellow", "Orange", "Multicolor", "Grey", "Purple", "Silver", "Neonpink", "Cherryblossam", "Blackgrey", "Whiteblack", "Blackwhite", "Redblack", "Blackred", "Redb", "Ghost", "Bling", "Paint"]
    
    # Sort colors by length descending so Blackwhite matches before Black
    colors.sort(key=len, reverse=True)

    # Special complex colors
    if 'black-flower' in base.lower(): return "Black Flower"
    if 'white-flower' in base.lower(): return "White Flower"
    
    for c in colors:
        if base.lower().startswith(c.lower()):
            return c
    return "Standard"

def img_sort_key(filename):
    f = filename.lower()
    if 'front' in f: return 0
    if 'main' in f: return 1
    if 'side' in f: return 2
    if 'inside' in f: return 4
    if 'back' in f: return 5
    return 3

def rebuild():
    products = []
    
    # 1. SCAN DIRECTORY
    items = sorted(os.listdir(IMAGE_DIR))
    folders = [f for f in items if os.path.isdir(os.path.join(IMAGE_DIR, f))]
    files = [f for f in items if os.path.isfile(os.path.join(IMAGE_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # 2. HANDLE FOLDERS
    for folder in folders:
        folder_path = os.path.join(IMAGE_DIR, folder)
        variant_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))], key=img_sort_key)
        if not variant_files: continue
        
        category = get_category(folder)
        product_name = folder.replace('-', ' ').title()
        
        # Group files into color variants
        colors = {}
        for f in variant_files:
            color = get_color_from_filename(f)
            if color not in colors:
                colors[color] = {"name": color, "images": []}
            colors[color]["images"].append(f"/src/assets/images/products/{folder}/{f}")
            
        variants = list(colors.values())
        
        # PRORITY: Blue first in suits
        if category == "Leather Suits":
            variants.sort(key=lambda v: 0 if v['name'] == "Blue" else 1)

        product = {
            "name": product_name,
            "category": category,
            "description": f"Professional grade JMX {product_name} designed for maximum performance.",
            "features": ["Premium Materials", "Ergonomic Fit", "Reinforced Protection"],
            "variants": variants
        }
        products.append(product)

    # 3. HANDLE STANDALONE FILES (Group correctly)
    standalone_groups = {}
    for f in files:
        if 'size-chart' in f.lower(): continue
        
        # STRIP EXTENSION FIRST
        base_name = re.sub(r'(\.png|\.jpg|\.jpeg)$', '', f, flags=re.I)
        # STRIP SUFFIX
        prefix = re.sub(r'-(front|back|main|oneside|side|inside)$', '', base_name, flags=re.I)
        
        prefix = prefix.lower()
        if prefix not in standalone_groups:
            standalone_groups[prefix] = []
        standalone_groups[prefix].append(f)

    for prefix, group_files in standalone_groups.items():
        category = get_category(prefix)
        product_name = clean_name(prefix)
        group_files = sorted(group_files, key=img_sort_key)
        color = get_color_from_filename(group_files[0])
        
        product = {
            "name": product_name,
            "category": category,
            "description": f"High-performance JMX {product_name} offering superior quality.",
            "features": ["Durable Construction", "Modern Design", "Verified Safety"],
            "variants": [
                {
                    "name": color,
                    "images": [f"/src/assets/images/products/{img}" for img in group_files]
                }
            ]
        }
        products.append(product)

    # 4. ASSIGN SKUS AND FEATURED STATUS
    sku_counts = {}
    # Re-sort for determinism
    products.sort(key=lambda x: (x['category'], x['name']))
    
    for product in products:
        prefix = get_sku_prefix(product['category'])
        sku_counts[prefix] = sku_counts.get(prefix, 0) + 1
        product['sku'] = f"JMX-{prefix}-{sku_counts[prefix]:03d}"
        
        # Default featured
        product['is_featured'] = False
        # Specific featured ones
        if product['sku'] in ["JMX-LS-001", "JMX-JH-001", "JMX-GL-001", "JMX-BT-001"]:
            product['is_featured'] = True
            
        # Generate Slug
        product['slug'] = product['name'].lower().replace(' ', '-').replace("'", "")
            
    # Final cleanup: ensure "Blue" is main if it's there
    for p in products:
        if p['category'] == "Leather Suits":
             # Ensure blue variant is first
             p['variants'].sort(key=lambda v: 0 if v['name'] == "Blue" else 1)

    # Save
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(products, f, indent=2)
    print(f"Rebuilt catalog with {len(products)} products.")

if __name__ == "__main__":
    rebuild()
