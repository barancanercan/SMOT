"""
Meclis Istihbarat Sistemi - FastAPI Backend
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_database
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1.router import api_router

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    init_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Meclis Istihbarat Sistemi API",
    description="Siyasi istihbarat analiz platformu - REST API",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware - restricted origins (SECURITY FIX)
allowed_origins = settings.cors_origins_list if hasattr(settings, 'cors_origins_list') else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Remove wildcard if present in production
if settings.environment == "production":
    allowed_origins = [o for o in allowed_origins if o != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Cache control for API responses
    if "/api/" in str(request.url):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

    return response


# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "3.1.0"}


@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "API is working"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Meclis Istihbarat Sistemi API",
        "version": "3.1.0",
        "docs": "/docs",
        "auth": "/api/v1/auth/token"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
