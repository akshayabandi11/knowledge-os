import time
import uuid
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging, logger, request_id_var, user_id_var
from app.core.exceptions import DomainError
from app.infrastructure.db.session import get_db

# Import Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.chat import router as chat_router

# Initialize Structured Logger
setup_logging(settings.ENVIRONMENT)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS Setup
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Correlation ID, Security Headers & Metric Logger Middleware
@app.middleware("http")
async def security_and_metrics_middleware(request: Request, call_next):
    # Set request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request_id_var.set(request_id)

    # Initialize user ID variable as empty
    user_id_var.set("")

    start_time = time.time()

    # Process Request
    response = await call_next(request)

    # Calculate performance duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Attach correlation headers
    response.headers["X-Request-ID"] = request_id

    # Enforce Secure HTTP Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'; "
        "object-src 'none';"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Extract contextual values
    user_id = user_id_var.get() or "unauthenticated"

    # Log structured details
    logger.info(
        f"API Request processed | "
        f"RequestID: {request_id} | "
        f"UserID: {user_id} | "
        f"Method: {request.method} | "
        f"Endpoint: {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration_ms}ms"
    )

    return response


# Centralized Domain Exceptions mapping handler (RFC 7807)
@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    request_id = request_id_var.get()
    error_content = {
        "type": f"/errors/{exc.code}",
        "title": exc.title,
        "status": exc.status_code,
        "detail": str(exc),
        "instance": request.url.path,
        "code": exc.code,
        "request_id": request_id,
    }
    logger.error(
        f"Domain Error processing request | "
        f"RequestID: {request_id} | "
        f"Method: {request.method} | "
        f"Endpoint: {request.url.path} | "
        f"Error: {exc.code} - {str(exc)}"
    )
    return JSONResponse(status_code=exc.status_code, content=error_content)


# Include Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


# Health & Database Connectivity verification route
@app.get("/healthz")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "project": settings.PROJECT_NAME,
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )
