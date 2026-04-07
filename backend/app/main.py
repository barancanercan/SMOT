"""
SMOT - Sosyal Medya Gozlem Araci - FastAPI Backend
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_database
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    init_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="SMOT API",
    description="Sosyal Medya Gozlem Araci - REST API",
    version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware - configured origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.is_production else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    # Log incoming request
    logger.info(f"➡️  {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000

        # Log response
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(f"{status_emoji} {request.method} {request.url.path} - {response.status_code} ({duration:.0f}ms)")

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Cache control for API responses
        if "/api/" in str(request.url):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"💥 {request.method} {request.url.path} - ERROR: {str(e)} ({duration:.0f}ms)")
        raise


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
        "name": "SMOT API",
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
