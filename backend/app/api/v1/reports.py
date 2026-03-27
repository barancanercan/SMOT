"""
Reports API Routes
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas import Platform
from app.core.database import (
    get_report_cache, save_report_cache, clear_report_cache, clear_expired_cache,
    get_content_by_platform, get_instagram_posts
)
from app.core.rate_limit import limiter, RateLimits
from app.core.constants import normalize_party_name
from app.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger("Reports")
router = APIRouter()


class GenerateReportRequest(BaseModel):
    username: str
    use_llm: bool = True
    force_refresh: bool = False
    platform: Platform = Platform.TWITTER


class BatchReportRequest(BaseModel):
    usernames: List[str]
    use_llm: bool = True
    platform: Platform = Platform.TWITTER


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
    - platform: 'twitter', 'instagram', or 'both'

    Rate limit: 5 requests per minute
    """
    username = body.username
    platform = body.platform

    # Build cache key with platform
    cache_key = f"{platform.value}_{'full' if body.use_llm else 'quick'}"

    # Check cache first
    if not body.force_refresh:
        cached = get_report_cache(username, cache_key)
        if cached:
            return {
                "username": username,
                "report": cached["content"],
                "cached": True,
                "created_at": cached["created_at"],
                "platform": platform.value
            }

    # Generate new report
    try:
        logger.info(f"Rapor olusturuluyor: @{username} (LLM: {body.use_llm}, Platform: {platform.value})")
        generator = ReportGenerator(use_llm=body.use_llm, platform=platform.value)
        report = generator.generate_report(username)

        # Cache the report
        save_report_cache(username, cache_key, report)

        logger.info(f"Rapor basarili: @{username}")
        return {
            "username": username,
            "content": report,
            "cached": False,
            "platform": platform.value
        }
    except Exception as e:
        logger.error(f"Rapor hatasi @{username}: {str(e)}", exc_info=True)
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
    platform: Platform = Platform.TWITTER


class MultiUserReportRequest(BaseModel):
    usernames: List[str]
    use_llm: bool = True
    platform: Platform = Platform.TWITTER


@router.post("/multi")
@limiter.limit(RateLimits.HEAVY)
async def generate_multi_user_report(
    request: Request,
    body: MultiUserReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a combined report for multiple users with individual LLM analysis.

    Args:
    - usernames: List of usernames (2-10 users)
    - use_llm: Enable LLM analysis for each user + collective

    Rate limit: 5 requests per minute
    """
    from app.core.models import Councilor, Tweet, InstagramPost
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

        # Initialize LLM analyzer if needed
        analyzer = None
        if body.use_llm:
            from app.services.analysis.analyzer import TweetAnalyzer
            try:
                analyzer = TweetAnalyzer()
            except Exception as e:
                logger.warning(f"TweetAnalyzer baslatma hatasi: {str(e)}")

        # Get platform
        platform = body.platform if hasattr(body, 'platform') else Platform.TWITTER

        # Individual user sections with LLM analysis
        all_tweets_for_llm = []
        all_posts_for_llm = []
        for username in body.usernames:
            if username not in councilor_map:
                continue

            c = councilor_map[username]
            normalized_party = normalize_party_name(c.party)

            # Get Twitter user stats if applicable
            tweet_stats = None
            if platform in [Platform.TWITTER, Platform.BOTH]:
                tweet_stats = db.query(
                    func.count(Tweet.id).label("tweet_count"),
                    func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                    func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                ).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).first()

            # Get Instagram stats if applicable
            ig_stats = None
            if platform in [Platform.INSTAGRAM, Platform.BOTH] and c.instagram_username:
                ig_stats = db.query(
                    func.count(InstagramPost.id).label("post_count"),
                    func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
                ).filter(
                    InstagramPost.username == c.instagram_username
                ).first()

            report_lines.append(f"## @{username} - {c.name}")
            report_lines.append("")
            report_lines.append(f"- **Parti:** {normalized_party}")
            report_lines.append(f"- **Ilce:** {c.district or 'Bilinmiyor'}")

            if tweet_stats and platform in [Platform.TWITTER, Platform.BOTH]:
                report_lines.append(f"- **Tweet Sayisi:** {tweet_stats.tweet_count:,}")
                report_lines.append(f"- **Twitter Like:** {tweet_stats.total_likes:,}")
                report_lines.append(f"- **Twitter RT:** {tweet_stats.total_retweets:,}")

            if ig_stats and platform in [Platform.INSTAGRAM, Platform.BOTH]:
                report_lines.append(f"- **Instagram Post:** {ig_stats.post_count:,}")
                report_lines.append(f"- **Instagram Like:** {ig_stats.total_likes:,}")
                report_lines.append(f"- **Instagram Yorum:** {ig_stats.total_comments:,}")

            # Get tweets for analysis
            tweet_list = []
            if platform in [Platform.TWITTER, Platform.BOTH]:
                user_tweets = db.query(Tweet).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).order_by(Tweet.tweet_date.desc()).limit(15).all()

                for t in user_tweets:
                    tweet_data = {
                        'text': t.tweet_text,
                        'date': str(t.tweet_date) if t.tweet_date else '',
                        'likes': t.likes or 0,
                        'retweets': t.retweets or 0,
                    }
                    tweet_list.append(tweet_data)
                    all_tweets_for_llm.append({
                        **tweet_data,
                        'username': username,
                        'party': normalized_party
                    })

            # Get Instagram posts for analysis
            post_list = []
            if platform in [Platform.INSTAGRAM, Platform.BOTH] and c.instagram_username:
                user_posts = db.query(InstagramPost).filter(
                    InstagramPost.username == c.instagram_username
                ).order_by(InstagramPost.post_date.desc()).limit(15).all()

                for p in user_posts:
                    post_data = {
                        'caption': p.caption or '',
                        'post_date': str(p.post_date) if p.post_date else '',
                        'likes': p.likes or 0,
                        'comments': p.comments or 0,
                        'is_video': p.is_video,
                    }
                    post_list.append(post_data)
                    all_posts_for_llm.append({
                        **post_data,
                        'username': username,
                        'party': normalized_party
                    })

            # Individual LLM analysis for this user
            if body.use_llm and analyzer:
                has_tweets = len(tweet_list) >= 1
                has_posts = len(post_list) >= 1

                user_analysis = None
                try:
                    # Choose the appropriate analyzer method based on platform - NO FALLBACK
                    if platform == Platform.BOTH and has_tweets and has_posts:
                        user_analysis = analyzer.analyze_multi_platform(
                            tweet_list,
                            post_list,
                            username=username,
                            party=normalized_party
                        )
                    elif platform == Platform.INSTAGRAM:
                        if has_posts:
                            user_analysis = analyzer.analyze_instagram(
                                post_list,
                                username=c.instagram_username or username,
                                party=normalized_party
                            )
                        # Instagram secili ama post yok - analiz yapma
                    elif platform == Platform.TWITTER:
                        if has_tweets:
                            user_analysis = analyzer.analyze_intelligence(
                                tweet_list,
                                username=username,
                                party=normalized_party
                            )
                        # Twitter secili ama tweet yok - analiz yapma

                    if user_analysis and user_analysis.get('validated') and user_analysis.get('analysis'):
                        analysis = user_analysis['analysis']
                        report_lines.append("")
                        report_lines.append("**AI Analizi:**")
                        report_lines.append(f"> {analysis.executive_summary}")
                        report_lines.append(f">")
                        report_lines.append(f"> - Sadakat Seviyesi: {analysis.loyalty_level}")
                        report_lines.append(f"> - Elestiri Seviyesi: {analysis.criticism_level}")
                        if analysis.independent_topics:
                            report_lines.append(f"> - Onemli Konular: {', '.join(analysis.independent_topics[:3])}")
                        report_lines.append(f"> - Guven: {analysis.confidence_score:.0%}")
                except Exception as e:
                    logger.warning(f"Bireysel LLM analizi basarisiz @{username}: {str(e)}")
                    report_lines.append("")
                    report_lines.append("*Bireysel AI analizi yapilamadi*")

            report_lines.append("")

        # Collective LLM Analysis at the end - NO FALLBACK
        has_any_tweets = bool(all_tweets_for_llm)
        has_any_posts = bool(all_posts_for_llm)
        should_analyze = (platform == Platform.TWITTER and has_any_tweets) or \
                         (platform == Platform.INSTAGRAM and has_any_posts) or \
                         (platform == Platform.BOTH and has_any_tweets and has_any_posts)

        if body.use_llm and analyzer and should_analyze:
            try:
                analysis_result = None
                if platform == Platform.BOTH and has_any_tweets and has_any_posts:
                    analysis_result = analyzer.analyze_multi_platform(
                        all_tweets_for_llm[:30],
                        all_posts_for_llm[:30],
                        username="multi_user_analysis",
                        party="Coklu"
                    )
                elif platform == Platform.INSTAGRAM and has_any_posts:
                    analysis_result = analyzer.analyze_instagram(
                        all_posts_for_llm[:50],
                        username="multi_user_analysis",
                        party="Coklu"
                    )
                elif platform == Platform.TWITTER and has_any_tweets:
                    analysis_result = analyzer.analyze_intelligence(
                        all_tweets_for_llm[:50],
                        username="multi_user_analysis",
                        party="Coklu"
                    )

                if analysis_result and analysis_result.get('validated') and analysis_result.get('analysis'):
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
                logger.warning(f"Coklu kullanici birlesik LLM analizi basarisiz: {str(e)}")
                report_lines.append("")
                report_lines.append("*Birlesik AI analizi yapilamadi*")

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
    - platform: 'twitter', 'instagram', or 'both'

    Rate limit: 5 requests per minute
    """
    from app.core.models import Councilor, Tweet, ProfileHistory, InstagramPost
    from sqlalchemy import func, Integer

    platform = body.platform

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

        # Get Instagram usernames
        instagram_usernames = [m.instagram_username for m in members if m.instagram_username]

        # Get Twitter stats
        tweet_stats = None
        if platform in [Platform.TWITTER, Platform.BOTH]:
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

        # Get Instagram stats
        instagram_stats = None
        if platform in [Platform.INSTAGRAM, Platform.BOTH] and instagram_usernames:
            instagram_stats = db.query(
                func.count(InstagramPost.id).label("total_posts"),
                func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
                func.sum(func.cast(InstagramPost.is_video, Integer)).label("total_videos"),
            ).filter(
                InstagramPost.username.in_(instagram_usernames)
            ).first()

        # Get top performers - Twitter
        top_engagement = []
        if platform in [Platform.TWITTER, Platform.BOTH]:
            top_engagement = db.query(
                Tweet.username,
                func.coalesce(func.sum(Tweet.likes), 0).label("likes"),
            ).filter(
                Tweet.username.in_(usernames),
                Tweet.is_retweet == False
            ).group_by(Tweet.username).order_by(
                func.sum(Tweet.likes).desc()
            ).limit(5).all()

        # Get top performers - Instagram
        top_instagram = []
        if platform in [Platform.INSTAGRAM, Platform.BOTH] and instagram_usernames:
            top_instagram = db.query(
                InstagramPost.username,
                func.coalesce(func.sum(InstagramPost.likes), 0).label("likes"),
            ).filter(
                InstagramPost.username.in_(instagram_usernames)
            ).group_by(InstagramPost.username).order_by(
                func.sum(InstagramPost.likes).desc()
            ).limit(5).all()

        # Build report with normalized party name
        platform_label = "Twitter" if platform == Platform.TWITTER else "Instagram" if platform == Platform.INSTAGRAM else "Twitter + Instagram"
        report_lines = [
            f"# {normalized_party} Parti Raporu",
            "",
            f"**Toplam Uye:** {len(members)}",
            f"**Platform:** {platform_label}",
            "",
            "## Genel Istatistikler",
            "",
        ]

        # Twitter stats
        if tweet_stats and platform in [Platform.TWITTER, Platform.BOTH]:
            report_lines.extend([
                "### Twitter (X)",
                "",
                f"| Metrik | Deger |",
                f"|--------|-------|",
                f"| Toplam Tweet | {tweet_stats.total_tweets:,} |",
                f"| Toplam Like | {tweet_stats.total_likes:,} |",
                f"| Toplam RT | {tweet_stats.total_retweets:,} |",
                f"| Toplam Yorum | {tweet_stats.total_replies:,} |",
                f"| Toplam Gorus | {tweet_stats.total_views:,} |",
                "",
            ])

        # Instagram stats
        if instagram_stats and platform in [Platform.INSTAGRAM, Platform.BOTH]:
            total_posts = instagram_stats.total_posts or 0
            total_videos = instagram_stats.total_videos or 0
            total_photos = total_posts - total_videos
            report_lines.extend([
                "### Instagram",
                "",
                f"| Metrik | Deger |",
                f"|--------|-------|",
                f"| Toplam Post | {total_posts:,} |",
                f"| Foto | {total_photos:,} |",
                f"| Video | {total_videos:,} |",
                f"| Toplam Like | {instagram_stats.total_likes:,} |",
                f"| Toplam Yorum | {instagram_stats.total_comments:,} |",
                "",
            ])

        report_lines.extend([
            "## Uye Listesi",
            "",
        ])

        # Top Twitter performers
        if top_engagement and platform in [Platform.TWITTER, Platform.BOTH]:
            report_lines.append("")
            report_lines.append("## En Aktif Uyeler - Twitter (Like)")
            report_lines.append("")

            for i, t in enumerate(top_engagement, 1):
                member = next((m for m in members if m.username == t.username), None)
                name = member.name if member else t.username
                report_lines.append(f"{i}. **{name}** (@{t.username}) - {t.likes:,} like")

        # Top Instagram performers
        if top_instagram and platform in [Platform.INSTAGRAM, Platform.BOTH]:
            report_lines.append("")
            report_lines.append("## En Aktif Uyeler - Instagram (Like)")
            report_lines.append("")

            for i, t in enumerate(top_instagram, 1):
                # Find member by instagram username
                member = next((m for m in members if m.instagram_username == t.username), None)
                name = member.name if member else t.username
                report_lines.append(f"{i}. **{name}** (@{t.username}) - {t.likes:,} like")

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
            report_lines.append(f"### @{member.username} - {member.name}")
            report_lines.append("")
            report_lines.append(f"- **Ilce:** {member.district or 'Bilinmiyor'}")

            tweet_list = []
            instagram_posts = []

            # Twitter stats
            if platform in [Platform.TWITTER, Platform.BOTH]:
                member_stats = db.query(
                    func.count(Tweet.id).label("tweet_count"),
                    func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                    func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                ).filter(
                    Tweet.username == member.username,
                    Tweet.is_retweet == False
                ).first()

                report_lines.append(f"- **Tweet Sayisi:** {member_stats.tweet_count:,}")
                report_lines.append(f"- **Twitter Like:** {member_stats.total_likes:,}")
                report_lines.append(f"- **Twitter RT:** {member_stats.total_retweets:,}")

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

            # Instagram stats
            if platform in [Platform.INSTAGRAM, Platform.BOTH] and member.instagram_username:
                ig_stats = db.query(
                    func.count(InstagramPost.id).label("post_count"),
                    func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
                ).filter(
                    InstagramPost.username == member.instagram_username
                ).first()

                report_lines.append(f"- **Instagram:** @{member.instagram_username}")
                report_lines.append(f"- **Post Sayisi:** {ig_stats.post_count:,}")
                report_lines.append(f"- **Instagram Like:** {ig_stats.total_likes:,}")
                report_lines.append(f"- **Instagram Yorum:** {ig_stats.total_comments:,}")

                # Get recent Instagram posts
                member_ig_posts = db.query(InstagramPost).filter(
                    InstagramPost.username == member.instagram_username
                ).order_by(InstagramPost.post_date.desc()).limit(10).all()

                if member_ig_posts:
                    report_lines.append("")
                    report_lines.append("**Son Instagram Postlari:**")
                    for p in member_ig_posts[:3]:
                        media_type = "Video" if p.is_video else "Foto"
                        caption_preview = (p.caption[:80] + "...") if p.caption and len(p.caption) > 80 else (p.caption or "(aciklama yok)")
                        report_lines.append(f"  - [{media_type}] \"{caption_preview}\" ({p.likes} like)")

                    # Format for LLM
                    for p in member_ig_posts:
                        instagram_posts.append({
                            'caption': p.caption or '',
                            'post_date': str(p.post_date) if p.post_date else '',
                            'likes': p.likes or 0,
                            'comments': p.comments or 0,
                            'is_video': p.is_video,
                        })

            member_tweet_map[member.username] = {
                'member': member,
                'tweets': tweet_list,
                'instagram_posts': instagram_posts
            }

            # Individual LLM analysis for this member
            if body.use_llm and analyzer:
                try:
                    # Use multi-platform analysis if both platforms have data
                    if platform == Platform.BOTH and tweet_list and instagram_posts:
                        member_analysis = analyzer.analyze_multi_platform(
                            tweet_list,
                            instagram_posts,
                            username=member.username,
                            party=normalized_party
                        )
                    elif platform == Platform.INSTAGRAM and instagram_posts:
                        member_analysis = analyzer.analyze_instagram(
                            instagram_posts,
                            username=member.instagram_username or member.username,
                            party=normalized_party
                        )
                    elif tweet_list:
                        member_analysis = analyzer.analyze_intelligence(
                            tweet_list,
                            username=member.username,
                            party=normalized_party
                        )
                    else:
                        member_analysis = None

                    if member_analysis and member_analysis.get('validated') and member_analysis.get('analysis'):
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
