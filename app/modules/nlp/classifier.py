import re
from typing import Tuple
from app.models.issue import IssueCategory

class ComplaintNLPClassifier:
    """
    Interface for Complaint Text Classification, Urgency Detection, and Text Severity.
    Supports pluggable ML models (e.g. TF-IDF + Classifier, BERT) with rule-based heuristic fallbacks.
    """
    
    KEYWORD_CATEGORY_MAP = {
        IssueCategory.ROAD_DAMAGE: ["pothole", "crater", "road", "tar", "footpath", "divider", "asphalt", "skid"],
        IssueCategory.SANITATION: ["garbage", "trash", "waste", "stench", "dump", "bin", "filth", "debris"],
        IssueCategory.WATER_SUPPLY: ["water", "leak", "pipe", "drain", "sewage", "flooding", "potable", "burst"],
        IssueCategory.ELECTRICAL: ["light", "streetlight", "electric", "pole", "wire", "spark", "dark", "shock"],
        IssueCategory.TRAFFIC_SAFETY: ["traffic", "signal", "accident", "zebra", "speed breaker", "jam", "collision"]
    }

    URGENCY_KEYWORDS = {
        "critical": ["accident", "death", "injury", "injured", "skidded", "fallen", "burst", "life threatening", "collapsed", "live wire"],
        "high": ["dangerous", "hazard", "immediate", "terrible", "school", "hospital", "flooding", "blocked"],
        "moderate": ["delay", "inconvenience", "stench", "dark", "damaged", "broken"]
    }

    def predict_category(self, text: str) -> IssueCategory:
        text_lower = text.lower()
        for cat, keywords in self.KEYWORD_CATEGORY_MAP.items():
            if any(k in text_lower for k in keywords):
                return cat
        return IssueCategory.UNSPECIFIED

    def calculate_urgency(self, text: str) -> float:
        text_lower = text.lower()
        score = 0.35  # baseline urgency
        for kw in self.URGENCY_KEYWORDS["critical"]:
            if kw in text_lower:
                score += 0.40
                break
        for kw in self.URGENCY_KEYWORDS["high"]:
            if kw in text_lower:
                score += 0.20
                break
        for kw in self.URGENCY_KEYWORDS["moderate"]:
            if kw in text_lower:
                score += 0.10
                break
        return min(round(score, 2), 1.0)

    def calculate_severity(self, text: str, category: IssueCategory) -> float:
        urgency = self.calculate_urgency(text)
        # Severity reflects structural magnitude
        severity = round(0.40 + 0.50 * urgency, 2)
        return min(severity, 1.0)

    def analyze(self, text: str) -> Tuple[IssueCategory, float, float]:
        cat = self.predict_category(text)
        urg = self.calculate_urgency(text)
        sev = self.calculate_severity(text, cat)
        return cat, urg, sev

nlp_classifier = ComplaintNLPClassifier()
