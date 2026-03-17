"""
Exports API Routes
"""
import logging
from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd

from app.api.deps import get_db
from app.core.models import Councilor, Tweet, ProfileHistory
from app.core.database import get_report_cache
from app.core.constants import normalize_party_name

logger = logging.getLogger("Exports")
router = APIRouter()


@router.get("/followers/excel")
async def export_followers_excel(db: Session = Depends(get_db)):
    """
    Export followers data to Excel.
    """
    # Get latest profile for each user
    subquery = db.query(
        ProfileHistory.username,
        func.max(ProfileHistory.scrape_date).label("max_date")
    ).group_by(ProfileHistory.username).subquery()

    results = db.query(
        Councilor.username,
        Councilor.name,
        Councilor.party,
        Councilor.district,
        ProfileHistory.followers_count,
        ProfileHistory.following_count,
        ProfileHistory.tweet_count,
    ).join(
        ProfileHistory, Councilor.username == ProfileHistory.username
    ).join(
        subquery,
        (ProfileHistory.username == subquery.c.username) &
        (ProfileHistory.scrape_date == subquery.c.max_date)
    ).order_by(ProfileHistory.followers_count.desc()).all()

    # Create DataFrame
    df = pd.DataFrame([
        {
            "Kullanici Adi": r.username,
            "Ad Soyad": r.name,
            "Parti": normalize_party_name(r.party),
            "Ilce": r.district,
            "Takipci": r.followers_count,
            "Takip": r.following_count,
            "Tweet Sayisi": r.tweet_count,
        }
        for r in results
    ])

    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Takipci Siralamasi")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=takipci_siralamasi.xlsx"}
    )


@router.get("/engagement/excel")
async def export_engagement_excel(db: Session = Depends(get_db)):
    """
    Export engagement data to Excel.
    """
    results = db.query(
        Tweet.username,
        Councilor.name,
        Councilor.party,
        func.count(Tweet.id).label("tweet_count"),
        func.sum(Tweet.likes).label("total_likes"),
        func.sum(Tweet.retweets).label("total_retweets"),
        func.sum(Tweet.replies).label("total_replies"),
        func.sum(Tweet.views).label("total_views"),
    ).join(
        Councilor, Tweet.username == Councilor.username
    ).filter(
        Tweet.is_retweet == False
    ).group_by(Tweet.username).order_by(func.sum(Tweet.likes).desc()).all()

    df = pd.DataFrame([
        {
            "Kullanici Adi": r.username,
            "Ad Soyad": r.name,
            "Parti": normalize_party_name(r.party),
            "Tweet Sayisi": r.tweet_count,
            "Toplam Like": r.total_likes or 0,
            "Toplam RT": r.total_retweets or 0,
            "Toplam Reply": r.total_replies or 0,
            "Toplam Gorus": r.total_views or 0,
            "Toplam Etkilesim": (r.total_likes or 0) + (r.total_retweets or 0) + (r.total_replies or 0),
        }
        for r in results
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Etkilesim Analizi")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=etkilesim_analizi.xlsx"}
    )


@router.get("/report/{username}/md")
async def export_report_markdown(username: str, db: Session = Depends(get_db)):
    """
    Export report as markdown file.
    """
    cached = get_report_cache(username, "full")

    if not cached:
        raise HTTPException(status_code=404, detail=f"No report for {username}")

    content = cached["content"].encode("utf-8")

    return StreamingResponse(
        BytesIO(content),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={username}_rapor.md"}
    )


@router.get("/report/{username}/pdf")
async def export_report_pdf(username: str, db: Session = Depends(get_db)):
    """
    Export report as professionally formatted PDF.
    """
    from app.services.reporting.pdf_generator import generate_intelligence_pdf

    cached = get_report_cache(username, "full")

    if not cached:
        raise HTTPException(status_code=404, detail=f"No report for {username}")

    # Get user info
    user = db.query(Councilor).filter(Councilor.username == username).first()
    user_name = user.name if user else username
    user_party = normalize_party_name(user.party) if user and user.party else "Bilinmiyor"
    user_district = user.district if user else "Bilinmiyor"

    content = cached["content"]

    logger.info(f"PDF olusturuluyor: @{username}")

    try:
        # Generate PDF with new modular generator
        pdf_bytes = generate_intelligence_pdf(
            username=username,
            name=user_name,
            party=user_party,
            district=user_district,
            content=content
        )

        output = BytesIO(pdf_bytes)
        output.seek(0)

        logger.info(f"PDF basarili: @{username}")

        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=istihbarat_rapor_{username}_{datetime.now().strftime('%Y%m%d')}.pdf"}
        )

    except Exception as e:
        logger.error(f"PDF hatasi @{username}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF olusturulamadi: {str(e)}")
