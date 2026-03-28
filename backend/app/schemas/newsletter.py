"""
Pydantic schemas for newsletter subscription API.
"""

from pydantic import BaseModel, EmailStr


class SubscribeRequest(BaseModel):
    """Schema for subscribing to the newsletter."""
    email: EmailStr


class BroadcastRequest(BaseModel):
    """Schema for sending a broadcast email to all subscribers."""
    subject: str
    message: str  # Plain text or HTML body
