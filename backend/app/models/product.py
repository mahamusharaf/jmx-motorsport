"""
Product model — defines the data structure for motorsport products.
Using a simple in-memory store for now. Swap to SQLAlchemy/DB later.
"""

from typing import Optional


class Product:
    """Represents a motorsport apparel/gear product."""

    def __init__(
        self,
        id: int,
        name: str,
        slug: str,
        category: str,
        subcategory: str,
        description: str,
        price: float | None = None,
        currency: str | None = "USD",
        images: list[str] | None = None,
        features: list[str] | None = None,
        sizes: list[str] | None = None,
        colors: list[str] | None = None,
        in_stock: bool = True,
        is_featured: bool = False,
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.category = category
        self.subcategory = subcategory
        self.description = description
        self.price = price
        self.currency = currency
        self.images = images or []
        self.features = features or []
        self.sizes = sizes or []
        self.colors = colors or []
        self.in_stock = in_stock
        self.is_featured = is_featured

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "images": self.images,
            "features": self.features,
            "sizes": self.sizes,
            "colors": self.colors,
            "in_stock": self.in_stock,
            "is_featured": self.is_featured,
        }
