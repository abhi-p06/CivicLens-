import math
from typing import List, Tuple, Optional
from app.models.issue import Issue

class DeduplicationEngine:
    """
    Spatiotemporal duplicate and near-duplicate complaint detection.
    Matches complaints with text similarity > 0.70 within a 200m radius.
    """

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000  # meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def jaccard_similarity(text1: str, text2: str) -> float:
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def check_duplicate(
        self,
        new_text: str,
        lat: float,
        lng: float,
        existing_issues: List[Issue],
        radius_meters: float = 200.0,
        similarity_threshold: float = 0.15
    ) -> Tuple[bool, Optional[str], int]:
        """
        Returns (is_duplicate, duplicate_group_id, near_duplicate_count)
        Within 200m radius, issues sharing >= 3 significant terms or Jaccard >= 0.15 are linked.
        """
        near_matches = []
        set1 = set(new_text.lower().split())
        for issue in existing_issues:
            dist = self.haversine_distance_meters(lat, lng, issue.latitude, issue.longitude)
            if dist <= radius_meters:
                set2 = set(issue.complaintText.lower().split())
                shared_tokens = len(set1.intersection(set2))
                sim = self.jaccard_similarity(new_text, issue.complaintText)
                if sim >= similarity_threshold or shared_tokens >= 3:
                    near_matches.append(issue)

        if near_matches:
            first_match = near_matches[0]
            group_id = first_match.duplicateGroup or f"GRP-{first_match.issueId}"
            return True, group_id, len(near_matches)

        return False, None, 0

deduplication_engine = DeduplicationEngine()
