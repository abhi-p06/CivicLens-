import os
from typing import Dict, Any, Tuple, Optional
import cv2
import numpy as np
from PIL import Image

class SceneComparabilityEngine:
    """
    OpenCV-Powered Scene Comparability & Quality Engine.

    Evaluates whether two photographs (before repair vs after repair) represent
    the same geographic scene and are sufficiently aligned for computer-vision delta analysis.

    Metrics Calculated:
    1. Dimension & Aspect Ratio Compatibility (checks framing / orientation shifts)
    2. Color & Surface Tone Distribution via 2D HSV Histogram Correlation
    3. Structural Similarity Index (SSIM) on standardized grayscale representations
    4. Keypoint & Feature Matching via ORB (Oriented FAST and Rotated BRIEF)

    What SSIM Measures:
    - Structural Similarity (SSIM) quantifies the degradation/similarity of structural information
      between two images across luminance, contrast, and structural patterns.
    - SSIM ranges from -1.0 to +1.0 (normalized to [0.0, 1.0]).
    - In road maintenance, an identical scene with minor texture shifts typically yields SSIM 0.45–0.80.
    - Completely disparate viewpoints, different roads, or indoor scenes yield SSIM < 0.25.
    - SSIM is strictly SUPPORTING EVIDENCE for scene consistency, NEVER a standalone proof of repair.
    """

    def __init__(
        self,
        target_eval_size: Tuple[int, int] = (512, 512),
        min_comparability_threshold: float = 0.25,
        max_aspect_ratio_diff: float = 0.40
    ):
        self.target_eval_size = target_eval_size
        self.min_comparability_threshold = min_comparability_threshold
        self.max_aspect_ratio_diff = max_aspect_ratio_diff

    def compute_ssim(self, gray1: np.ndarray, gray2: np.ndarray) -> float:
        """
        Calculates Structural Similarity Index (SSIM) using local Gaussian windowing.
        Both inputs must be 2D float64 or uint8 arrays of identical dimensions.
        """
        img1 = gray1.astype(np.float64)
        img2 = gray2.astype(np.float64)

        # Standard SSIM constants (K1=0.01, K2=0.03, L=255)
        c1 = (0.01 * 255.0) ** 2
        c2 = (0.03 * 255.0) ** 2

        kernel = cv2.getGaussianKernel(11, 1.5)
        window = np.outer(kernel, kernel.transpose())

        mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]
        mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.filter2D(img1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
        sigma2_sq = cv2.filter2D(img2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
        sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

        numerator = (2.0 * mu1_mu2 + c1) * (2.0 * sigma12 + c2)
        denominator = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)

        ssim_map = numerator / (denominator + 1e-10)
        mean_ssim = float(np.clip(ssim_map.mean(), -1.0, 1.0))
        # Normalize [-1.0, 1.0] to [0.0, 1.0]
        return max(0.0, min(1.0, (mean_ssim + 1.0) / 2.0))

    def compute_histogram_correlation(self, bgr1: np.ndarray, bgr2: np.ndarray) -> float:
        """
        Computes 2D Hue-Saturation color histogram correlation in HSV space.
        Evaluates similarity in pavement tone, lighting condition, and ambient spectrum.
        """
        hsv1 = cv2.cvtColor(bgr1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(bgr2, cv2.COLOR_BGR2HSV)

        # 30 hue bins, 32 saturation bins
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [30, 32], [0, 180, 0, 256])

        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

        correlation = float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))
        # Bounded between 0.0 and 1.0
        return max(0.0, min(1.0, correlation))

    def compute_feature_match_ratio(self, gray1: np.ndarray, gray2: np.ndarray) -> Tuple[float, int]:
        """
        Extracts ORB keypoint descriptors and matches with Hamming distance.
        Returns (match_ratio, good_match_count).
        """
        orb = cv2.ORB_create(nfeatures=500)
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)

        if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
            return 0.0, 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        try:
            matches = bf.match(des1, des2)
            # Filter matches by distance threshold
            matches = sorted(matches, key=lambda x: x.distance)
            good_matches = [m for m in matches if m.distance < 60.0]
            min_kps = max(1, min(len(kp1), len(kp2)))
            ratio = float(min(1.0, len(good_matches) / min_kps))
            return ratio, len(good_matches)
        except Exception:
            return 0.0, 0

    def assess_comparability(
        self,
        image_path_1: str,
        image_path_2: str
    ) -> Dict[str, Any]:
        """
        Full scene comparability audit comparing two local image files.
        Returns dictionary containing comparability boolean, metrics, and explanatory reason.
        """
        if not os.path.exists(image_path_1) or not os.path.exists(image_path_2):
            return {
                "isComparable": False,
                "comparabilityScore": 0.0,
                "ssim": 0.0,
                "histogramCorrelation": 0.0,
                "featureMatchRatio": 0.0,
                "aspectRatioDiff": 1.0,
                "reason": "One or both image files do not exist on disk.",
                "qualityMetrics": {}
            }

        img1 = cv2.imread(image_path_1)
        img2 = cv2.imread(image_path_2)

        if img1 is None or img2 is None:
            return {
                "isComparable": False,
                "comparabilityScore": 0.0,
                "ssim": 0.0,
                "histogramCorrelation": 0.0,
                "featureMatchRatio": 0.0,
                "aspectRatioDiff": 1.0,
                "reason": "OpenCV failed to decode one or both image files.",
                "qualityMetrics": {}
            }

        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        ar1 = float(w1) / float(max(1, h1))
        ar2 = float(w2) / float(max(1, h2))
        ar_diff = abs(ar1 - ar2) / float(max(ar1, ar2))

        # Check aspect ratio compatibility
        if ar_diff > self.max_aspect_ratio_diff:
            return {
                "isComparable": False,
                "comparabilityScore": 0.10,
                "ssim": 0.0,
                "histogramCorrelation": 0.0,
                "featureMatchRatio": 0.0,
                "aspectRatioDiff": round(ar_diff, 3),
                "reason": f"Severe aspect ratio mismatch ({w1}x{h1} vs {w2}x{h2}). Camera framing or orientation is incompatible.",
                "qualityMetrics": {
                    "image1Dimensions": [w1, h1],
                    "image2Dimensions": [w2, h2],
                    "aspectRatio1": round(ar1, 2),
                    "aspectRatio2": round(ar2, 2)
                }
            }

        # Standardize grayscale frames for spatial and structural evaluation
        g1 = cv2.resize(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY), self.target_eval_size)
        g2 = cv2.resize(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY), self.target_eval_size)

        # 1. Structural Similarity
        ssim_val = self.compute_ssim(g1, g2)

        # 2. Color Tone Correlation
        hist_corr = self.compute_histogram_correlation(img1, img2)

        # 3. Feature Matching
        match_ratio, match_count = self.compute_feature_match_ratio(g1, g2)

        # Weighted composite comparability index (0.0 to 1.0)
        # Weights: 45% Color/Surface Histogram, 35% SSIM, 20% Feature keypoints
        composite_score = round(
            0.45 * hist_corr + 0.35 * ssim_val + 0.20 * min(1.0, match_ratio * 2.5),
            3
        )

        is_comparable = (composite_score >= self.min_comparability_threshold) and (ar_diff <= self.max_aspect_ratio_diff)

        if not is_comparable:
            reason = (
                f"Low scene comparability index ({composite_score:.2f} < {self.min_comparability_threshold:.2f}). "
                f"Camera viewpoint, lighting, or pavement context diverged significantly."
            )
        else:
            reason = (
                f"Scene alignment verified (comparability score: {composite_score:.2f}, SSIM: {ssim_val:.2f}, "
                f"color correlation: {hist_corr:.2f}). Images represent comparable viewpoints."
            )

        return {
            "isComparable": is_comparable,
            "comparabilityScore": composite_score,
            "ssim": round(ssim_val, 3),
            "histogramCorrelation": round(hist_corr, 3),
            "featureMatchRatio": round(match_ratio, 3),
            "featureMatchCount": match_count,
            "aspectRatioDiff": round(ar_diff, 3),
            "reason": reason,
            "qualityMetrics": {
                "image1Dimensions": [w1, h1],
                "image2Dimensions": [w2, h2],
                "aspectRatioDiff": round(ar_diff, 3)
            }
        }

scene_comparator = SceneComparabilityEngine()
