"""
Analysis Schemas v3.0 - Intelligence Intelligence Report Structure
"""
from pydantic import BaseModel, Field
from typing import List

class IntelligenceEvidence(BaseModel):
    """Specific tweet evidence with metrics"""
    tweet_text: str = Field(..., description="Content of the tweet")
    likes: int = Field(default=0, description="Like count")
    views: int = Field(default=0, description="View count")
    date: str = Field(default="", description="Tweet date")


class GreenTeamAnalysis(BaseModel):
    """Self-party/leader analysis (Yeşil Takım)"""
    summary: str = Field(..., description="How they support their own party/leader")
    representation_score: str = Field(..., description="Support level: Düşük/Orta/Yüksek")
    key_messages: List[str] = Field(..., description="Main support messages identified")
    evidence: List[IntelligenceEvidence] = Field(default_factory=list, description="Supporting tweets")


class RedTeamAnalysis(BaseModel):
    """Rival party/leader analysis (Kırmızı Takım)"""
    summary: str = Field(..., description="How they criticize or target rival parties")
    target_parties: List[str] = Field(..., description="List of targeted parties/leaders")
    criticism_points: List[str] = Field(..., description="Main points of criticism")
    evidence: List[IntelligenceEvidence] = Field(default_factory=list, description="Supporting tweets")


class GreyTeamAnalysis(BaseModel):
    """Independent/Neutral/Institution analysis (Gri Takım)"""
    independent_topics: List[str] = Field(..., description="Topics not related to partisan politics")
    person_criticisms: List[str] = Field(..., description="Criticisms targeted at specific individuals")
    event_criticisms: List[str] = Field(..., description="Criticisms targeted at specific events")
    institution_criticisms: List[str] = Field(..., description="Criticisms targeted at institutions/organizations")
    evidence: List[IntelligenceEvidence] = Field(default_factory=list, description="Supporting tweets")


class IntelligenceAnalysis(BaseModel):
    """Comprehensive Intelligence Report Structure - Flattened for Small Models"""
    executive_summary: str = Field(..., description="Overall summary")

    # Yeşil Takım
    green_summary: str = Field(..., description="Self-party support analysis")
    loyalty_level: str = Field(..., description="Düşük/Orta/Yüksek")

    # Kırmızı Takım
    red_summary: str = Field(..., description="Rival party criticism analysis")
    criticism_level: str = Field(..., description="Düşük/Orta/Yüksek")

    # Gri Takım
    grey_summary: str = Field(..., description="Independent/Institutional analysis")
    independent_topics: List[str] = Field(default_factory=list, description="Non-political topics")

    # Confidence Score (0.0 - 1.0)
    confidence_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Analysis confidence level")


# For backward compatibility or simpler tasks
class TopicAnalysis(BaseModel):
    """Main topics identified from tweets"""
    topics: List[str] = Field(..., max_length=5, description="List of main topics (max 5)")


class PartyDefenseAnalysis(BaseModel):
    """Party/leader defense analysis"""
    defended_party: str = Field(..., description="Defended party or 'Yok'")
    intensity: str = Field(..., description="Defense intensity: Güçlü/Orta/Zayıf/Yok")


class OppositionCriticismAnalysis(BaseModel):
    """Opposition criticism analysis"""
    criticized_party: str = Field(..., description="Criticized party or 'Yok'")
    intensity: str = Field(..., description="Criticism intensity: Sert/Orta/Hafif/Yok")


class FullAnalysis(BaseModel):
    """Simplified analysis for backward compatibility"""
    main_topics: List[str] = Field(..., max_length=5, description="Main topics discussed")
    defended_party: str = Field(..., description="Party/leader defended")
    defense_intensity: str = Field(..., description="Defense strength: Güçlü/Orta/Zayıf/Yok")
    criticized_party: str = Field(..., description="Party/leader criticized")
    criticism_intensity: str = Field(..., description="Criticism strength: Sert/Orta/Hafif/Yok")
    summary: str = Field(..., description="Brief summary of overall stance")
