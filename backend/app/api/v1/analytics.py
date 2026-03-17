"""
Analytics API Routes
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.constants import normalize_party_name
from app.core.rate_limit import limiter, RateLimits

logger = logging.getLogger("Analytics")
router = APIRouter()


class ComparisonRequest(BaseModel):
    usernames: List[str]


@router.get("/followers")
async def get_followers_ranking(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get followers ranking for all council members.
    """
    try:
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
            })
        return result
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    """
    Get engagement ranking for all users.
    """
    try:
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
            }
            for r in results
        ]
    except Exception as e:
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

    Returns metrics for each user including followers, tweets, engagement.
    """
    if not body.usernames:
        raise HTTPException(status_code=400, detail="Kullanici listesi bos")

    if len(body.usernames) < 2:
        raise HTTPException(status_code=400, detail="En az 2 kullanici secilmeli")

    if len(body.usernames) > 10:
        raise HTTPException(status_code=400, detail="Maksimum 10 kullanici secebilirsiniz")

    try:
        # Get councilors
        councilors = db.query(Councilor).filter(
            Councilor.username.in_(body.usernames)
        ).all()

        if not councilors:
            raise HTTPException(status_code=404, detail="Kullanici bulunamadi")

        councilor_map = {c.username: c for c in councilors}

        # Get latest profile for followers
        subquery = db.query(
            ProfileHistory.username,
            func.max(ProfileHistory.scrape_date).label("max_date")
        ).filter(
            ProfileHistory.username.in_(body.usernames)
        ).group_by(ProfileHistory.username).subquery()

        profiles = db.query(ProfileHistory).join(
            subquery,
            (ProfileHistory.username == subquery.c.username) &
            (ProfileHistory.scrape_date == subquery.c.max_date)
        ).all()

        profile_map = {p.username: p for p in profiles}

        # Get tweet stats
        tweet_stats = db.query(
            Tweet.username,
            func.count(Tweet.id).label("tweet_count"),
            func.coalesce(func.sum(Tweet.likes), 0).label("total_likes"),
            func.coalesce(func.sum(Tweet.retweets), 0).label("total_retweets"),
            func.coalesce(func.sum(Tweet.replies), 0).label("total_replies"),
            func.coalesce(func.sum(Tweet.views), 0).label("total_views"),
        ).filter(
            Tweet.username.in_(body.usernames),
            Tweet.is_retweet == False
        ).group_by(Tweet.username).all()

        stats_map = {s.username: s for s in tweet_stats}

        # Build response maintaining order
        metrics = []
        for username in body.usernames:
            if username not in councilor_map:
                continue

            c = councilor_map[username]
            p = profile_map.get(username)
            s = stats_map.get(username)

            followers = p.followers_count if p else 0
            tweet_count = s.tweet_count if s else 0
            total_likes = s.total_likes if s else 0
            total_retweets = s.total_retweets if s else 0

            # Calculate engagement rate (likes + retweets per tweet)
            engagement_rate = 0.0
            if tweet_count > 0:
                engagement_rate = (total_likes + total_retweets) / tweet_count

            metrics.append({
                "username": username,
                "name": c.name,
                "party": normalize_party_name(c.party),
                "district": c.district or "",
                "followers": followers,
                "tweet_count": tweet_count,
                "total_likes": total_likes,
                "total_retweets": total_retweets,
                "total_replies": s.total_replies if s else 0,
                "total_views": s.total_views if s else 0,
                "engagement_rate": round(engagement_rate, 2),
            })

        return {"users": metrics}

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

    try:
        from app.services.analysis.analyzer import TweetAnalyzer

        # Initialize analyzer
        analyzer = TweetAnalyzer()

        # Collect data for all users
        user_data = []
        all_tweets = []

        for username in body.usernames:
            councilor = db.query(Councilor).filter(Councilor.username == username).first()
            if not councilor:
                continue

            party = normalize_party_name(councilor.party)

            # Get tweets for this user
            user_tweets = db.query(Tweet).filter(
                Tweet.username == username,
                Tweet.is_retweet == False
            ).order_by(Tweet.tweet_date.desc()).limit(10).all()

            tweets = []
            for t in user_tweets:
                tweet_data = {
                    'text': t.tweet_text,
                    'date': str(t.tweet_date) if t.tweet_date else '',
                    'likes': t.likes or 0,
                    'retweets': t.retweets or 0,
                }
                tweets.append(tweet_data)
                all_tweets.append({**tweet_data, 'username': username})

            user_data.append({
                'username': username,
                'name': councilor.name,
                'party': party,
                'tweets': tweets
            })

        # Build comparison analysis
        analysis_text = ""
        if len(user_data) >= 2 and all_tweets:
            try:
                usernames_str = ", ".join([f"@{u['username']}" for u in user_data])
                logger.info(f"LLM karsilastirma basliyor: {usernames_str}")

                # For 2 users, use the specialized comparison prompt
                if len(user_data) == 2:
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
                    # For 3+ users, run individual analyses and combine
                    analysis_lines = [
                        f"## {len(user_data)} Kullanici Karsilastirma Analizi",
                        "",
                    ]

                    for ud in user_data:
                        if len(ud['tweets']) >= 1:
                            try:
                                result = analyzer.analyze_intelligence(
                                    ud['tweets'],
                                    username=ud['username'],
                                    party=ud['party']
                                )

                                if result.get('validated') and result.get('analysis'):
                                    a = result['analysis']
                                    analysis_lines.append(f"### @{ud['username']} ({ud['party']})")
                                    analysis_lines.append(f"**Ozet:** {a.executive_summary}")
                                    analysis_lines.append(f"- Sadakat: {a.loyalty_level} | Elestiri: {a.criticism_level}")
                                    if a.independent_topics:
                                        analysis_lines.append(f"- Konular: {', '.join(a.independent_topics[:3])}")
                                    analysis_lines.append(f"- Guven: {a.confidence_score:.0%}")
                                    analysis_lines.append("")
                            except Exception as e:
                                logger.warning(f"@{ud['username']} analizi basarisiz: {str(e)}")
                                analysis_lines.append(f"### @{ud['username']} ({ud['party']})")
                                analysis_lines.append("*Analiz yapilamadi*")
                                analysis_lines.append("")

                    # Add collective summary
                    try:
                        collective = analyzer.analyze_intelligence(
                            all_tweets[:50],
                            username="comparison_group",
                            party="Coklu"
                        )

                        if collective.get('validated') and collective.get('analysis'):
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
            analysis_text = "Karsilastirma icin yeterli tweet bulunamadi."

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
