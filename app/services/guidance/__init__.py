"""
CIVILENS AI Field Guidance & Official Government Research Integration Module.
"""
from app.services.guidance.registry import (
    INITIAL_ALLOWLIST_SOURCES,
    is_domain_allowlisted,
    validate_source_url,
    GuidanceRateLimiter
)
from app.services.guidance.scraper import DocumentScraper
from app.services.guidance.knowledge_base import GuidanceKnowledgeBase
from app.services.guidance.guidance_engine import GuidanceEngine

__all__ = [
    "INITIAL_ALLOWLIST_SOURCES",
    "is_domain_allowlisted",
    "validate_source_url",
    "GuidanceRateLimiter",
    "DocumentScraper",
    "GuidanceKnowledgeBase",
    "GuidanceEngine"
]
