"""
API v1 Router - Combines all route modules
"""
from fastapi import APIRouter

from app.api.v1 import auth, dashboard, users, analytics, tweets, reports, exports, metrics

api_router = APIRouter()

# Authentication (public)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Protected routes
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(tweets.router, prefix="/tweets", tags=["Tweets"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])

# Observability
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
