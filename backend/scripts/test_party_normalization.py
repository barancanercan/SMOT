"""
Quick test script for party normalization
"""
from app.core.constants import normalize_party_name, PARTY_ALIASES, ALL_PARTIES

print("=" * 60)
print("PARTY NORMALIZATION TEST")
print("=" * 60)

# Test cases
test_cases = [
    ("CHP", "CHP"),
    ("Cumhuriyet Halk Partisi", "CHP"),
    ("AKP", "AK Parti"),
    ("AK Parti", "AK Parti"),
    ("Adalet ve Kalkınma Partisi", "AK Parti"),
    ("MHP", "MHP"),
    ("İYİ Parti", "İYİ Parti"),
    ("IYI Parti", "İYİ Parti"),
    ("DEM Parti", "DEM Parti"),
    ("HDP", "DEM Parti"),
    (None, "Bağımsız"),
    ("", "Bağımsız"),
    ("Unknown Party", "Unknown Party"),
]

print("\nTest Results:")
print("-" * 60)
all_passed = True
for input_val, expected in test_cases:
    result = normalize_party_name(input_val)
    passed = result == expected
    all_passed = all_passed and passed
    status = "✓" if passed else "✗"
    print(f"{status} normalize_party_name({repr(input_val)}) = {repr(result)}")
    if not passed:
        print(f"  Expected: {repr(expected)}")

print("\n" + "=" * 60)
print(f"ALL TESTS {'PASSED' if all_passed else 'FAILED'}")
print("=" * 60)

print(f"\nTotal unique parties: {len(ALL_PARTIES)}")
print("Normalized party list:")
for party in ALL_PARTIES:
    print(f"  - {party}")

print(f"\nTotal aliases: {len(PARTY_ALIASES)}")
