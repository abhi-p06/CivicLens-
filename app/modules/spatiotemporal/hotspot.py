import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN

from app.models.issue import Issue, HotspotInfo, HotspotLevel, IssueCategory

class SpatiotemporalHotspotDetector:
    """
    Feature 16: Spatiotemporal Hotspot Detection
    
    Uses coordinates (lat, lng), timestamps, categories, and priority scores to:
    - Cluster issues using Haversine DBSCAN or spatial density
    - Compare current period vs previous period to compute growth rate
    - Determine dominant issue category and average priority
    - Compute density and assign Hotspot Level (LOW, MODERATE, HIGH, SEVERE)
    """

    EARTH_RADIUS_METERS = 6371000

    def detect_hotspots(
        self,
        issues: List[Issue],
        period_days: int = 14,
        eps_meters: float = 400.0,
        min_samples: int = 2
    ) -> List[HotspotInfo]:
        if not issues:
            return []

        now = datetime.now(timezone.utc)
        current_cutoff = now - timedelta(days=period_days)
        previous_cutoff = now - timedelta(days=period_days * 2)

        # Segment issues into current period and previous period
        current_period_issues: List[Issue] = []
        previous_period_issues: List[Issue] = []

        for issue in issues:
            try:
                # Parse timestamp
                ts = datetime.fromisoformat(issue.timestamp.replace("Z", "+00:00"))
                if ts >= current_cutoff:
                    current_period_issues.append(issue)
                elif ts >= previous_cutoff:
                    previous_period_issues.append(issue)
                else:
                    current_period_issues.append(issue)  # Include baseline issues in current period if historical
            except Exception:
                current_period_issues.append(issue)

        if len(current_period_issues) < min_samples:
            return []

        # Convert coords to radians for Haversine DBSCAN
        coords = np.array([[math.radians(i.latitude), math.radians(i.longitude)] for i in current_period_issues])
        kms_per_radian = 6371.0
        eps_radians = (eps_meters / 1000.0) / kms_per_radian

        db = DBSCAN(eps=eps_radians, min_samples=min_samples, metric="haversine")
        labels = db.fit_predict(coords)

        hotspots: List[HotspotInfo] = []
        unique_labels = set(labels)

        for cluster_label in unique_labels:
            if cluster_label == -1:
                continue  # Noise points

            cluster_issues = [current_period_issues[idx] for idx, lbl in enumerate(labels) if lbl == cluster_label]
            cluster_lats = [i.latitude for i in cluster_issues]
            cluster_lngs = [i.longitude for i in cluster_issues]

            center_lat = float(np.mean(cluster_lats))
            center_lng = float(np.mean(cluster_lngs))

            # Compute radius in meters
            max_dist = 0.0
            for i in cluster_issues:
                d = self._haversine(center_lat, center_lng, i.latitude, i.longitude)
                if d > max_dist:
                    max_dist = d
            radius = max(round(max_dist, 1), 150.0)

            # Dominant Category
            cat_counts: Dict[str, int] = {}
            for i in cluster_issues:
                cat_val = i.category.value if hasattr(i.category, "value") else str(i.category)
                cat_counts[cat_val] = cat_counts.get(cat_val, 0) + 1
            dominant_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "General Civic Issue"

            # Average Priority
            avg_priority = round(float(np.mean([i.priorityScore for i in cluster_issues])), 1)

            # Growth rate: count issues in previous period within same radius
            prev_count = 0
            for pi in previous_period_issues:
                if self._haversine(center_lat, center_lng, pi.latitude, pi.longitude) <= radius:
                    prev_count += 1

            curr_count = len(cluster_issues)
            if prev_count > 0:
                growth_rate = round(((curr_count - prev_count) / float(prev_count)) * 100.0, 1)
            else:
                growth_rate = round(curr_count * 50.0, 1) if curr_count > 1 else 0.0

            # Density per km2
            area_km2 = math.pi * ((radius / 1000.0) ** 2)
            density = round(curr_count / area_km2, 1) if area_km2 > 0 else float(curr_count)

            # Hotspot Level
            if curr_count >= 5 or avg_priority >= 80.0:
                h_level = HotspotLevel.SEVERE
            elif curr_count >= 3 or avg_priority >= 70.0:
                h_level = HotspotLevel.HIGH
            elif curr_count >= 2:
                h_level = HotspotLevel.MODERATE
            else:
                h_level = HotspotLevel.LOW

            cluster_id_str = f"HOTSPOT-MUM-{int(abs(center_lat)*1000):05d}-{int(abs(center_lng)*1000):05d}"

            hotspots.append(HotspotInfo(
                hotspotId=cluster_id_str,
                center=[round(center_lat, 4), round(center_lng, 4)],
                radius=radius,
                issueCount=curr_count,
                dominantCategory=dominant_cat,
                averagePriority=avg_priority,
                growthRate=growth_rate,
                hotspotLevel=h_level,
                densityPerKm2=density
            ))

        return hotspots

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

hotspot_detector = SpatiotemporalHotspotDetector()
