"""Motorsport Brand — FastAPI Backend

Entry point for the product catalog API.

Dev:   uvicorn main:app --reload --port 8000
Prod:  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import connect_to_mongo, close_mongo_connection
from app.routes.products import router as products_router
from app.routes.newsletter import router as newsletter_router

load_dotenv()  # load .env in dev; on Render / Railway, env vars are set in dashboard


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle — connect & disconnect from MongoDB."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="JMX Motorsport API",
    description="Product catalog & newsletter API for JMX Motorsport.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS --------------------------------------------------------------- #
# In production set ALLOWED_ORIGINS=https://yourdomain.com in the env vars.
# Multiple origins can be comma-separated.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = (
    [o.strip() for o in _raw_origins.split(",")]
    if _raw_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health endpoint (used by Render / Railway for uptime checks) ------- #
@app.get("/health", tags=["Ops"])
async def health_check():
    return JSONResponse({"status": "ok"})


# --- Routes ------------------------------------------------------------- #
app.include_router(products_router)
app.include_router(newsletter_router)

# --- Mount Frontend (Static Files) -------------------------------------- #
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
