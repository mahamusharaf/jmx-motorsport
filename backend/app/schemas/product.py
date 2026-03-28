"""
Pydantic schemas for product catalog API request/response validation.
"""

from pydantic import BaseModel, Field

class ProductColorVariant(BaseModel):
    color: str
    images: list[str]

class ProductVariant(BaseModel):
    name: str
    images: list[str]


class ProductBase(BaseModel):
    name: str
    slug: str
    category: str
    subcategory: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = "USD"
    images: list[str] = []
    features: list[str] = []
    sizes: list[str] = []
    colors: list[str] = []
    in_stock: bool = True
    is_featured: bool = False
    sku: str | None = None
    variants: list[ProductVariant] | None = None
    color_variants: list[ProductColorVariant] | None = None


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product — all fields optional."""
    name: str | None = None
    slug: str | None = None
    category: str | None = None
    subcategory: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    images: list[str] | None = None
    features: list[str] | None = None
    sizes: list[str] | None = None
    colors: list[str] | None = None
    in_stock: bool | None = None
    is_featured: bool | None = None


class ProductResponse(ProductBase):
    """Schema for product response — id is a string (MongoDB ObjectId)."""
    id: str

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Schema for category listing."""
    name: str
    slug: str
    subcategories: list[str] = []
    product_count: int = 0
