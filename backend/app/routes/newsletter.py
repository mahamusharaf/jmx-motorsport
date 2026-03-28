"""
Newsletter subscription routes.

POST /api/newsletter/subscribe  — save an email to MongoDB subscribers collection
POST /api/newsletter/broadcast  — send an HTML email to all subscribers
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from app.database import get_database
from app.schemas.newsletter import SubscribeRequest, BroadcastRequest

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])


def get_subscribers_collection():
    db = get_database()
    return db["subscribers"]


# ── Subscribe ────────────────────────────────────────────────────────────────

@router.post("/subscribe")
async def subscribe(req: SubscribeRequest):
    """Save an email address to the subscribers collection (deduplicates)."""
    col = get_subscribers_collection()
    email = req.email.lower()

    existing = await col.find_one({"email": email})
    if existing:
        return {"status": "already_subscribed", "message": "You're already on the list!"}

    await col.insert_one({
        "email": email,
        "subscribed_at": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "subscribed", "message": "You're in! Thanks for subscribing."}


# ── Broadcast ────────────────────────────────────────────────────────────────

@router.post("/broadcast")
async def broadcast(req: BroadcastRequest):
    """Send a marketing email to every subscriber. Call this when launching a new product."""
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Email credentials not configured. Add EMAIL_SENDER and EMAIL_PASSWORD to .env"
        )

    col = get_subscribers_collection()
    subscribers = await col.find({}).to_list(length=10_000)

    if not subscribers:
        return {"status": "no_subscribers", "message": "No subscribers to email."}

    # Build a clean HTML email
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#0d0d0d;color:#f0f0f0;padding:0;margin:0;">
      <div style="max-width:600px;margin:0 auto;padding:40px 32px;">
        <img src="https://res.cloudinary.com/dmp05w5mi/image/upload/jmx-logo.png"
             alt="JMX Motorsport" style="height:50px;margin-bottom:30px;">
        <h1 style="color:#e31e26;font-size:28px;margin:0 0 16px;">{req.subject}</h1>
        <div style="font-size:16px;line-height:1.7;color:#ccc;">{req.message}</div>
        <hr style="border:none;border-top:1px solid #333;margin:40px 0;">
        <p style="font-size:12px;color:#666;">
          You are receiving this because you subscribed to JMX Motorsport updates.<br>
          © 2026 JMX Motorsport. All rights reserved.
        </p>
      </div>
    </body></html>
    """

    # At this point EMAIL_SENDER and EMAIL_PASSWORD are definitely set (guarded above)
    assert isinstance(EMAIL_SENDER, str)
    assert isinstance(EMAIL_PASSWORD, str)
    sender: str = EMAIL_SENDER
    password: str = EMAIL_PASSWORD

    failed = []
    sent: int = 0

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            for sub in subscribers:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = req.subject
                    msg["From"] = f"JMX Motorsport <{sender}>"
                    msg["To"] = sub["email"]
                    msg.attach(MIMEText(html_body, "html"))
                    server.sendmail(sender, sub["email"], msg.as_string())
                    sent += 1
                except Exception:
                    failed.append(sub["email"])

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Gmail authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD in .env"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")

    return {
        "status": "done",
        "sent": sent,
        "failed": len(failed),
        "failed_emails": failed
    }
