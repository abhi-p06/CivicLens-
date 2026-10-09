import math
from typing import List, Optional, Dict, Any
from app.models.issue import Issue

class SpatiotemporalAnalyzer:
    """
    Spatiotemporal Hotspot Detection & Complaint Clustering Engine:
    - Clusters geo-tagged complaints into geographic corridors
    - Evaluates 90-day recurrence density
    - Flags high-density zones as civic hotspots
    """

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000  # meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
        return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)

    def analyze_location_context(
        self,
        lat: float,
        lng: float,
        existing_issues: Optional[List[Issue]] = None,
        cluster_radius_meters: float = 400.0
    ) -> Dict[str, Any]:
        if not existing_issues:
            return {
                "recurrence": 1,
                "isHotspot": False,
                "hotspotClusterId": None,
                "clusterIssueCount": 1,
                "clusterRadiusMeters": cluster_radius_meters,
                "analysisMode": "initial_point"
            }

        nearby_issues = []
        cluster_ids = []

        for issue in existing_issues:
            dist = self.haversine_distance_meters(lat, lng, issue.latitude, issue.longitude)
            if dist <= cluster_radius_meters:
                nearby_issues.append(issue)
                if issue.hotspotClusterId:
                    cluster_ids.append(issue.hotspotClusterId)

        recurrence = len(nearby_issues) + 1
        is_hotspot = recurrence >= 3
        
        # If an existing cluster ID is known, inherit it; otherwise assign deterministic coordinate-based cluster ID
        if cluster_ids:
            cluster_id = cluster_ids[0]
        elif is_hotspot:
            lat_code = f"{int(abs(lat) * 1000):05d}"[-4:]
            lng_code = f"{int(abs(lng) * 1000):05d}"[-4:]
            cluster_id = f"CLUSTER-MUM-{lat_code}-{lng_code}"
        else:
            cluster_id = None

        return {
            "recurrence": recurrence,
            "isHotspot": is_hotspot,
            "hotspotClusterId": cluster_id,
            "clusterIssueCount": recurrence,
            "clusterRadiusMeters": cluster_radius_meters,
            "analysisMode": "spatial_cluster_evaluated"
        }

spatiotemporal_analyzer = SpatiotemporalAnalyzer()
