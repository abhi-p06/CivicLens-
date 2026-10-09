import math
from typing import List, Optional, Dict, Any
from app.models.issue import Issue, IssueCategory

class DeduplicationEngine:
    """
    Spatiotemporal Duplicate and Near-Duplicate Detection Engine:
    - Haversine geodesic radius threshold (default 200m)
    - Jaccard and keyword overlap token matching
    - Identifies exact duplicates vs near-duplicate recurring complaints
    """

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    @staticmethod
    def token_similarity(text1: str, text2: str) -> float:
        stop_words = {"the", "a", "an", "in", "on", "at", "and", "or", "near", "front", "of", "to", "for"}
        tokens1 = {t for t in text1.lower().split() if t not in stop_words}
        tokens2 = {t for t in text2.lower().split() if t not in stop_words}
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        return round(intersection / union, 2)

    def check_duplicate(
        self,
        new_text: str,
        lat: float,
        lng: float,
        category: Optional[IssueCategory] = None,
        existing_issues: Optional[List[Issue]] = None,
        radius_meters: float = 250.0,
        similarity_threshold: float = 0.15
    ) -> Dict[str, Any]:
        if not existing_issues:
            return {
                "isDuplicate": False,
                "duplicateGroup": None,
                "nearDuplicateCount": 0,
                "matchedMasterIssueId": None,
                "similarityScore": 0.0,
                "distanceMeters": None,
                "dedupMode": "no_prior_records"
            }

        matched_issues = []
        set1 = set(new_text.lower().split())

        for issue in existing_issues:
            dist = self.haversine_distance_meters(lat, lng, issue.latitude, issue.longitude)
            if dist <= radius_meters:
                sim = self.token_similarity(new_text, issue.complaintText)
                set2 = set(issue.complaintText.lower().split())
                shared_tokens = len(set1.intersection(set2))
                
                # Match if within radius and either token similarity threshold met or shared category with shared keywords
                is_near = (sim >= similarity_threshold) or (shared_tokens >= 3)
                if not is_near and category and issue.category == category and dist <= 100.0:
                    is_near = True
                    sim = max(sim, 0.20)

                if is_near:
                    matched_issues.append((issue, dist, sim))

        if matched_issues:
            # Sort by highest similarity first, then closest distance
            matched_issues.sort(key=lambda x: (-x[2], x[1]))
            best_match, best_dist, best_sim = matched_issues[0]
            group_id = best_match.duplicateGroup or f"GRP-{best_match.issueId}"
            return {
                "isDuplicate": True,
                "duplicateGroup": group_id,
                "nearDuplicateCount": len(matched_issues),
                "matchedMasterIssueId": best_match.issueId,
                "similarityScore": best_sim,
                "distanceMeters": best_dist,
                "dedupMode": "spatial_lexical_match"
            }

        return {
            "isDuplicate": False,
            "duplicateGroup": None,
            "nearDuplicateCount": 0,
            "matchedMasterIssueId": None,
            "similarityScore": 0.0,
            "distanceMeters": None,
            "dedupMode": "distinct_issue"
        }

deduplication_engine = DeduplicationEngine()
