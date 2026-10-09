import re
from typing import Tuple, Optional, Dict, Any

class LocationExtractor:
    """
    Location Extraction & Geocoding Engine:
    - Extracts named civic landmarks and road corridors from complaint text
    - Geocodes to accurate WGS84 coordinates using local Mumbai geospatial directory
    - Explicitly marks whether coordinates are live extracted or fallback
    """
    
    LOCAL_LANDMARK_COORDINATES = {
        "lbs marg, ghatkopar": (19.0911, 72.9154, "LBS Marg, Ghatkopar West", "N-Ward"),
        "somaiya vidyavihar": (19.0728, 72.8998, "Somaiya Vidyavihar Campus, Vidyavihar East", "N-Ward"),
        "vidyavihar": (19.0728, 72.8998, "Somaiya Vidyavihar, Vidyavihar East", "N-Ward"),
        "somaiya": (19.0728, 72.8998, "Somaiya Vidyavihar Campus, Vidyavihar East", "N-Ward"),
        "lbs marg": (19.0911, 72.9154, "LBS Marg, Ghatkopar West", "N-Ward"),
        "ghatkopar": (19.0856, 72.9082, "Ghatkopar West", "N-Ward"),
        "r-city": (19.0990, 72.9164, "R-City Mall, Ghatkopar West", "N-Ward"),
        "kurla": (19.0655, 72.8710, "Kurla West", "L-Ward"),
        "sion": (19.0435, 72.8620, "Sion Circle", "F/North"),
        "dharavi": (19.0435, 72.8562, "90 Feet Road, Dharavi", "G/North"),
        "bandra": (19.0601, 72.8361, "Linking Road, Bandra West", "H/West"),
        "dadar": (19.0178, 72.8478, "Dadar TT Circle", "G/North"),
        "chembur": (19.0622, 72.8974, "Chembur Naka", "M/West"),
        "andheri": (19.1197, 72.8464, "Andheri East Metro Junction", "K/East"),
        "powai": (19.1176, 72.9060, "Powai Hiranandani", "S-Ward")
    }

    DEFAULT_COORDINATES = (19.0760, 72.8777, "Mumbai Central Municipal Ward", "HQ-Ward")

    def extract_and_geocode(
        self,
        text: str,
        user_location: Optional[str] = None
    ) -> Dict[str, Any]:
        search_target = f"{user_location or ''} {text}".lower()
        
        # Sort landmarks by length descending to match specific corridors (e.g. 'lbs marg') before broad areas ('ghatkopar')
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

        # Fallback to general municipal coordinates
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
