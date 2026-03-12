"""
Reports API Routes
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.database import get_report_cache, save_report_cache, clear_report_cache
from app.core.rate_limit import limiter, RateLimits
from app.services.reporting.report_generator import ReportGenerator

router = APIRouter()


class GenerateReportRequest(BaseModel):
    username: str
    use_llm: bool = True
    force_refresh: bool = False


class BatchReportRequest(BaseModel):
    usernames: List[str]
    use_llm: bool = True


@router.post("/generate")
@limiter.limit(RateLimits.HEAVY)
async def generate_report(
    request_obj: Request,
    request: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a professional intelligence report for a user.

    Options:
    - use_llm: Enable LLM analysis (slower but more detailed)
    - force_refresh: Ignore cache and regenerate

    Rate limit: 5 requests per minute
    """
    username = request.username

    # Check cache first
    if not request.force_refresh:
        cached = get_report_cache(username, "full" if request.use_llm else "quick")
        if cached:
            return {
                "username": username,
                "report": cached["content"],
                "cached": True,
                "created_at": cached["created_at"],
            }

    # Generate new report
    try:
        generator = ReportGenerator(use_llm=request.use_llm)
        report = generator.generate_report(username)

        # Cache the report
        report_type = "full" if request.use_llm else "quick"
        save_report_cache(username, report_type, report)

        return {
            "username": username,
            "content": report,
            "cached": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/batch")
@limiter.limit(RateLimits.BATCH)
async def generate_batch_report(
    request_obj: Request,
    request: BatchReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate reports for multiple users.

    Returns immediately and processes in background.

    Rate limit: 3 requests per minute
    """
    if not request.usernames:
        raise HTTPException(status_code=400, detail="No usernames provided")

    if len(request.usernames) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 users per batch")

    # Start background task
    # For now, we'll process synchronously but this should be moved to Celery
    try:
        generator = ReportGenerator(use_llm=request.use_llm)
        reports = {}

        for username in request.usernames:
            try:
                report = generator.generate_report(username)
                reports[username] = {"status": "success", "report": report}

                # Cache each report
                report_type = "full" if request.use_llm else "quick"
                save_report_cache(username, report_type, report)
            except Exception as e:
                reports[username] = {"status": "error", "error": str(e)}

        return {
            "total": len(request.usernames),
            "success": sum(1 for r in reports.values() if r["status"] == "success"),
            "failed": sum(1 for r in reports.values() if r["status"] == "error"),
            "reports": reports,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@router.get("/{username}")
@limiter.limit(RateLimits.STANDARD)
async def get_cached_report(
    request_obj: Request,
    username: str,
    report_type: str = "full",
    db: Session = Depends(get_db)
):
    """
    Get cached report for a user.

    Rate limit: 30 requests per minute
    """
    cached = get_report_cache(username, report_type)

    if not cached:
        return {
            "username": username,
            "cached": False,
            "content": None,
        }

    return {
        "username": username,
        "cached": True,
        "content": cached["content"],
        "created_at": cached["created_at"],
        "expires_at": cached["expires_at"],
    }


@router.delete("/{username}/cache")
@limiter.limit(RateLimits.WRITE)
async def clear_user_cache(
    request_obj: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Clear cached reports for a user.

    Rate limit: 20 requests per minute
    """
    deleted = clear_report_cache(username=username)
    return {"deleted": deleted}


class PartyReportRequest(BaseModel):
    party: str
    use_llm: bool = False


@router.post("/party")
@limiter.limit(RateLimits.HEAVY)
async def generate_party_report(
    request_obj: Request,
    request: PartyReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a summary report for all members of a party.

    Rate limit: 5 requests per minute
    """
    from app.core.models import Councilor, Tweet, ProfileHistory
    from sqlalchemy import func

    try:
        # Get party members
        members = db.query(Councilor).filter(
            Councilor.party.ilike(f"%{request.party}%")
        ).all()

        if not members:
            raise HTTPException(status_code=404, detail=f"Parti bulunamadi: {request.party}")

        usernames = [m.username for m in members]

        # Get aggregated stats
        tweet_stats = db.query(
            func.count(Tweet.id).label("total_tweets"),
            func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
            func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
            func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
            func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
        ).filter(
            Tweet.username.in_(usernames),
            Tweet.is_retweet == False
        ).first()

        # Get top performers
        top_engagement = db.query(
            Tweet.username,
            func.coalesce(func.sum(Tweet.likes), 0).label("likes"),
        ).filter(
            Tweet.username.in_(usernames),
            Tweet.is_retweet == False
        ).group_by(Tweet.username).order_by(
            func.sum(Tweet.likes).desc()
        ).limit(5).all()

        # Build report
        report_lines = [
            f"# {request.party} Parti Raporu",
            "",
            f"**Toplam Uye:** {len(members)}",
            "",
            "## Genel Istatistikler",
            "",
            f"| Metrik | Deger |",
            f"|--------|-------|",
            f"| Toplam Tweet | {tweet_stats.total_tweets:,} |",
            f"| Toplam Like | {tweet_stats.total_likes:,} |",
            f"| Toplam RT | {tweet_stats.total_retweets:,} |",
            f"| Toplam Yorum | {tweet_stats.total_replies:,} |",
            f"| Toplam Gorus | {tweet_stats.total_views:,} |",
            "",
            "## Uye Listesi",
            "",
        ]

        for m in members:
            report_lines.append(f"- **{m.name}** (@{m.username}) - {m.district or 'Bilinmiyor'}")

        report_lines.append("")
        report_lines.append("## En Aktif Uyeler (Like)")
        report_lines.append("")

        for i, t in enumerate(top_engagement, 1):
            member = next((m for m in members if m.username == t.username), None)
            name = member.name if member else t.username
            report_lines.append(f"{i}. **{name}** - {t.likes:,} like")

        report = "\n".join(report_lines)

        return {
            "party": request.party,
            "member_count": len(members),
            "content": report,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor olusturulamadi: {str(e)}")
