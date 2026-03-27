"""
Analytics API Routes
"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.api.deps import get_db
from app.api.v1.schemas import Platform, ComparisonRequest, PartyComparisonRequest
from app.core.models import Councilor, Tweet, ProfileHistory, InstagramPost, InstagramProfile
from app.core.constants import normalize_party_name
from app.core.rate_limit import limiter, RateLimits
from app.core.database import (
    get_instagram_followers_ranking,
    get_instagram_engagement_ranking,
    get_engagement_by_platform
)

logger = logging.getLogger("Analytics")
router = APIRouter()


@router.get("/followers")
async def get_followers_ranking(
    limit: int = 20,
    platform: Platform = Query(Platform.TWITTER, description="Platform for followers ranking"),
    db: Session = Depends(get_db)
):
    """
    Get followers ranking for all council members.

    Args:
        limit: Maximum number of results
        platform: 'twitter', 'instagram', or 'both'
    """
    try:
        if platform == Platform.INSTAGRAM:
            # Instagram followers ranking
            return get_instagram_followers_ranking(limit)

        elif platform == Platform.BOTH:
            # Combined ranking - get both and merge
            twitter_ranking = []
            ig_ranking = get_instagram_followers_ranking(limit)

            # Get Twitter ranking
            councilors = db.query(Councilor).all()
            councilor_map = {c.username: c for c in councilors}

            subquery = db.query(
                ProfileHistory.username,
                func.max(ProfileHistory.scrape_date).label("max_date")
            ).group_by(ProfileHistory.username).subquery()

            profiles = db.query(ProfileHistory).join(
                subquery,
                (ProfileHistory.username == subquery.c.username) &
                (ProfileHistory.scrape_date == subquery.c.max_date)
            ).order_by(ProfileHistory.followers_count.desc()).limit(limit).all()

            for p in profiles:
                c = councilor_map.get(p.username)
                twitter_ranking.append({
                    "username": p.username,
                    "name": c.name if c else p.username,
                    "party": normalize_party_name(c.party) if c else "",
                    "district": c.district if c else "",
                    "followers_count": p.followers_count or 0,
                    "following_count": p.following_count or 0,
                    "platform": "twitter"
                })

            # Merge and sort by followers
            combined = twitter_ranking + ig_ranking
            combined.sort(key=lambda x: x.get("followers_count", 0), reverse=True)
            return combined[:limit]

        else:  # TWITTER (default)
            # Get all councilors
            councilors = db.query(Councilor).all()
            councilor_map = {c.username: c for c in councilors}

            # Get latest profile for each user
            subquery = db.query(
                ProfileHistory.username,
                func.max(ProfileHistory.scrape_date).label("max_date")
            ).group_by(ProfileHistory.username).subquery()

            profiles = db.query(ProfileHistory).join(
                subquery,
                (ProfileHistory.username == subquery.c.username) &
                (ProfileHistory.scrape_date == subquery.c.max_date)
            ).order_by(ProfileHistory.followers_count.desc()).limit(limit).all()

            result = []
            for p in profiles:
                c = councilor_map.get(p.username)
                result.append({
                    "username": p.username,
                    "name": c.name if c else p.username,
                    "party": normalize_party_name(c.party) if c else "",
                    "district": c.district if c else "",
                    "followers_count": p.followers_count or 0,
                    "following_count": p.following_count or 0,
                    "platform": "twitter"
                })
            return result
    except Exception as e:
        logger.error(f"Followers ranking error: {e}")
        return []


@router.get("/parties")
async def get_party_statistics(db: Session = Depends(get_db)):
    """
    Get statistics grouped by party.
    """
    try:
        # Get all councilors
        councilors = db.query(Councilor).all()

        # Normalize party names and aggregate
        party_map = {}
        for c in councilors:
            normalized = normalize_party_name(c.party)
            if normalized not in party_map:
                party_map[normalized] = {
                    "party": normalized,
                    "member_count": 0,
                    "total_followers": 0
                }
            party_map[normalized]["member_count"] += 1

        return sorted(list(party_map.values()), key=lambda x: x["member_count"], reverse=True)
    except Exception as e:
        return []


@router.get("/engagement")
async def get_engagement_ranking(
    limit: int = 15,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platform: Platform = Query(Platform.TWITTER, description="Platform for engagement ranking"),
    db: Session = Depends(get_db)
):
    """
    Get engagement ranking for all users.

    Args:
        limit: Maximum number of results
        start_date: Optional start date filter
        end_date: Optional end date filter
        platform: 'twitter', 'instagram', or 'both'
    """
    try:
        if platform == Platform.INSTAGRAM:
            # Instagram engagement ranking
            return get_instagram_engagement_ranking(limit)

        elif platform == Platform.BOTH:
            # Combined engagement ranking
            twitter_ranking = []
            ig_ranking = get_instagram_engagement_ranking(limit)

            # Get Twitter ranking
            councilors = db.query(Councilor).all()
            councilor_map = {c.username: c for c in councilors}

            query = db.query(
                Tweet.username,
                func.count(Tweet.id).label("tweet_count"),
                func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
            ).filter(Tweet.is_retweet == False)

            if start_date:
                query = query.filter(Tweet.tweet_date >= start_date)
            if end_date:
                query = query.filter(Tweet.tweet_date <= end_date)

            results = query.group_by(Tweet.username).order_by(
                (func.coalesce(func.sum(Tweet.likes), 0) + func.coalesce(func.sum(Tweet.retweets), 0)).desc()
            ).limit(limit).all()

            for r in results:
                c = councilor_map.get(r.username)
                twitter_ranking.append({
                    "username": r.username,
                    "name": c.name if c else r.username,
                    "party": normalize_party_name(c.party) if c else "",
                    "content_count": r.tweet_count,
                    "total_likes": r.total_likes or 0,
                    "total_retweets": r.total_retweets or 0,
                    "total_replies": r.total_replies or 0,
                    "total_views": r.total_views or 0,
                    "total_engagement": (r.total_likes or 0) + (r.total_retweets or 0) + (r.total_replies or 0),
                    "platform": "twitter"
                })

            # Merge and sort by engagement
            combined = twitter_ranking + ig_ranking
            combined.sort(key=lambda x: x.get("total_engagement", 0), reverse=True)
            return combined[:limit]

        else:  # TWITTER (default)
            # Get councilor map
            councilors = db.query(Councilor).all()
            councilor_map = {c.username: c for c in councilors}

            query = db.query(
                Tweet.username,
                func.count(Tweet.id).label("tweet_count"),
                func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
            ).filter(Tweet.is_retweet == False)

            if start_date:
                query = query.filter(Tweet.tweet_date >= start_date)
            if end_date:
                query = query.filter(Tweet.tweet_date <= end_date)

            results = query.group_by(Tweet.username).order_by(
                (func.coalesce(func.sum(Tweet.likes), 0) + func.coalesce(func.sum(Tweet.retweets), 0)).desc()
            ).limit(limit).all()

            return [
                {
                    "username": r.username,
                    "name": councilor_map.get(r.username).name if councilor_map.get(r.username) else r.username,
                    "party": normalize_party_name(councilor_map.get(r.username).party) if councilor_map.get(r.username) else "",
                    "tweet_count": r.tweet_count,
                    "total_likes": r.total_likes or 0,
                    "total_retweets": r.total_retweets or 0,
                    "total_replies": r.total_replies or 0,
                    "total_views": r.total_views or 0,
                    "total_engagement": (r.total_likes or 0) + (r.total_retweets or 0) + (r.total_replies or 0),
                    "platform": "twitter"
                }
                for r in results
            ]
    except Exception as e:
        logger.error(f"Engagement ranking error: {e}")
        return []


@router.get("/districts")
async def get_district_statistics(db: Session = Depends(get_db)):
    """
    Get statistics grouped by district.
    """
    try:
        results = db.query(
            Councilor.district,
            func.count(Councilor.id).label("member_count")
        ).group_by(Councilor.district).order_by(func.count(Councilor.id).desc()).all()

        return [
            {
                "district": r.district or "Bilinmiyor",
                "member_count": r.member_count,
            }
            for r in results
        ]
    except Exception as e:
        return []


@router.post("/compare")
@limiter.limit(RateLimits.STANDARD)
async def compare_users(
    request: Request,
    body: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple users side by side with key metrics.

    Args:
    - usernames: List of usernames (2-10 users)
    - platform: 'twitter', 'instagram', or 'both'

    Returns metrics for each user including followers, content count, engagement.
    """
    if not body.usernames:
        raise HTTPException(status_code=400, detail="Kullanici listesi bos")

    if len(body.usernames) < 2:
        raise HTTPException(status_code=400, detail="En az 2 kullanici secilmeli")

    if len(body.usernames) > 10:
        raise HTTPException(status_code=400, detail="Maksimum 10 kullanici secebilirsiniz")

    platform = body.platform if hasattr(body, 'platform') else Platform.TWITTER

    try:
        # Get councilors
        councilors = db.query(Councilor).filter(
            Councilor.username.in_(body.usernames)
        ).all()

        if not councilors:
            raise HTTPException(status_code=404, detail="Kullanici bulunamadi")

        councilor_map = {c.username: c for c in councilors}

        # Build response maintaining order
        metrics = []
        for username in body.usernames:
            if username not in councilor_map:
                continue

            c = councilor_map[username]

            if platform == Platform.TWITTER or platform == Platform.BOTH:
                # Get Twitter profile
                twitter_profile = db.query(ProfileHistory).filter(
                    ProfileHistory.username == username
                ).order_by(ProfileHistory.scrape_date.desc()).first()

                # Get Twitter stats
                twitter_stats = db.query(
                    func.count(Tweet.id).label("tweet_count"),
                    func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                    func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                    func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
                ).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).first()

            if platform == Platform.INSTAGRAM or platform == Platform.BOTH:
                # Get Instagram profile
                ig_profile = db.query(InstagramProfile).filter(
                    InstagramProfile.username == username
                ).order_by(InstagramProfile.scrape_date.desc()).first()

                # Get Instagram stats
                ig_stats = db.query(
                    func.count(InstagramPost.id).label("post_count"),
                    func.coalesce(func.sum(InstagramPost.likes), 0).label("total_likes"),
                    func.coalesce(func.sum(InstagramPost.comments), 0).label("total_comments"),
                ).filter(
                    InstagramPost.username == username
                ).first()

            # Build metrics based on platform
            if platform == Platform.TWITTER:
                followers = twitter_profile.followers_count if twitter_profile else 0
                content_count = twitter_stats.tweet_count if twitter_stats else 0
                total_likes = twitter_stats.total_likes if twitter_stats else 0
                total_retweets = twitter_stats.total_retweets if twitter_stats else 0
                total_engagement = (total_likes + total_retweets + (twitter_stats.total_replies if twitter_stats else 0))

                engagement_rate = total_engagement / content_count if content_count > 0 else 0

                metrics.append({
                    "username": username,
                    "name": c.name,
                    "party": normalize_party_name(c.party),
                    "district": c.district or "",
                    "followers": followers,
                    "tweet_count": content_count,
                    "total_likes": total_likes,
                    "total_retweets": total_retweets,
                    "total_replies": twitter_stats.total_replies if twitter_stats else 0,
                    "total_views": twitter_stats.total_views if twitter_stats else 0,
                    "engagement_rate": round(engagement_rate, 2),
                    "platform": "twitter"
                })

            elif platform == Platform.INSTAGRAM:
                followers = ig_profile.followers_count if ig_profile else 0
                content_count = ig_stats.post_count if ig_stats else 0
                total_likes = ig_stats.total_likes if ig_stats else 0
                total_comments = ig_stats.total_comments if ig_stats else 0
                total_engagement = total_likes + total_comments

                engagement_rate = total_engagement / content_count if content_count > 0 else 0

                metrics.append({
                    "username": username,
                    "name": c.name,
                    "party": normalize_party_name(c.party),
                    "district": c.district or "",
                    "followers": followers,
                    "post_count": content_count,
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_engagement": total_engagement,
                    "engagement_rate": round(engagement_rate, 2),
                    "platform": "instagram"
                })

            else:  # BOTH
                twitter_followers = twitter_profile.followers_count if twitter_profile else 0
                ig_followers = ig_profile.followers_count if ig_profile else 0

                tweet_count = twitter_stats.tweet_count if twitter_stats else 0
                post_count = ig_stats.post_count if ig_stats else 0

                twitter_likes = twitter_stats.total_likes if twitter_stats else 0
                ig_likes = ig_stats.total_likes if ig_stats else 0

                twitter_engagement = (twitter_likes +
                                     (twitter_stats.total_retweets if twitter_stats else 0) +
                                     (twitter_stats.total_replies if twitter_stats else 0))
                ig_engagement = ig_likes + (ig_stats.total_comments if ig_stats else 0)
                total_engagement = twitter_engagement + ig_engagement

                total_content = tweet_count + post_count
                engagement_rate = total_engagement / total_content if total_content > 0 else 0

                metrics.append({
                    "username": username,
                    "name": c.name,
                    "party": normalize_party_name(c.party),
                    "district": c.district or "",
                    # Combined metrics
                    "total_followers": twitter_followers + ig_followers,
                    "total_content": total_content,
                    "total_likes": twitter_likes + ig_likes,
                    "total_engagement": total_engagement,
                    "engagement_rate": round(engagement_rate, 2),
                    # Platform-specific
                    "twitter_followers": twitter_followers,
                    "instagram_followers": ig_followers,
                    "tweet_count": tweet_count,
                    "post_count": post_count,
                    "twitter_engagement": twitter_engagement,
                    "instagram_engagement": ig_engagement,
                    "platform": "both"
                })

        return {"users": metrics, "platform": platform.value}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Karsilastirma hatasi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Karsilastirma yapilamadi: {str(e)}")


@router.post("/compare/llm")
@limiter.limit(RateLimits.HEAVY)
async def compare_users_llm(
    request: Request,
    body: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare 2 or more users with LLM analysis.

    Args:
    - usernames: List of 2-10 usernames
    - platform: 'twitter', 'instagram', or 'both'

    Returns metrics plus AI-generated comparison analysis.
    """
    if len(body.usernames) < 2:
        raise HTTPException(
            status_code=400,
            detail="LLM karsilastirma icin en az 2 kullanici secmelisiniz"
        )

    # Get base metrics first
    base_result = await compare_users(request, body, db)

    if not base_result.get("users") or len(base_result["users"]) < 2:
        return base_result

    # Get platform from request
    platform = body.platform if hasattr(body, 'platform') else Platform.TWITTER

    try:
        from app.services.analysis.analyzer import TweetAnalyzer

        # Initialize analyzer
        analyzer = TweetAnalyzer()

        # Collect data for all users
        user_data = []
        all_tweets = []
        all_instagram_posts = []

        for username in body.usernames:
            councilor = db.query(Councilor).filter(Councilor.username == username).first()
            if not councilor:
                continue

            party = normalize_party_name(councilor.party)

            tweets = []
            instagram_posts = []

            # Get Twitter content if platform is twitter or both
            if platform in [Platform.TWITTER, Platform.BOTH]:
                user_tweets = db.query(Tweet).filter(
                    Tweet.username == username,
                    Tweet.is_retweet == False
                ).order_by(Tweet.tweet_date.desc()).limit(10).all()

                for t in user_tweets:
                    tweet_data = {
                        'text': t.tweet_text,
                        'date': str(t.tweet_date) if t.tweet_date else '',
                        'likes': t.likes or 0,
                        'retweets': t.retweets or 0,
                    }
                    tweets.append(tweet_data)
                    all_tweets.append({**tweet_data, 'username': username})

            # Get Instagram content if platform is instagram or both
            if platform in [Platform.INSTAGRAM, Platform.BOTH] and councilor.instagram_username:
                ig_posts = db.query(InstagramPost).filter(
                    InstagramPost.username == councilor.instagram_username
                ).order_by(InstagramPost.post_date.desc()).limit(10).all()

                for p in ig_posts:
                    post_data = {
                        'caption': p.caption or '',
                        'post_date': str(p.post_date) if p.post_date else '',
                        'likes': p.likes or 0,
                        'comments': p.comments or 0,
                        'is_video': p.is_video,
                    }
                    instagram_posts.append(post_data)
                    all_instagram_posts.append({**post_data, 'username': username})

            user_data.append({
                'username': username,
                'name': councilor.name,
                'party': party,
                'tweets': tweets,
                'instagram_posts': instagram_posts
            })

        # Build comparison analysis
        analysis_text = ""
        has_content = (platform in [Platform.TWITTER, Platform.BOTH] and all_tweets) or \
                      (platform in [Platform.INSTAGRAM, Platform.BOTH] and all_instagram_posts)

        if len(user_data) >= 2 and has_content:
            try:
                usernames_str = ", ".join([f"@{u['username']}" for u in user_data])
                platform_label = "Twitter" if platform == Platform.TWITTER else "Instagram" if platform == Platform.INSTAGRAM else "Twitter + Instagram"
                logger.info(f"LLM karsilastirma basliyor: {usernames_str} (Platform: {platform_label})")

                # For 2 users with Twitter, use the specialized comparison prompt
                if len(user_data) == 2 and platform == Platform.TWITTER and all_tweets:
                    from app.services.analysis.prompts import get_prompt

                    comparison_prompt = get_prompt(
                        'comparison',
                        username1=user_data[0]['username'],
                        username2=user_data[1]['username'],
                        party1=user_data[0]['party'],
                        party2=user_data[1]['party'],
                        tweets1=user_data[0]['tweets'],
                        tweets2=user_data[1]['tweets']
                    )

                    response = analyzer._call_llm(comparison_prompt)
                    logger.info(f"LLM yanit uzunlugu: {len(response)} karakter")

                    if response and len(response) > 10:
                        import json

                        json_str = response.strip()
                        if json_str.startswith("```"):
                            json_start = json_str.find("{")
                            json_end = json_str.rfind("}") + 1
                            if json_start != -1 and json_end > json_start:
                                json_str = json_str[json_start:json_end]

                        data = json.loads(json_str)

                        if '@context' in data or '@type' in data:
                            data = analyzer._clean_json_response(data)

                        u1, u2 = user_data[0], user_data[1]
                        analysis_lines = [
                            f"## @{u1['username']} vs @{u2['username']} Karsilastirma",
                            "",
                            f"**Genel Degerlendirme:** {data.get('comparison_summary', 'Analiz yapilamadi')}",
                            "",
                            f"### @{u1['username']} Profili ({u1['party']})",
                            f"- **Baskin Tema:** {data.get('user1_profile', {}).get('dominant_theme', '-')}",
                            f"- **Siyasi Durus:** {data.get('user1_profile', {}).get('political_stance', '-')}",
                            f"- **Aktivite Seviyesi:** {data.get('user1_profile', {}).get('activity_level', '-')}",
                            "",
                            f"### @{u2['username']} Profili ({u2['party']})",
                            f"- **Baskin Tema:** {data.get('user2_profile', {}).get('dominant_theme', '-')}",
                            f"- **Siyasi Durus:** {data.get('user2_profile', {}).get('political_stance', '-')}",
                            f"- **Aktivite Seviyesi:** {data.get('user2_profile', {}).get('activity_level', '-')}",
                            "",
                            "### Benzerlikler",
                        ]

                        for sim in data.get('similarities', ['Benzerlik bulunamadi']):
                            analysis_lines.append(f"- {sim}")

                        analysis_lines.append("")
                        analysis_lines.append("### Farkliliklar")

                        for diff in data.get('differences', ['Farklilik bulunamadi']):
                            analysis_lines.append(f"- {diff}")

                        if data.get('common_topics'):
                            analysis_lines.append("")
                            analysis_lines.append(f"**Ortak Konular:** {', '.join(data.get('common_topics', []))}")

                        if data.get('recommendation'):
                            analysis_lines.append("")
                            analysis_lines.append(f"**Degerlendirme:** {data.get('recommendation')}")

                        analysis_lines.append("")
                        analysis_lines.append(f"**Guven Skoru:** {float(data.get('confidence_score', 0.8)):.0%}")

                        analysis_text = "\n".join(analysis_lines)

                else:
                    # For 3+ users or other platforms, run individual analyses and combine
                    analysis_lines = [
                        f"## {len(user_data)} Kullanici Karsilastirma Analizi ({platform_label})",
                        "",
                    ]

                    for ud in user_data:
                        has_user_tweets = len(ud.get('tweets', [])) >= 1
                        has_user_posts = len(ud.get('instagram_posts', [])) >= 1

                        result = None
                        try:
                            # Choose the appropriate analyzer method based on platform - NO FALLBACK
                            if platform == Platform.BOTH and has_user_tweets and has_user_posts:
                                result = analyzer.analyze_multi_platform(
                                    ud['tweets'],
                                    ud['instagram_posts'],
                                    username=ud['username'],
                                    party=ud['party']
                                )
                            elif platform == Platform.INSTAGRAM:
                                if has_user_posts:
                                    result = analyzer.analyze_instagram(
                                        ud['instagram_posts'],
                                        username=ud['username'],
                                        party=ud['party']
                                    )
                                # Instagram secili ama post yok - analiz yapma
                            elif platform == Platform.TWITTER:
                                if has_user_tweets:
                                    result = analyzer.analyze_intelligence(
                                        ud['tweets'],
                                        username=ud['username'],
                                        party=ud['party']
                                    )
                                # Twitter secili ama tweet yok - analiz yapma

                            if result and result.get('validated') and result.get('analysis'):
                                a = result['analysis']
                                analysis_lines.append(f"### @{ud['username']} ({ud['party']})")
                                analysis_lines.append(f"**Ozet:** {a.executive_summary}")
                                analysis_lines.append(f"- Sadakat: {a.loyalty_level} | Elestiri: {a.criticism_level}")
                                if a.independent_topics:
                                    analysis_lines.append(f"- Konular: {', '.join(a.independent_topics[:3])}")
                                analysis_lines.append(f"- Guven: {a.confidence_score:.0%}")
                                analysis_lines.append("")
                            else:
                                analysis_lines.append(f"### @{ud['username']} ({ud['party']})")
                                analysis_lines.append("*Analiz yapilamadi*")
                                analysis_lines.append("")
                        except Exception as e:
                            logger.warning(f"@{ud['username']} analizi basarisiz: {str(e)}")
                            analysis_lines.append(f"### @{ud['username']} ({ud['party']})")
                            analysis_lines.append("*Analiz yapilamadi*")
                            analysis_lines.append("")

                    # Add collective summary
                    try:
                        collective = None
                        # NO FALLBACK - only analyze content for selected platform
                        if platform == Platform.BOTH and all_tweets and all_instagram_posts:
                            collective = analyzer.analyze_multi_platform(
                                all_tweets[:30],
                                all_instagram_posts[:30],
                                username="comparison_group",
                                party="Coklu"
                            )
                        elif platform == Platform.INSTAGRAM and all_instagram_posts:
                            collective = analyzer.analyze_instagram(
                                all_instagram_posts[:50],
                                username="comparison_group",
                                party="Coklu"
                            )
                        elif platform == Platform.TWITTER and all_tweets:
                            collective = analyzer.analyze_intelligence(
                                all_tweets[:50],
                                username="comparison_group",
                                party="Coklu"
                            )

                        if collective and collective.get('validated') and collective.get('analysis'):
                            a = collective['analysis']
                            analysis_lines.append("---")
                            analysis_lines.append("")
                            analysis_lines.append("## Genel Karsilastirma Ozeti")
                            analysis_lines.append(f"**Degerlendirme:** {a.executive_summary}")
                            analysis_lines.append("")
                            analysis_lines.append(f"**Ortak Temalar:** {a.green_summary}")
                            if a.independent_topics:
                                analysis_lines.append(f"**Onemli Konular:** {', '.join(a.independent_topics[:5])}")
                            analysis_lines.append(f"**Guven Skoru:** {a.confidence_score:.0%}")
                    except Exception as e:
                        logger.warning(f"Birlesik analiz basarisiz: {str(e)}")

                    analysis_text = "\n".join(analysis_lines)

                logger.info(f"LLM karsilastirma analizi tamamlandi ({len(analysis_text)} karakter)")

            except Exception as e:
                logger.error(f"LLM karsilastirma hatasi: {str(e)}", exc_info=True)
                analysis_text = f"LLM analiz hatasi: {str(e)}"
        else:
            platform_label = "Twitter" if platform == Platform.TWITTER else "Instagram" if platform == Platform.INSTAGRAM else "Twitter + Instagram"
            analysis_text = f"Karsilastirma icin yeterli {platform_label} icerigi bulunamadi."

        return {
            "users": base_result["users"],
            "analysis": analysis_text,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM karsilastirma analizi basarisiz: {str(e)}", exc_info=True)
        return {
            "users": base_result.get("users", []),
            "analysis": f"LLM analizi yapilamadi: {str(e)}",
        }


@router.post("/parties/compare")
@limiter.limit(RateLimits.STANDARD)
async def compare_parties(
    request: Request,
    body: PartyComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple parties with aggregated metrics.
    """
    if not body.parties or len(body.parties) < 2:
        raise HTTPException(status_code=400, detail="En az 2 parti secilmeli")

    if len(body.parties) > 10:
        raise HTTPException(status_code=400, detail="Maksimum 10 parti secilebilir")

    try:
        results = []
        for party_name in body.parties:
            normalized_party = normalize_party_name(party_name)

            # Get all councilors of this party
            councilors = db.query(Councilor).all()
            party_members = [c for c in councilors if normalize_party_name(c.party) == normalized_party]

            if not party_members:
                continue

            usernames = [c.username for c in party_members]

            # Get follower stats
            subquery = db.query(
                ProfileHistory.username,
                func.max(ProfileHistory.scrape_date).label("max_date")
            ).filter(ProfileHistory.username.in_(usernames)).group_by(ProfileHistory.username).subquery()

            profiles = db.query(ProfileHistory).join(
                subquery,
                (ProfileHistory.username == subquery.c.username) &
                (ProfileHistory.scrape_date == subquery.c.max_date)
            ).all()

            total_followers = sum(p.followers_count or 0 for p in profiles)

            # Get tweet stats
            tweet_stats = db.query(
                func.count(Tweet.id).label("tweet_count"),
                func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
                func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
                func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
                func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
            ).filter(
                Tweet.username.in_(usernames),
                Tweet.is_retweet == False
            ).first()

            tweet_count = tweet_stats.tweet_count if tweet_stats else 0
            total_likes = tweet_stats.total_likes if tweet_stats else 0
            total_retweets = tweet_stats.total_retweets if tweet_stats else 0

            engagement_rate = 0.0
            if tweet_count > 0:
                engagement_rate = (total_likes + total_retweets) / tweet_count

            results.append({
                "party": normalized_party,
                "member_count": len(party_members),
                "total_followers": total_followers,
                "avg_followers": total_followers // len(party_members) if party_members else 0,
                "tweet_count": tweet_count,
                "total_likes": total_likes,
                "total_retweets": total_retweets,
                "total_engagement": total_likes + total_retweets + (tweet_stats.total_replies if tweet_stats else 0),
                "engagement_rate": round(engagement_rate, 2),
            })

        return {"parties": results}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parti karsilastirma hatasi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parties/compare/llm")
@limiter.limit(RateLimits.HEAVY)
async def compare_parties_llm(
    request: Request,
    body: PartyComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare parties with LLM analysis.

    Args:
    - parties: List of party names
    - platform: 'twitter', 'instagram', or 'both'
    """
    # Get base metrics
    base_result = await compare_parties(request, body, db)

    if not base_result.get("parties") or len(base_result["parties"]) < 2:
        return base_result

    # Get platform from request
    platform = body.platform if hasattr(body, 'platform') else Platform.TWITTER
    logger.info(f"[DEBUG] /parties/compare/llm - Platform: {platform}, parties: {body.parties}")

    try:
        from app.services.analysis.analyzer import TweetAnalyzer
        analyzer = TweetAnalyzer()

        # Collect sample content from each party
        party_data = []
        all_tweets = []
        all_instagram_posts = []

        for party_name in body.parties:
            normalized_party = normalize_party_name(party_name)
            councilors = db.query(Councilor).all()
            party_members = [c for c in councilors if normalize_party_name(c.party) == normalized_party]
            usernames = [c.username for c in party_members]
            ig_usernames = [c.instagram_username for c in party_members if c.instagram_username]

            tweets = []
            instagram_posts = []

            # Get Twitter content if platform is twitter or both
            if platform in [Platform.TWITTER, Platform.BOTH]:
                party_tweets = db.query(Tweet).filter(
                    Tweet.username.in_(usernames),
                    Tweet.is_retweet == False
                ).order_by(Tweet.tweet_date.desc()).limit(20).all()

                tweets = [{
                    'text': t.tweet_text,
                    'date': str(t.tweet_date) if t.tweet_date else '',
                    'likes': t.likes or 0,
                    'username': t.username,
                } for t in party_tweets]
                all_tweets.extend(tweets)

            # Get Instagram content if platform is instagram or both
            if platform in [Platform.INSTAGRAM, Platform.BOTH] and ig_usernames:
                party_posts = db.query(InstagramPost).filter(
                    InstagramPost.username.in_(ig_usernames)
                ).order_by(InstagramPost.post_date.desc()).limit(20).all()

                instagram_posts = [{
                    'caption': p.caption or '',
                    'post_date': str(p.post_date) if p.post_date else '',
                    'likes': p.likes or 0,
                    'comments': p.comments or 0,
                    'is_video': p.is_video,
                } for p in party_posts]
                all_instagram_posts.extend(instagram_posts)

            party_data.append({
                'party': normalized_party,
                'member_count': len(party_members),
                'tweets': tweets,
                'instagram_posts': instagram_posts
            })

        # Generate analysis
        platform_label = "Twitter" if platform == Platform.TWITTER else "Instagram" if platform == Platform.INSTAGRAM else "Twitter + Instagram"
        analysis_lines = [
            f"## {len(body.parties)} Parti Karsilastirma Analizi ({platform_label})",
            "",
        ]

        for pd in party_data:
            has_tweets = bool(pd.get('tweets'))
            has_posts = bool(pd.get('instagram_posts'))
            logger.info(f"[DEBUG] Parti: {pd['party']}, has_tweets: {has_tweets}, has_posts: {has_posts}, platform: {platform}")

            result = None
            try:
                # Choose the appropriate analyzer method based on platform - NO FALLBACK
                if platform == Platform.BOTH and has_tweets and has_posts:
                    logger.info(f"[DEBUG] {pd['party']}: analyze_multi_platform cagiriliyor")
                    result = analyzer.analyze_multi_platform(
                        pd['tweets'],
                        pd['instagram_posts'],
                        username=pd['party'],
                        party=pd['party']
                    )
                elif platform == Platform.INSTAGRAM:
                    if has_posts:
                        logger.info(f"[DEBUG] {pd['party']}: analyze_instagram cagiriliyor ({len(pd['instagram_posts'])} post)")
                        result = analyzer.analyze_instagram(
                            pd['instagram_posts'],
                            username=pd['party'],
                            party=pd['party']
                        )
                    else:
                        logger.info(f"[DEBUG] {pd['party']}: Instagram secili ama post yok!")
                    # Instagram secili ama post yok - analiz yapma
                elif platform == Platform.TWITTER:
                    if has_tweets:
                        logger.info(f"[DEBUG] {pd['party']}: analyze_intelligence cagiriliyor ({len(pd['tweets'])} tweet)")
                        result = analyzer.analyze_intelligence(
                            [{'tweet_text': t['text'], 'tweet_date': t['date'], 'likes': t['likes'], 'views': 0} for t in pd['tweets']],
                            username=pd['party'],
                            party=pd['party']
                        )
                    else:
                        logger.info(f"[DEBUG] {pd['party']}: Twitter secili ama tweet yok!")
                    # Twitter secili ama tweet yok - analiz yapma

                if result and result.get('validated') and result.get('analysis'):
                    a = result['analysis']
                    analysis_lines.append(f"### {pd['party']} ({pd['member_count']} Uye)")
                    analysis_lines.append(f"**Genel Durus:** {a.executive_summary}")
                    analysis_lines.append(f"- Parti Sadakati: {a.loyalty_level}")
                    analysis_lines.append(f"- Elestiri Seviyesi: {a.criticism_level}")
                    if a.independent_topics:
                        analysis_lines.append(f"- One Cikan Konular: {', '.join(a.independent_topics[:3])}")
                    analysis_lines.append("")
                else:
                    analysis_lines.append(f"### {pd['party']} ({pd['member_count']} Uye)")
                    analysis_lines.append("*Analiz yapilamadi*")
                    analysis_lines.append("")
            except Exception as e:
                logger.warning(f"{pd['party']} analizi basarisiz: {str(e)}")

        analysis_text = "\n".join(analysis_lines)

        return {
            "parties": base_result["parties"],
            "analysis": analysis_text,
            "platform": platform.value
        }

    except Exception as e:
        logger.error(f"Parti LLM karsilastirma hatasi: {str(e)}", exc_info=True)
        return {
            "parties": base_result.get("parties", []),
            "analysis": f"LLM analizi yapilamadi: {str(e)}",
        }


@router.get("/tweets/weekly-top")
@limiter.limit(RateLimits.STANDARD)
async def get_weekly_top_tweets(
    request: Request,
    party: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get top tweets from the last 7 days.
    Filter by party or username.
    """
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        query = db.query(Tweet).filter(
            Tweet.is_retweet == False,
            Tweet.tweet_date >= start_date.strftime("%Y-%m-%d")
        )

        # Filter by party or username
        if username:
            query = query.filter(Tweet.username == username)
        elif party:
            normalized_party = normalize_party_name(party)
            councilors = db.query(Councilor).all()
            party_members = [c.username for c in councilors if normalize_party_name(c.party) == normalized_party]
            if party_members:
                query = query.filter(Tweet.username.in_(party_members))

        # Order by engagement
        query = query.order_by(
            (func.coalesce(Tweet.likes, 0) + func.coalesce(Tweet.retweets, 0)).desc()
        ).limit(limit)

        tweets = query.all()

        # Get councilor info
        councilors = db.query(Councilor).all()
        councilor_map = {c.username: c for c in councilors}

        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "filter": {"party": party, "username": username},
            "tweets": [
                {
                    "id": t.id,
                    "username": t.username,
                    "name": councilor_map.get(t.username).name if councilor_map.get(t.username) else t.username,
                    "party": normalize_party_name(councilor_map.get(t.username).party) if councilor_map.get(t.username) else "",
                    "tweet_text": t.tweet_text,
                    "tweet_date": t.tweet_date,
                    "likes": t.likes or 0,
                    "retweets": t.retweets or 0,
                    "replies": t.replies or 0,
                    "views": t.views or 0,
                    "engagement": (t.likes or 0) + (t.retweets or 0) + (t.replies or 0),
                }
                for t in tweets
            ]
        }
    except Exception as e:
        logger.error(f"Weekly top tweets hatasi: {str(e)}", exc_info=True)
        return {"period": "", "filter": {}, "tweets": []}


@router.get("/tweets/recent")
@limiter.limit(RateLimits.STANDARD)
async def get_recent_tweets(
    request: Request,
    party: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Get most recent tweets.
    Filter by party or username.
    """
    try:
        query = db.query(Tweet).filter(Tweet.is_retweet == False)

        # Filter by party or username
        if username:
            query = query.filter(Tweet.username == username)
        elif party:
            normalized_party = normalize_party_name(party)
            councilors = db.query(Councilor).all()
            party_members = [c.username for c in councilors if normalize_party_name(c.party) == normalized_party]
            if party_members:
                query = query.filter(Tweet.username.in_(party_members))

        # Order by date
        query = query.order_by(Tweet.tweet_date.desc()).limit(limit)

        tweets = query.all()

        # Get councilor info
        councilors = db.query(Councilor).all()
        councilor_map = {c.username: c for c in councilors}

        return {
            "filter": {"party": party, "username": username},
            "tweets": [
                {
                    "id": t.id,
                    "username": t.username,
                    "name": councilor_map.get(t.username).name if councilor_map.get(t.username) else t.username,
                    "party": normalize_party_name(councilor_map.get(t.username).party) if councilor_map.get(t.username) else "",
                    "tweet_text": t.tweet_text,
                    "tweet_date": t.tweet_date,
                    "likes": t.likes or 0,
                    "retweets": t.retweets or 0,
                    "replies": t.replies or 0,
                    "views": t.views or 0,
                }
                for t in tweets
            ]
        }
    except Exception as e:
        logger.error(f"Recent tweets hatasi: {str(e)}", exc_info=True)
        return {"filter": {}, "tweets": []}


@router.get("/tweets/top")
@limiter.limit(RateLimits.STANDARD)
async def get_top_tweets_all(
    request: Request,
    party: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get all-time top tweets by engagement.
    Filter by party or username.
    """
    try:
        query = db.query(Tweet).filter(Tweet.is_retweet == False)

        # Filter by party or username
        if username:
            query = query.filter(Tweet.username == username)
        elif party:
            normalized_party = normalize_party_name(party)
            councilors = db.query(Councilor).all()
            party_members = [c.username for c in councilors if normalize_party_name(c.party) == normalized_party]
            if party_members:
                query = query.filter(Tweet.username.in_(party_members))

        # Order by engagement
        query = query.order_by(
            (func.coalesce(Tweet.likes, 0) + func.coalesce(Tweet.retweets, 0)).desc()
        ).limit(limit)

        tweets = query.all()

        # Get councilor info
        councilors = db.query(Councilor).all()
        councilor_map = {c.username: c for c in councilors}

        return {
            "filter": {"party": party, "username": username},
            "limit": limit,
            "tweets": [
                {
                    "id": t.id,
                    "username": t.username,
                    "name": councilor_map.get(t.username).name if councilor_map.get(t.username) else t.username,
                    "party": normalize_party_name(councilor_map.get(t.username).party) if councilor_map.get(t.username) else "",
                    "tweet_text": t.tweet_text,
                    "tweet_date": t.tweet_date,
                    "likes": t.likes or 0,
                    "retweets": t.retweets or 0,
                    "replies": t.replies or 0,
                    "views": t.views or 0,
                    "engagement": (t.likes or 0) + (t.retweets or 0) + (t.replies or 0),
                }
                for t in tweets
            ]
        }
    except Exception as e:
        logger.error(f"Top tweets hatasi: {str(e)}", exc_info=True)
        return {"filter": {}, "limit": limit, "tweets": []}


# =============================================================================
# Instagram Posts Endpoints
# =============================================================================

@router.get("/posts/top")
@limiter.limit(RateLimits.STANDARD)
async def get_top_posts(
    request: Request,
    party: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get all-time top Instagram posts by engagement.
    Filter by party or username.
    """
    try:
        query = db.query(InstagramPost)

        # Get councilors for mapping
        councilors = db.query(Councilor).all()
        councilor_map = {c.instagram_username: c for c in councilors if c.instagram_username}

        # Filter by party or username
        if username:
            # Check if it's a Twitter username and convert to Instagram username
            councilor = next((c for c in councilors if c.username == username), None)
            if councilor and councilor.instagram_username:
                query = query.filter(InstagramPost.username == councilor.instagram_username)
            else:
                query = query.filter(InstagramPost.username == username)
        elif party:
            normalized_party = normalize_party_name(party)
            party_ig_usernames = [c.instagram_username for c in councilors
                                  if c.instagram_username and normalize_party_name(c.party) == normalized_party]
            if party_ig_usernames:
                query = query.filter(InstagramPost.username.in_(party_ig_usernames))

        # Order by engagement (likes + comments)
        query = query.order_by(
            (func.coalesce(InstagramPost.likes, 0) + func.coalesce(InstagramPost.comments, 0)).desc()
        ).limit(limit)

        posts = query.all()

        return {
            "filter": {"party": party, "username": username},
            "limit": limit,
            "posts": [
                {
                    "id": p.id,
                    "username": p.username,
                    "name": councilor_map.get(p.username).name if councilor_map.get(p.username) else p.username,
                    "party": normalize_party_name(councilor_map.get(p.username).party) if councilor_map.get(p.username) else "",
                    "caption": p.caption,
                    "post_date": p.post_date,
                    "post_url": p.post_url,
                    "likes": p.likes or 0,
                    "comments": p.comments or 0,
                    "is_video": p.is_video,
                    "engagement": (p.likes or 0) + (p.comments or 0),
                }
                for p in posts
            ]
        }
    except Exception as e:
        logger.error(f"Top posts hatasi: {str(e)}", exc_info=True)
        return {"filter": {}, "limit": limit, "posts": []}


@router.get("/posts/weekly-top")
@limiter.limit(RateLimits.STANDARD)
async def get_weekly_top_posts(
    request: Request,
    party: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get top Instagram posts from the last 7 days.
    Filter by party or username.
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        query = db.query(InstagramPost).filter(
            InstagramPost.post_date >= start_date,
            InstagramPost.post_date <= end_date
        )

        # Get councilors for mapping
        councilors = db.query(Councilor).all()
        councilor_map = {c.instagram_username: c for c in councilors if c.instagram_username}

        # Filter by party or username
        if username:
            councilor = next((c for c in councilors if c.username == username), None)
            if councilor and councilor.instagram_username:
                query = query.filter(InstagramPost.username == councilor.instagram_username)
            else:
                query = query.filter(InstagramPost.username == username)
        elif party:
            normalized_party = normalize_party_name(party)
            party_ig_usernames = [c.instagram_username for c in councilors
                                  if c.instagram_username and normalize_party_name(c.party) == normalized_party]
            if party_ig_usernames:
                query = query.filter(InstagramPost.username.in_(party_ig_usernames))

        # Order by engagement
        query = query.order_by(
            (func.coalesce(InstagramPost.likes, 0) + func.coalesce(InstagramPost.comments, 0)).desc()
        ).limit(limit)

        posts = query.all()

        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "filter": {"party": party, "username": username},
            "posts": [
                {
                    "id": p.id,
                    "username": p.username,
                    "name": councilor_map.get(p.username).name if councilor_map.get(p.username) else p.username,
                    "party": normalize_party_name(councilor_map.get(p.username).party) if councilor_map.get(p.username) else "",
                    "caption": p.caption,
                    "post_date": p.post_date,
                    "post_url": p.post_url,
                    "likes": p.likes or 0,
                    "comments": p.comments or 0,
                    "is_video": p.is_video,
                    "engagement": (p.likes or 0) + (p.comments or 0),
                }
                for p in posts
            ]
        }
    except Exception as e:
        logger.error(f"Weekly top posts hatasi: {str(e)}", exc_info=True)
        return {"period": "", "filter": {}, "posts": []}
