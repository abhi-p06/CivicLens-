import math
from datetime import datetime, timezone
from typing import List, Optional
from app.models.issue import Issue, RecurrenceInfo, RecurrenceTrend, IssueCategory

class RecurringIssueDetector:
    """
    Feature 17: Recurring Issue Detection
    
    Distinct from duplicate detection:
    - Duplicate: Same physical incident reported multiple times simultaneously.
    - Recurring: Same category/infrastructure defect repeatedly occurring at a location over time.
    
    Returns:
    - recurringIssue: bool
    - location: str
    - category: str
    - reportCount: int
    - firstReported: str
    - lastReported: str
    - recurrenceScore: float (0.0 to 1.0)
    - trend: INCREASING, STABLE, DECREASING
    """

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def evaluate_recurrence(
        self,
        lat: float,
        lng: float,
        category: IssueCategory,
        location_name: str,
        existing_issues: List[Issue],
        radius_meters: float = 300.0
    ) -> RecurrenceInfo:
        if not existing_issues:
            now_iso = datetime.now(timezone.utc).isoformat()
            return RecurrenceInfo(
                recurringIssue=False,
                location=location_name,
                category=category.value if hasattr(category, "value") else str(category),
                reportCount=1,
                firstReported=now_iso,
                lastReported=now_iso,
                recurrenceScore=0.10,
                trend=RecurrenceTrend.STABLE
            )

        # Match prior issues of the SAME category within spatial radius
        matched_history: List[Issue] = []
        for issue in existing_issues:
            dist = self.haversine_distance_meters(lat, lng, issue.latitude, issue.longitude)
            if dist <= radius_meters and issue.category == category:
                matched_history.append(issue)

        total_count = len(matched_history) + 1
        is_recurring = total_count >= 2

        # Sort historical timestamps
        timestamps = []
        for i in matched_history:
            try:
                ts = datetime.fromisoformat(i.timestamp.replace("Z", "+00:00"))
                timestamps.append((ts, i.timestamp))
            except Exception:
                pass

        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        if timestamps:
            timestamps.sort(key=lambda x: x[0])
            first_reported = timestamps[0][1]
            last_reported = now_iso
            
            # Trend calculation
            if len(timestamps) >= 3:
                # Compare intervals between reports
                intervals = [(timestamps[i+1][0] - timestamps[i][0]).total_seconds() for i in range(len(timestamps)-1)]
                if len(intervals) >= 2 and intervals[-1] < intervals[0] * 0.7:
                    trend = RecurrenceTrend.INCREASING
                elif len(intervals) >= 2 and intervals[-1] > intervals[0] * 1.3:
                    trend = RecurrenceTrend.DECREASING
                else:
                    trend = RecurrenceTrend.STABLE
            else:
                trend = RecurrenceTrend.INCREASING if total_count >= 3 else RecurrenceTrend.STABLE
        else:
            first_reported = now_iso
            last_reported = now_iso
            trend = RecurrenceTrend.STABLE

        # Recurrence Score [0.0 to 1.0]
        rec_score = min(0.20 + (total_count * 0.20), 1.0)

        return RecurrenceInfo(
            recurringIssue=is_recurring,
            location=location_name,
            category=category.value if hasattr(category, "value") else str(category),
            reportCount=total_count,
            firstReported=first_reported,
            lastReported=last_reported,
            recurrenceScore=round(rec_score, 2),
            trend=trend
        )

recurring_detector = RecurringIssueDetector()
