"""CSV file parsing utilities"""

import pandas as pd
from typing import List, Tuple


def parse_csv(csv_file) -> Tuple[List[str], dict]:
    """
    Parse CSV and extract usernames + metadata
    Returns: (usernames_list, metadata_dict)
    """
    try:
        df = pd.read_csv(csv_file.name)
        usernames = []
        metadata = {}

        # Sütunları kontrol et
        has_username_col = "username" in df.columns
        has_link_col = "link" in df.columns
        has_name_col = "Meclis Üyesi" in df.columns or "name" in df.columns
        has_party_col = "Parti" in df.columns or "party" in df.columns
        has_district_col = "İlçe" in df.columns or "district" in df.columns

        if has_username_col:
            # username sütunundan
            for _, row in df.iterrows():
                u = str(row["username"]).replace("@", "").strip()
                if u and u != "nan":
                    usernames.append(u)
                    # Metadata topla
                    name = str(row.get("Meclis Üyesi", row.get("name", "Unknown"))).strip()
                    party = str(row.get("Parti", row.get("party", ""))).strip()
                    district = str(row.get("İlçe", row.get("district", ""))).strip()
                    metadata[u] = {
                        "name": name if name != "nan" else "Unknown",
                        "party": party if party != "nan" else "",
                        "district": district if district != "nan" else ""
                    }

        elif has_link_col:
            # link sütunundan
            for _, row in df.iterrows():
                link = str(row["link"]).strip()
                if link and ("x.com/" in link or "twitter.com/" in link):
                    u = link.split("/")[-1].replace("@", "").strip()
                    if u:
                        usernames.append(u)
                        # Metadata topla
                        name = str(row.get("Meclis Üyesi", row.get("name", u))).strip()
                        party = str(row.get("Parti", row.get("party", ""))).strip()
                        district = str(row.get("İlçe", row.get("district", ""))).strip()
                        metadata[u] = {
                            "name": name if name != "nan" else u,
                            "party": party if party != "nan" else "",
                            "district": district if district != "nan" else ""
                        }

        return list(set(usernames)), metadata

    except Exception as e:
        print(f"❌ CSV Error: {e}")
        return [], {}
