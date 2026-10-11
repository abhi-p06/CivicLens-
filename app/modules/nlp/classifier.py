import re
from typing import Tuple, Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from app.models.issue import IssueCategory

# Representative civic training samples
CIVIC_TRAINING_CORPUS = [
    # Road damage & footpaths
    ("huge pothole in the middle of the road cars getting damaged", IssueCategory.ROAD_DAMAGE),
    ("broken asphalt and deep craters near signal vehicles skidding", IssueCategory.ROAD_DAMAGE),
    ("footpath tiles completely broken pedestrians forced to walk on road", IssueCategory.ROAD_DAMAGE),
    ("road tar washed away after rain uneven surface causing accidents", IssueCategory.ROAD_DAMAGE),
    ("damaged road divider broken concrete blocks lying on street", IssueCategory.ROAD_DAMAGE),
    ("dangerous trench dug for cables left open on main street", IssueCategory.ROAD_DAMAGE),

    # Sanitation & Garbage
    ("overflowing garbage bin waste scattered all across pavement", IssueCategory.SANITATION),
    ("garbage truck did not arrive for three days terrible stench", IssueCategory.SANITATION),
    ("illegal garbage dumping site creating fly infestation and health hazard", IssueCategory.SANITATION),
    ("dead animal rotting on roadside need urgent clearance", IssueCategory.SANITATION),
    ("plastic waste and trash choking roadside gutter", IssueCategory.SANITATION),
    ("foul smell from open public dustbin near residential colony", IssueCategory.SANITATION),

    # Water Supply & Drainage
    ("drinking water pipeline burst gallons of water flooding road", IssueCategory.WATER_SUPPLY),
    ("contaminated muddy water coming from municipal supply taps", IssueCategory.WATER_SUPPLY),
    ("underground sewer line choked manhole overflowing dirty sewage", IssueCategory.WATER_SUPPLY),
    ("storm water drain blocked causing waterlogging during rain", IssueCategory.WATER_SUPPLY),
    ("water leakage from main supply valve zero pressure in houses", IssueCategory.WATER_SUPPLY),
    ("open manhole cover missing on road severe danger of falling in drain", IssueCategory.WATER_SUPPLY),

    # Electricity & Streetlights
    ("streetlights not functioning whole street pitch dark at night", IssueCategory.ELECTRICAL),
    ("live wire hanging dangerously from electric pole sparking in rain", IssueCategory.ELECTRICAL),
    ("electric transformer box open and burning smell coming out", IssueCategory.ELECTRICAL),
    ("lamp post knocked down by truck wires exposed on ground", IssueCategory.ELECTRICAL),
    ("power fluctuations and street lamps flickering continuously", IssueCategory.ELECTRICAL),

    # Traffic & Safety
    ("traffic signal not working heavy jam at major intersection", IssueCategory.TRAFFIC_SAFETY),
    ("missing zebra crossing and pedestrian signal near school zone", IssueCategory.TRAFFIC_SAFETY),
    ("illegal parking blocking entire road causing massive bottleneck", IssueCategory.TRAFFIC_SAFETY),
    ("speed breaker paint worn out speeding vehicles causing accidents", IssueCategory.TRAFFIC_SAFETY)
]

class ComplaintNLPClassifier:
    """
    Multimodal Text Analytics Engine:
    - Real scikit-learn TF-IDF + Logistic Regression classification
    - Urgency scoring with hazard lexicon evaluation
    - Text severity scoring
    - Fully decoupled from UI with explicit executionMode logging
    """

    URGENCY_KEYWORDS = {
        "critical": ["accident", "death", "injury", "injured", "skidded", "fallen", "burst", "life threatening", "collapsed", "live wire", "open manhole"],
        "high": ["dangerous", "hazard", "immediate", "terrible", "school", "hospital", "flooding", "blocked", "overflowing", "sparking"],
        "moderate": ["delay", "inconvenience", "stench", "dark", "damaged", "broken", "pothole"]
    }

    def __init__(self):
        self._pipeline = None
        self._init_real_model()

    def _init_real_model(self):
        try:
            texts = [item[0] for item in CIVIC_TRAINING_CORPUS]
            labels = [item[1].value for item in CIVIC_TRAINING_CORPUS]
            self._pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words="english")),
                ("clf", LogisticRegression(C=5.0, max_iter=200, random_state=42))
            ])
            self._pipeline.fit(texts, labels)
            self._real_model_ready = True
        except Exception:
            self._real_model_ready = False

    def predict_category(self, text: str) -> Tuple[IssueCategory, float, str]:
        """
        Returns (predicted_category, confidence_score, execution_mode)
        """
        if not text or len(text.strip()) < 3:
            return IssueCategory.UNSPECIFIED, 0.0, "demo_fallback"

        # 1. Real ML Inference
        if self._real_model_ready and self._pipeline is not None:
            try:
                probs = self._pipeline.predict_proba([text])[0]
                classes = self._pipeline.classes_
                best_idx = probs.argmax()
                confidence = float(probs[best_idx])
                best_class = classes[best_idx]
                
                # If ML confidence is reasonable, use real ML prediction
                if confidence >= 0.25:
                    return IssueCategory(best_class), round(confidence, 2), "real_ml"
            except Exception:
                pass

        # 2. Deterministic Keyword Fallback
        text_lower = text.lower()
        keyword_map = {
            IssueCategory.ROAD_DAMAGE: ["pothole", "crater", "road", "tar", "footpath", "divider", "asphalt", "skid"],
            IssueCategory.SANITATION: ["garbage", "trash", "waste", "stench", "dump", "bin", "filth", "debris"],
            IssueCategory.STORM_WATER: ["culvert", "storm water", "stormwater", "nullah", "nalah", "storm drain"],
            IssueCategory.WATER_SUPPLY: ["water", "leak", "pipe", "drain", "sewage", "flooding", "potable", "burst", "manhole"],
            IssueCategory.ELECTRICAL: ["light", "streetlight", "electric", "pole", "wire", "spark", "dark"],
            IssueCategory.TRAFFIC_SAFETY: ["traffic", "signal", "accident", "zebra", "speed breaker", "jam"]
        }
        for cat, kws in keyword_map.items():
            if any(k in text_lower for k in kws):
                return cat, 0.85, "demo_fallback"

        return IssueCategory.UNSPECIFIED, 0.40, "demo_fallback"

    def calculate_urgency(self, text: str) -> Tuple[float, List[str]]:
        """
        Returns (urgency_score in [0.0, 1.0], detected_cues)
        """
        text_lower = text.lower()
        score = 0.35  # base civic urgency
        cues = []
        for kw in self.URGENCY_KEYWORDS["critical"]:
            if kw in text_lower:
                score += 0.40
                cues.append(kw)
                break
        for kw in self.URGENCY_KEYWORDS["high"]:
            if kw in text_lower:
                score += 0.20
                cues.append(kw)
                break
        for kw in self.URGENCY_KEYWORDS["moderate"]:
            if kw in text_lower:
                score += 0.10
                cues.append(kw)
                break
        return min(round(score, 2), 1.0), cues

    def calculate_severity(self, text: str, urgency: float, category: IssueCategory) -> float:
        """
        Severity reflects the physical magnitude and danger profile
        """
        base_severity = 0.40
        if category in [IssueCategory.ROAD_DAMAGE, IssueCategory.WATER_SUPPLY, IssueCategory.STORM_WATER]:
            base_severity = 0.50
        severity = base_severity + (0.50 * urgency)
        return min(round(severity, 2), 1.0)

    def analyze(self, text: str) -> Dict[str, Any]:
        category, confidence, mode = self.predict_category(text)
        urgency, cues = self.calculate_urgency(text)
        severity = self.calculate_severity(text, urgency, category)
        return {
            "category": category,
            "categoryConfidence": confidence,
            "classificationMode": mode,
            "urgency": urgency,
            "urgencyCues": cues,
            "severity": severity
        }

nlp_classifier = ComplaintNLPClassifier()
