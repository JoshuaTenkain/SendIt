from __future__ import annotations

import time

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.database import get_db
from app.routers import addresses, admin, auth, bookings, payments, quotes, shipments, tracking
from app.utils.logging import configure_logging
from sqlalchemy.orm import Session

configure_logging(settings.env)

# Initialize Sentry for error tracking in production
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.env,
    )


def _validate_config() -> None:
    """Fail fast if critical env vars are missing in production."""
    if settings.env == "prod":
        required_secrets = [
            ("SENDIT_JWT_SECRET_KEY", settings.jwt_secret_key),
            ("SENDIT_GUEST_TOKEN_SECRET", settings.guest_token_secret),
        ]
        for env_name, value in required_secrets:
            if not value or value.startswith("change-me"):
                raise RuntimeError(
                    f"Production requires {env_name} to be set to a secure random value. "
                    f"Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
        
        required_urls = [
            ("SENDIT_FRONTEND_BASE_URL", settings.frontend_base_url),
            ("SENDIT_API_BASE_URL", settings.api_base_url),
        ]
        for env_name, value in required_urls:
            if not value or value.startswith("http://localhost"):
                raise RuntimeError(
                    f"Production requires {env_name} to be set to a production domain. "
                    f"Got: {value}"
                )


_validate_config()

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="SEND-IT API")
app.state.limiter = limiter


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with duration and status code."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    # Skip health checks from logs to reduce noise
    if request.url.path != "/health":
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=int(duration * 1000),
            ip=request.client.host if request.client else "unknown",
        )
    
    return response

def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return limiter._rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
def health(db: Session = Depends(get_db)) -> dict:
    """Health check endpoint with database connectivity verification."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "environment": settings.env,
    }
