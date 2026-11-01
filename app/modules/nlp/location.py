import re
import math
from typing import Tuple, Optional, Dict, Any, List
from app.modules.gis.bounds import is_within_supported_bounds

class LocationExtractor:
    """
    Location Extraction & Geocoding Engine:
    - Extracts named civic landmarks and road corridors from complaint text
    - Geocodes to accurate WGS84 coordinates using local Mumbai & Navi Mumbai geospatial directory
    - Computes closest ward and landmark for arbitrary GPS coordinates
    - Enforces Mumbai & Navi Mumbai regional boundaries
    """
    
    LOCAL_LANDMARK_COORDINATES = {
        # Mumbai — Central & Eastern Suburbs
        "lbs marg, ghatkopar": (19.0911, 72.9154, "LBS Marg, Ghatkopar West", "N-Ward"),
        "somaiya vidyavihar": (19.0728, 72.8998, "Somaiya Vidyavihar Campus, Vidyavihar East", "N-Ward"),
        "vidyavihar": (19.0728, 72.8998, "Somaiya Vidyavihar, Vidyavihar East", "N-Ward"),
        "somaiya": (19.0728, 72.8998, "Somaiya Vidyavihar Campus, Vidyavihar East", "N-Ward"),
        "lbs marg": (19.0911, 72.9154, "LBS Marg, Ghatkopar West", "N-Ward"),
        "ghatkopar east": (19.0856, 72.9182, "Ghatkopar East", "N-Ward"),
        "ghatkopar west": (19.0856, 72.9082, "Ghatkopar West", "N-Ward"),
        "ghatkopar": (19.0856, 72.9082, "Ghatkopar West", "N-Ward"),
        "r-city": (19.0990, 72.9164, "R-City Mall, Ghatkopar West", "N-Ward"),
        "kurla west": (19.0655, 72.8710, "Kurla West", "L-Ward"),
        "kurla east": (19.0655, 72.8850, "Kurla East", "L-Ward"),
        "kurla": (19.0655, 72.8710, "Kurla West", "L-Ward"),
        "chembur": (19.0622, 72.8974, "Chembur Naka", "M/West"),
        "govandi": (19.0558, 72.9152, "Govandi Station Area", "M/East"),
        "mankhurd": (19.0494, 72.9325, "Mankhurd Link Road", "M/East"),
        "sion": (19.0435, 72.8620, "Sion Circle", "F/North"),
        "dharavi": (19.0435, 72.8562, "90 Feet Road, Dharavi", "G/North"),
        "dadar west": (19.0178, 72.8428, "Dadar West", "G/North"),
        "dadar": (19.0178, 72.8478, "Dadar TT Circle", "G/North"),
        "powai": (19.1176, 72.9060, "Powai Hiranandani", "S-Ward"),
        "bhandup": (19.1511, 72.9372, "Bhandup West", "S-Ward"),
        "mulund": (19.1726, 72.9565, "Mulund West", "T-Ward"),

        # Mumbai — Western Suburbs
        "bandra west": (19.0601, 72.8361, "Linking Road, Bandra West", "H/West"),
        "bandra east": (19.0601, 72.8520, "BKC, Bandra East", "H/East"),
        "bandra": (19.0601, 72.8361, "Linking Road, Bandra West", "H/West"),
        "khar": (19.0700, 72.8361, "Khar West", "H/West"),
        "santacruz": (19.0800, 72.8410, "S.V. Road, Santacruz", "H/West"),
        "vile parle": (19.0990, 72.8440, "Vile Parle East", "K/East"),
        "andheri east": (19.1197, 72.8464, "Andheri East Metro Junction", "K/East"),
        "andheri west": (19.1200, 72.8300, "Lokhandwala, Andheri West", "K/West"),
        "andheri": (19.1197, 72.8464, "Andheri East Metro Junction", "K/East"),
        "jogeshwari": (19.1350, 72.8480, "Jogeshwari Caves Road", "K/East"),
        "goregaon": (19.1663, 72.8526, "Goregaon West", "P/South"),
        "malad": (19.1860, 72.8485, "Malad Link Road", "P/North"),
        "kandivali": (19.2060, 72.8520, "Kandivali West", "R/South"),
        "borivali": (19.2307, 72.8567, "Borivali West", "R/Central"),
        "dahisar": (19.2500, 72.8600, "Dahisar Toll Plaza", "R/North"),

        # Mumbai — Island City (South Mumbai)
        "colaba": (18.9067, 72.8147, "Colaba Causeway", "A-Ward"),
        "fort": (18.9345, 72.8358, "Fort Business District", "A-Ward"),
        "marine drive": (18.9432, 72.8230, "Marine Drive Promenade", "A-Ward"),
        "nariman point": (18.9260, 72.8235, "Nariman Point", "A-Ward"),
        "girgaon": (18.9550, 72.8180, "Girgaon Chowpatty", "D-Ward"),
        "byculla": (18.9750, 72.8330, "Byculla Zoo Road", "E-Ward"),

        # Navi Mumbai
        "vashi": (19.0771, 72.9986, "Sector 17, Vashi, Navi Mumbai", "NMMC Vashi"),
        "sanpada": (19.0645, 73.0083, "Sanpada Palm Beach Road, Navi Mumbai", "NMMC Sanpada"),
        "nerul": (19.0330, 73.0197, "Nerul West, Navi Mumbai", "NMMC Nerul"),
        "seawoods": (19.0200, 73.0180, "Seawoods Grand Central, Navi Mumbai", "NMMC Nerul"),
        "belapur": (19.0144, 73.0380, "CBD Belapur, Navi Mumbai", "NMMC Belapur"),
        "cbd belapur": (19.0144, 73.0380, "CBD Belapur, Navi Mumbai", "NMMC Belapur"),
        "kharghar": (19.0473, 73.0699, "Utsav Chowk, Kharghar, Navi Mumbai", "CIDCO Kharghar"),
        "panvel": (18.9894, 73.1175, "Panvel Bus Depot, Navi Mumbai", "PMC Panvel"),
        "airoli": (19.1579, 72.9935, "Airoli Knowledge Park, Navi Mumbai", "NMMC Airoli"),
        "kopar khairane": (19.1027, 73.0031, "Kopar Khairane Sector 5, Navi Mumbai", "NMMC Kopar Khairane"),
        "ghansoli": (19.1170, 73.0160, "Ghansoli Railway Station, Navi Mumbai", "NMMC Ghansoli"),
        "turbhe": (19.0833, 73.0167, "Turbhe MIDC, Navi Mumbai", "NMMC Turbhe"),
        "ulwe": (18.9750, 73.0250, "Ulwe Sector 19, Navi Mumbai", "CIDCO Ulwe"),
        "dronagiri": (18.8850, 72.9550, "Dronagiri Port Node, Navi Mumbai", "CIDCO Dronagiri"),
    }

    DEFAULT_COORDINATES = (19.0760, 72.8777, "Mumbai Central Municipal Ward", "HQ-Ward")

    def derive_ward_from_coordinates(self, lat: float, lng: float) -> str:
        """Finds closest ward in the Mumbai / Navi Mumbai directory."""
        closest_ward = "N-Ward"
        min_dist = float("inf")

        for _, (clat, clng, _, ward) in self.LOCAL_LANDMARK_COORDINATES.items():
            dist = (clat - lat) ** 2 + (clng - lng) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_ward = ward

        return closest_ward

    def derive_landmark_from_coordinates(self, lat: float, lng: float) -> str:
        """Finds closest canonical locality/landmark description for GPS coordinates."""
        closest_name = self.DEFAULT_COORDINATES[2]
        min_dist = float("inf")

        for _, (clat, clng, canonical, ward) in self.LOCAL_LANDMARK_COORDINATES.items():
            dist = (clat - lat) ** 2 + (clng - lng) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_name = f"{canonical} ({ward})"

        return closest_name

    def search_landmarks(self, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Returns autocomplete suggestions for Mumbai and Navi Mumbai."""
        q = (query or "").strip().lower()
        if not q:
            # Return top featured localities
            featured = ["vidyavihar", "ghatkopar", "kurla", "bandra", "andheri", "vashi", "nerul", "kharghar", "powai", "dadar"]
            results = []
            for k in featured:
                if k in self.LOCAL_LANDMARK_COORDINATES:
                    lat, lng, canonical, ward = self.LOCAL_LANDMARK_COORDINATES[k]
                    results.append({
                        "name": canonical,
                        "ward": ward,
                        "latitude": lat,
                        "longitude": lng
                    })
            return results[:limit]

        matches = []
        for key, (lat, lng, canonical, ward) in self.LOCAL_LANDMARK_COORDINATES.items():
            if q in key or q in canonical.lower() or q in ward.lower():
                matches.append({
                    "name": canonical,
                    "ward": ward,
                    "latitude": lat,
                    "longitude": lng
                })
                if len(matches) >= limit:
                    break
        return matches

    def extract_and_geocode(
        self,
        text: str,
        user_location: Optional[str] = None
    ) -> Dict[str, Any]:
        search_target = f"{user_location or ''} {text}".lower()
        
        # Sort landmarks by length descending to match specific corridors before broad areas
        sorted_landmarks = sorted(self.LOCAL_LANDMARK_COORDINATES.items(), key=lambda item: len(item[0]), reverse=True)
        for landmark, (lat, lng, canonical_name, ward) in sorted_landmarks:
            if landmark in search_target:
                resolved_name = user_location if user_location and len(user_location.strip()) > 3 else canonical_name
                mode = "user_provided_geocoded" if (user_location and landmark in user_location.lower()) else "extracted_from_text"
                return {
                    "resolvedLocation": resolved_name,
                    "latitude": lat,
                    "longitude": lng,
                    "ward": ward,
                    "extractionMode": mode,
                    "extractedEntity": landmark
                }

        # Fallback to general municipal coordinates if text contains no landmarks
        fallback_name = user_location if user_location and len(user_location.strip()) > 1 else self.DEFAULT_COORDINATES[2]
        return {
            "resolvedLocation": fallback_name,
            "latitude": self.DEFAULT_COORDINATES[0],
            "longitude": self.DEFAULT_COORDINATES[1],
            "ward": self.DEFAULT_COORDINATES[3],
            "extractionMode": "default_coordinates",
            "extractedEntity": None
        }

location_extractor = LocationExtractor()
