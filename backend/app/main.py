from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import addresses, admin, auth, bookings, payments, quotes, shipments, tracking
from app.utils.logging import configure_logging

configure_logging(settings.env)

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="SEND-IT API")
app.state.limiter = limiter

def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return limiter._rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(addresses.router)
app.include_router(quotes.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(tracking.router)
app.include_router(shipments.router)
app.include_router(admin.router)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
