"""
Application Constants - Party Name Normalization
Ensures consistent party names across the system
"""
from __future__ import annotations
from typing import Dict

# Party name aliases mapping to canonical names
PARTY_ALIASES: Dict[str, str] = {
    # CHP (Cumhuriyet Halk Partisi)
    "CHP": "CHP",
    "Cumhuriyet Halk Partisi": "CHP",
    "chp": "CHP",

    # AK Parti (Adalet ve Kalkınma Partisi)
    "AKP": "AK Parti",
    "AK Parti": "AK Parti",
    "Ak Parti": "AK Parti",
    "AK PARTİ": "AK Parti",
    "Adalet ve Kalkınma Partisi": "AK Parti",
    "akp": "AK Parti",

    # MHP (Milliyetçi Hareket Partisi)
    "MHP": "MHP",
    "Milliyetçi Hareket Partisi": "MHP",
    "Milliyetci Hareket Partisi": "MHP",
    "mhp": "MHP",

    # İYİ Parti
    "İYİ Parti": "İYİ Parti",
    "IYI Parti": "İYİ Parti",
    "İyi Parti": "İYİ Parti",
    "Iyi Parti": "İYİ Parti",
    "iyiparti": "İYİ Parti",
    "İYİ PARTİ": "İYİ Parti",

    # DEM Parti (formerly HDP)
    "DEM Parti": "DEM Parti",
    "DEM": "DEM Parti",
    "HDP": "DEM Parti",
    "Halkların Demokratik Partisi": "DEM Parti",
    "Halklarin Demokratik Partisi": "DEM Parti",
    "dem": "DEM Parti",
    "hdp": "DEM Parti",

    # Saadet Partisi
    "Saadet Partisi": "Saadet Partisi",
    "SP": "Saadet Partisi",
    "sp": "Saadet Partisi",

    # Yeniden Refah Partisi
    "Yeniden Refah Partisi": "Yeniden Refah Partisi",
    "Yeniden Refah": "Yeniden Refah Partisi",
    "YRP": "Yeniden Refah Partisi",
    "yrp": "Yeniden Refah Partisi",

    # TİP (Türkiye İşçi Partisi)
    "TİP": "TİP",
    "TIP": "TİP",
    "Türkiye İşçi Partisi": "TİP",
    "Turkiye Isci Partisi": "TİP",
    "tip": "TİP",

    # Bağımsız
    "Bağımsız": "Bağımsız",
    "Bagimsiz": "Bağımsız",
    "Bağımsiz": "Bağımsız",
    "Independent": "Bağımsız",
    "bagimsiz": "Bağımsız",

    # Zafer Partisi
    "Zafer Partisi": "Zafer Partisi",
    "Zafer": "Zafer Partisi",
    "ZP": "Zafer Partisi",
    "zp": "Zafer Partisi",

    # BBP (Büyük Birlik Partisi)
    "BBP": "BBP",
    "Büyük Birlik Partisi": "BBP",
    "Buyuk Birlik Partisi": "BBP",
    "BÜYÜK BİRLİK PARTİSİ": "BBP",
    "BUYUK BIRLIK PARTISI": "BBP",
    "Büyük Birlik": "BBP",
    "BÜYÜK BİRLİK": "BBP",
    "BUYUK BIRLIK": "BBP",
    "bbp": "BBP",

    # Memleket Partisi
    "Memleket Partisi": "Memleket Partisi",
    "Memleket": "Memleket Partisi",
    "MP": "Memleket Partisi",
}


def _normalize_turkish(text: str) -> str:
    """Normalize Turkish characters for comparison."""
    replacements = {
        'İ': 'I', 'ı': 'i', 'Ğ': 'G', 'ğ': 'g',
        'Ü': 'U', 'ü': 'u', 'Ş': 'S', 'ş': 's',
        'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c',
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    return text


def normalize_party_name(party: str | None) -> str:
    """
    Normalize party name to canonical form.

    Args:
        party: Raw party name from database or user input

    Returns:
        Normalized party name. Returns "Bağımsız" for None/empty strings.

    Examples:
        >>> normalize_party_name("Cumhuriyet Halk Partisi")
        'CHP'
        >>> normalize_party_name("AKP")
        'AK Parti'
        >>> normalize_party_name(None)
        'Bağımsız'
        >>> normalize_party_name("")
        'Bağımsız'
        >>> normalize_party_name("UnknownParty")
        'UnknownParty'
    """
    if not party or not party.strip():
        return "Bağımsız"

    party_stripped = party.strip()

    # Try exact match first
    if party_stripped in PARTY_ALIASES:
        return PARTY_ALIASES[party_stripped]

    # Try case-insensitive match
    for alias, canonical in PARTY_ALIASES.items():
        if alias.lower() == party_stripped.lower():
            return canonical

    # Try Turkish-normalized match
    normalized_input = _normalize_turkish(party_stripped.upper())
    for alias, canonical in PARTY_ALIASES.items():
        normalized_alias = _normalize_turkish(alias.upper())
        if normalized_alias == normalized_input:
            return canonical

    # No match found - return original stripped value
    return party_stripped


def get_party_color(party: str) -> str:
    """
    Get party color for UI visualization.

    Args:
        party: Normalized party name

    Returns:
        Hex color code for the party
    """
    colors = {
        "CHP": "#E30A17",           # Red
        "AK Parti": "#F7941D",      # Orange
        "MHP": "#DA251C",           # Dark Red
        "İYİ Parti": "#00A3E0",     # Blue
        "DEM Parti": "#9C27B0",     # Purple
        "Saadet Partisi": "#000000", # Black
        "Yeniden Refah Partisi": "#006633", # Green
        "TİP": "#E53935",           # Red
        "Zafer Partisi": "#FF6F00", # Dark Orange
        "BBP": "#000080",           # Navy
        "Memleket Partisi": "#2E7D32", # Dark Green
        "Bağımsız": "#757575",      # Gray
    }

    return colors.get(party, "#9E9E9E")  # Default gray


# Export commonly used constants
DEFAULT_PARTY = "Bağımsız"
ALL_PARTIES = sorted(set(PARTY_ALIASES.values()))
