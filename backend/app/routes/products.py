"""
Product catalog API routes — backed by MongoDB.
Provides endpoints for browsing, searching, and managing products.
"""

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from app.database import get_products_collection
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    CategoryResponse,
)

router = APIRouter(prefix="/api/products", tags=["Products"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _doc_to_response(doc: dict) -> dict:
    """Convert a MongoDB document to an API-friendly dict (ObjectId → str)."""
    doc["id"] = str(doc.pop("_id"))
    
    # Backward compatibility for cached frontends or old data
    variants = doc.get("variants", [])
    if variants:
        # Populate color_variants so older JS code can read it
        doc["color_variants"] = [
            {"color": v.get("name", "Standard"), "images": v.get("images", [])}
            for v in variants
        ]
        # Ensure root images has the first image or images so old code doesn't crash on p.images[0]
        if not doc.get("images"):
            doc["images"] = variants[0].get("images", [])
            
    return doc


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[ProductResponse])
async def list_products(
    category: str | None = Query(None, description="Filter by category name"),
    subcategory: str | None = Query(None, description="Filter by subcategory name"),
    featured: bool | None = Query(None, description="Filter featured products only"),
    search: str | None = Query(None, description="Search product names & descriptions"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Return a paginated, filterable list of products."""
    collection = get_products_collection()
    query: dict = {}

    if category:
        query["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if subcategory:
        query["subcategory"] = {"$regex": f"^{subcategory}$", "$options": "i"}
    if featured is not None:
        query["is_featured"] = featured
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    cursor = collection.find(query).skip(skip).limit(limit)
    products = []
    async for doc in cursor:
        products.append(_doc_to_response(doc))
    return products


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories():
    """Return all categories with their subcategories and product counts."""
    collection = get_products_collection()
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "subcategories": {"$addToSet": "$subcategory"},
                "product_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    categories = []
    async for doc in collection.aggregate(pipeline):
        categories.append(
            CategoryResponse(
                name=doc["_id"],
                slug=doc["_id"].lower().replace(" ", "-"),
                subcategories=sorted(doc["subcategories"]),
                product_count=doc["product_count"],
            )
        )
    return categories


@router.get("/featured", response_model=list[ProductResponse])
async def list_featured():
    """Return only featured/hero products."""
    collection = get_products_collection()
    products = []
    async for doc in collection.find({"is_featured": True}):
        products.append(_doc_to_response(doc))
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a single product by its MongoDB ObjectId."""
    collection = get_products_collection()
    try:
        doc = await collection.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return _doc_to_response(doc)


# ---------------------------------------------------------------------------
# POST / PUT / DELETE endpoints
# ---------------------------------------------------------------------------
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """Add a new product to the catalog."""
    collection = get_products_collection()
    doc = product.model_dump()
    result = await collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, updates: ProductUpdate):
    """Update an existing product."""
    collection = get_products_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await collection.find_one_and_update(
        {"_id": oid},
        {"$set": update_data},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return _doc_to_response(result)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str):
    """Remove a product from the catalog."""
    collection = get_products_collection()
    try:
        oid = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID format")

    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
