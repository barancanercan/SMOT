"""
Reports API Routes
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.database import get_report_cache, save_report_cache, clear_report_cache, clear_expired_cache
from app.core.rate_limit import limiter, RateLimits
from app.core.constants import normalize_party_name
from app.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger("Reports")
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
    request: Request,
    body: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a professional intelligence report for a user.

    Options:
    - use_llm: Enable LLM analysis (slower but more detailed)
    - force_refresh: Ignore cache and regenerate

    Rate limit: 5 requests per minute
    """
    username = body.username

    # Check cache first
    if not body.force_refresh:
        cached = get_report_cache(username, "full" if body.use_llm else "quick")
        if cached:
            return {
                "username": username,
                "report": cached["content"],
                "cached": True,
                "created_at": cached["created_at"],
            }

    # Generate new report
    try:
        logger.info(f"📊 Rapor oluşturuluyor: @{username} (LLM: {body.use_llm})")
        generator = ReportGenerator(use_llm=body.use_llm)
        report = generator.generate_report(username)

        # Cache the report
        report_type = "full" if body.use_llm else "quick"
        save_report_cache(username, report_type, report)

        logger.info(f"✅ Rapor başarılı: @{username}")
        return {
            "username": username,
            "content": report,
            "cached": False,
        }
    except Exception as e:
        logger.error(f"❌ Rapor hatası @{username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/batch")
@limiter.limit(RateLimits.BATCH)
async def generate_batch_report(
    request: Request,
    body: BatchReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate reports for multiple users.

    Returns immediately and processes in background.

    Rate limit: 3 requests per minute
    """
    if not body.usernames:
        raise HTTPException(status_code=400, detail="No usernames provided")

    if len(body.usernames) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 users per batch")

    # Start background task
    # For now, we'll process synchronously but this should be moved to Celery
    try:
        generator = ReportGenerator(use_llm=body.use_llm)
        reports = {}

        for username in body.usernames:
            try:
                report = generator.generate_report(username)
                reports[username] = {"status": "success", "report": report}

                # Cache each report
                report_type = "full" if body.use_llm else "quick"
                save_report_cache(username, report_type, report)
            except Exception as e:
                reports[username] = {"status": "error", "error": str(e)}

        return {
            "total": len(body.usernames),
            "success": sum(1 for r in reports.values() if r["status"] == "success"),
            "failed": sum(1 for r in reports.values() if r["status"] == "error"),
            "reports": reports,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@router.get("/{username}")
@limiter.limit(RateLimits.STANDARD)
async def get_cached_report(
    request: Request,
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


@router.delete("/cache")
@limiter.limit(RateLimits.WRITE)
async def clear_all_cache(
    request: Request,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Clear all cached reports.

    Options:
    - report_type: Optional filter by report type ("full" or "quick")

    Rate limit: 20 requests per minute
    """
    deleted = clear_report_cache(report_type=report_type)
    return {"deleted": deleted, "report_type": report_type or "all"}


@router.delete("/{username}/cache")
@limiter.limit(RateLimits.WRITE)
async def clear_user_cache(
    request: Request,
    username: str,
    db: Session = Depends(get_db)
):
    """
    Clear cached reports for a user.

    Rate limit: 20 requests per minute
    """
    deleted = clear_report_cache(username=username)
    return {"deleted": deleted}


@router.post("/cache/cleanup")
@limiter.limit(RateLimits.WRITE)
async def cleanup_expired_cache(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Clean up expired cache entries.

    Rate limit: 20 requests per minute
    """
    deleted = clear_expired_cache()
    return {"deleted": deleted, "message": "Expired cache entries cleaned up"}


class PartyReportRequest(BaseModel):
    party: str
    use_llm: bool = False


class MultiUserReportRequest(BaseModel):
    usernames: List[str]
    use_llm: bool = True


@router.post("/multi")
@limiter.limit(RateLimits.HEAVY)
async def generate_multi_user_report(
    request: Request,
    body: MultiUserReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a combined report for multiple users.

    Args:
    - usernames: List of usernames (2-10 users)
    - use_llm: Enable LLM analysis

    Rate limit: 5 requests per minute
    """
    from app.core.models import Councilor, Tweet
    from sqlalchemy import func

    if not body.usernames:
        raise HTTPException(status_code=400, detail="Kullanici listesi bos")

    if len(body.usernames) < 2:
        raise HTTPException(status_code=400, detail="En az 2 kullanici secilmeli")

    if len(body.usernames) > 10:
        raise HTTPException(status_code=400, detail="Maksimum 10 kullanici secebilirsiniz")

    try:
        # Get all selected users
        councilors = db.query(Councilor).filter(
            Councilor.username.in_(body.usernames)
        ).all()

        if not councilors:
            raise HTTPException(status_code=404, detail="Kullanici bulunamadi")

        councilor_map = {c.username: c for c in councilors}

        # Build report header
        report_lines = [
            "# Coklu Kullanici Raporu",
            "",
            f"**Analiz Edilen Kullanicilar:** {len(councilors)}",
            f"**Tarih:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
        ]

        # Individual user sections
        all_tweets_for_llm = []
        for username in body.usernames:
            if username not in councilor_map:
                continue

            c = councilor_map[username]

            # Get user stats
            stats = db.query(
                func.count(Tweet.id).label("tweet_count"),
                func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
            ).filter(
                Tweet.username == username,
                Tweet.is_retweet == False
            ).first()

            report_lines.append(f"## @{username} - {c.name}")
            report_lines.append("")
            report_lines.append(f"- **Parti:** {normalize_party_name(c.party)}")
            report_lines.append(f"- **Ilce:** {c.district or 'Bilinmiyor'}")
            report_lines.append(f"- **Tweet Sayisi:** {stats.tweet_count:,}")
            report_lines.append(f"- **Toplam Like:** {stats.total_likes:,}")
            report_lines.append(f"- **Toplam RT:** {stats.total_retweets:,}")
            report_lines.append("")

            # Collect tweets for LLM if enabled
            if body.use_llm:
                user_tweets = db.query(Tweet).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).order_by(Tweet.tweet_date.desc()).limit(10).all()

                for t in user_tweets:
                    all_tweets_for_llm.append({
                        'text': t.tweet_text,
                        'date': str(t.tweet_date) if t.tweet_date else '',
                        'likes': t.likes or 0,
                        'retweets': t.retweets or 0,
                        'username': username,
                        'party': normalize_party_name(c.party)
                    })

        # LLM Combined Analysis
        if body.use_llm and all_tweets_for_llm:
            from app.services.analysis.analyzer import TweetAnalyzer

            try:
                analyzer = TweetAnalyzer()
                analysis_result = analyzer.analyze_intelligence(
                    all_tweets_for_llm,
                    username="multi_user_analysis",
                    party="Coklu"
                )

                if analysis_result.get('validated') and analysis_result.get('analysis'):
                    analysis = analysis_result['analysis']
                    report_lines.append("---")
                    report_lines.append("")
                    report_lines.append("## Birlesik AI Analizi")
                    report_lines.append("")
                    report_lines.append(f"**Genel Degerlendirme:** {analysis.executive_summary}")
                    report_lines.append("")
                    report_lines.append(f"**Ortak Temalar (Yesil):** {analysis.green_summary}")
                    report_lines.append("")
                    report_lines.append(f"**Elestiri Analizi (Kirmizi):** {analysis.red_summary}")
                    report_lines.append("")
                    report_lines.append(f"**Bagimsiz Konular (Gri):** {analysis.grey_summary}")
                    if analysis.independent_topics:
                        report_lines.append("")
                        report_lines.append(f"**Onemli Konular:** {', '.join(analysis.independent_topics[:5])}")
                    report_lines.append("")
                    report_lines.append(f"**Analiz Guveni:** {analysis.confidence_score:.1%}")

            except Exception as e:
                logger.warning(f"Coklu kullanici LLM analizi basarisiz: {str(e)}")
                report_lines.append("")
                report_lines.append("*AI analizi yapilamadi*")

        report = "\n".join(report_lines)

        return {
            "usernames": body.usernames,
            "member_count": len(councilors),
            "content": report,
            "use_llm": body.use_llm,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Coklu rapor hatasi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rapor olusturulamadi: {str(e)}")


@router.post("/party")
@limiter.limit(RateLimits.HEAVY)
async def generate_party_report(
    request: Request,
    body: PartyReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a summary report for all members of a party.

    Options:
    - use_llm: Enable LLM analysis for deeper insights (slower but more detailed)

    Rate limit: 5 requests per minute
    """
    from app.core.models import Councilor, Tweet, ProfileHistory
    from sqlalchemy import func

    try:
        # Normalize the requested party name
        normalized_party = normalize_party_name(body.party)

        # Get party members - check both normalized and original names
        # to catch all variations in the database
        members = db.query(Councilor).all()

        # Filter members by normalized party name
        members = [m for m in members if normalize_party_name(m.party) == normalized_party]

        if not members:
            raise HTTPException(status_code=404, detail=f"Parti bulunamadi: {body.party}")

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

        # Build report with normalized party name
        report_lines = [
            f"# {normalized_party} Parti Raporu",
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

        report_lines.append("")
        report_lines.append("## En Aktif Uyeler (Like)")
        report_lines.append("")

        for i, t in enumerate(top_engagement, 1):
            member = next((m for m in members if m.username == t.username), None)
            name = member.name if member else t.username
            report_lines.append(f"{i}. **{name}** - {t.likes:,} like")

        # Individual member details with LLM analysis
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("## Bireysel Uye Raporlari")
        report_lines.append("")

        all_tweets_for_llm = []
        member_tweet_map = {}  # Store tweets for individual LLM analysis

        # Initialize analyzer once if LLM is enabled
        analyzer = None
        if body.use_llm:
            from app.services.analysis.analyzer import TweetAnalyzer
            try:
                analyzer = TweetAnalyzer()
            except Exception as e:
                logger.warning(f"TweetAnalyzer baslatma hatasi: {str(e)}")

        for member in members:
            # Get member stats
            member_stats = db.query(
                func.count(Tweet.id).label("tweet_count"),
                func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
            ).filter(
                Tweet.username == member.username,
                Tweet.is_retweet == False
            ).first()

            report_lines.append(f"### @{member.username} - {member.name}")
            report_lines.append("")
            report_lines.append(f"- **Ilce:** {member.district or 'Bilinmiyor'}")
            report_lines.append(f"- **Tweet Sayisi:** {member_stats.tweet_count:,}")
            report_lines.append(f"- **Toplam Like:** {member_stats.total_likes:,}")
            report_lines.append(f"- **Toplam RT:** {member_stats.total_retweets:,}")

            # Get recent tweets for display and LLM
            member_tweets = db.query(Tweet).filter(
                Tweet.username == member.username,
                Tweet.is_retweet == False
            ).order_by(Tweet.tweet_date.desc()).limit(15).all()

            if member_tweets:
                report_lines.append("")
                report_lines.append("**Son Tweetler:**")
                for t in member_tweets[:3]:
                    tweet_preview = t.tweet_text[:100] + "..." if len(t.tweet_text) > 100 else t.tweet_text
                    report_lines.append(f"  - \"{tweet_preview}\" ({t.likes} like)")

                # Format tweets for LLM
                tweet_list = []
                for t in member_tweets:
                    tweet_data = {
                        'text': t.tweet_text,
                        'date': str(t.tweet_date) if t.tweet_date else '',
                        'likes': t.likes or 0,
                        'retweets': t.retweets or 0,
                    }
                    tweet_list.append(tweet_data)
                    all_tweets_for_llm.append({
                        **tweet_data,
                        'username': member.username,
                        'member_name': member.name
                    })

                member_tweet_map[member.username] = {
                    'member': member,
                    'tweets': tweet_list
                }

                # Individual LLM analysis for this member
                if body.use_llm and analyzer and len(tweet_list) >= 3:
                    try:
                        member_analysis = analyzer.analyze_intelligence(
                            tweet_list,
                            username=member.username,
                            party=normalized_party  # Use normalized party name
                        )

                        if member_analysis.get('validated') and member_analysis.get('analysis'):
                            analysis = member_analysis['analysis']
                            report_lines.append("")
                            report_lines.append("**AI Analizi:**")
                            report_lines.append(f"  - {analysis.executive_summary}")
                            report_lines.append(f"  - Sadakat: {analysis.loyalty_level} | Elestiri: {analysis.criticism_level}")
                            if analysis.independent_topics:
                                report_lines.append(f"  - Konular: {', '.join(analysis.independent_topics[:3])}")
                    except Exception as e:
                        logger.warning(f"Bireysel LLM analizi basarisiz @{member.username}: {str(e)}")

            report_lines.append("")

        # Collective Party-wide LLM Analysis
        if body.use_llm and analyzer and all_tweets_for_llm:
            try:
                # Party-wide analysis
                analysis_result = analyzer.analyze_intelligence(
                    all_tweets_for_llm[:50],  # Limit to 50 tweets
                    username=f"parti_{normalized_party}",
                    party=normalized_party
                )

                if analysis_result.get('validated') and analysis_result.get('analysis'):
                    analysis = analysis_result['analysis']
                    report_lines.append("---")
                    report_lines.append("")
                    report_lines.append("## AI Parti Genel Analizi")
                    report_lines.append("")
                    report_lines.append(f"**Yonetici Ozeti:** {analysis.executive_summary}")
                    report_lines.append("")
                    report_lines.append(f"**Parti Sadakati (Yesil Takim):** {analysis.green_summary}")
                    report_lines.append(f"- Sadakat Seviyesi: {analysis.loyalty_level}")
                    report_lines.append("")
                    report_lines.append(f"**Muhalefet Elestirisi (Kirmizi Takim):** {analysis.red_summary}")
                    report_lines.append(f"- Elestiri Seviyesi: {analysis.criticism_level}")
                    report_lines.append("")
                    report_lines.append(f"**Bagimsiz Konular (Gri Takim):** {analysis.grey_summary}")
                    if analysis.independent_topics:
                        report_lines.append("")
                        report_lines.append(f"**Onemli Konular:** {', '.join(analysis.independent_topics)}")
                    report_lines.append("")
                    report_lines.append(f"**Guven Skoru:** {analysis.confidence_score:.1%}")

            except Exception as e:
                logger.warning(f"LLM parti analizi basarisiz: {str(e)}")
                report_lines.append("")
                report_lines.append("*AI parti analizi yapilamadi*")

        report = "\n".join(report_lines)

        return {
            "party": normalized_party,
            "member_count": len(members),
            "content": report,
            "use_llm": body.use_llm,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rapor olusturulamadi: {str(e)}")
