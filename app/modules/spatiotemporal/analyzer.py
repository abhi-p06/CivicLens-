import math
from typing import List, Tuple, Optional
from app.models.issue import Issue

class SpatiotemporalAnalyzer:
    """
    Spatiotemporal Hotspot Detection and Recurrence Analysis.
    Identifies recurring issue corridors and hot clusters.
    """

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def analyze_location_context(
        self,
        lat: float,
        lng: float,
        existing_issues: List[Issue],
        cluster_radius_meters: float = 400.0
    ) -> Tuple[int, bool, Optional[str]]:
        """
        Returns (recurrence_count, is_hotspot, cluster_id)
        """
        nearby_count = 0
        cluster_ids = []
        for issue in existing_issues:
            dist = self.haversine_distance_meters(lat, lng, issue.latitude, issue.longitude)
            if dist <= cluster_radius_meters:
                nearby_count += 1
                if issue.hotspotClusterId:
                    cluster_ids.append(issue.hotspotClusterId)

        recurrence = nearby_count + 1
        is_hotspot = recurrence >= 3
        cluster_id = cluster_ids[0] if cluster_ids else (f"CLUSTER-LOC-{int(lat*100)}-{int(lng*100)}" if is_hotspot else None)
        return recurrence, is_hotspot, cluster_id

spatiotemporal_analyzer = SpatiotemporalAnalyzer()
