import re
from typing import Tuple, Optional

class LocationExtractor:
    """
    Interface for extracting landmarks, areas, and geocoding to coordinates.
    Maintains a deterministic local landmark directory for reliable offline demos and tests.
    """
    
    LOCAL_LANDMARK_COORDINATES = {
        "vidyavihar": (19.0728, 72.8998, "Somaiya Vidyavihar, Vidyavihar East"),
        "somaiya": (19.0728, 72.8998, "Somaiya Vidyavihar, Vidyavihar East"),
        "ghatkopar": (19.0856, 72.9082, "Ghatkopar West"),
        "lbs marg": (19.0911, 72.9154, "LBS Marg, Ghatkopar West"),
        "kurla": (19.0655, 72.8710, "Kurla West"),
        "sion": (19.0435, 72.8620, "Sion Circle"),
        "dharavi": (19.0435, 72.8562, "90 Feet Road, Dharavi"),
        "bandra": (19.0601, 72.8361, "Linking Road, Bandra West"),
        "dadar": (19.0178, 72.8478, "Dadar TT Circle"),
        "chembur": (19.0622, 72.8974, "Chembur Naka")
    }

    DEFAULT_COORDINATES = (19.0760, 72.8777, "Mumbai Central Region")

    def extract_and_geocode(self, text: str, user_location: Optional[str] = None) -> Tuple[str, float, float]:
        search_target = f"{user_location or ''} {text}".lower()
        
        for landmark, (lat, lng, canonical_name) in self.LOCAL_LANDMARK_COORDINATES.items():
            if landmark in search_target:
                resolved_name = user_location if user_location and len(user_location.strip()) > 3 else canonical_name
                return resolved_name, lat, lng
                
        fallback_name = user_location if user_location else self.DEFAULT_COORDINATES[2]
        return fallback_name, self.DEFAULT_COORDINATES[0], self.DEFAULT_COORDINATES[1]

location_extractor = LocationExtractor()
