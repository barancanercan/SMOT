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
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.constants import normalize_party_name
from app.core.rate_limit import limiter, RateLimits

logger = logging.getLogger("Analytics")
router = APIRouter()


class ComparisonRequest(BaseModel):
    usernames: List[str]


class PartyComparisonRequest(BaseModel):
    parties: List[str]


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
    """
    # Get base metrics
    base_result = await compare_parties(request, body, db)

    if not base_result.get("parties") or len(base_result["parties"]) < 2:
        return base_result

    try:
        from app.services.analysis.analyzer import TweetAnalyzer
        analyzer = TweetAnalyzer()

        # Collect sample tweets from each party
        party_data = []
        all_tweets = []

        for party_name in body.parties:
            normalized_party = normalize_party_name(party_name)
            councilors = db.query(Councilor).all()
            party_members = [c for c in councilors if normalize_party_name(c.party) == normalized_party]
            usernames = [c.username for c in party_members]

            # Get sample tweets from this party
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

            party_data.append({
                'party': normalized_party,
                'member_count': len(party_members),
                'tweets': tweets
            })
            all_tweets.extend(tweets)

        # Generate analysis
        analysis_lines = [
            f"## {len(body.parties)} Parti Karsilastirma Analizi",
            "",
        ]

        for pd in party_data:
            if pd['tweets']:
                try:
                    result = analyzer.analyze_intelligence(
                        [{'tweet_text': t['text'], 'tweet_date': t['date'], 'likes': t['likes'], 'views': 0} for t in pd['tweets']],
                        username=pd['party'],
                        party=pd['party']
                    )

                    if result.get('validated') and result.get('analysis'):
                        a = result['analysis']
                        analysis_lines.append(f"### {pd['party']} ({pd['member_count']} Uye)")
                        analysis_lines.append(f"**Genel Durus:** {a.executive_summary}")
                        analysis_lines.append(f"- Parti Sadakati: {a.loyalty_level}")
                        analysis_lines.append(f"- Elestiri Seviyesi: {a.criticism_level}")
                        if a.independent_topics:
                            analysis_lines.append(f"- One Cikan Konular: {', '.join(a.independent_topics[:3])}")
                        analysis_lines.append("")
                except Exception as e:
                    logger.warning(f"{pd['party']} analizi basarisiz: {str(e)}")

        analysis_text = "\n".join(analysis_lines)

        return {
            "parties": base_result["parties"],
            "analysis": analysis_text,
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
