import re
import time
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import urllib.robotparser

logger = logging.getLogger(__name__)

INITIAL_ALLOWLIST_SOURCES = [
    {
        "id": "SRC-MORTH-01",
        "name": "Ministry of Road Transport and Highways (MoRTH)",
        "domain": "morth.nic.in",
        "base_url": "https://morth.nic.in",
        "category": "Roads & Footpaths",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-MCGM-01",
        "name": "Municipal Corporation of Greater Mumbai (MCGM / BMC)",
        "domain": "mcgm.gov.in",
        "base_url": "https://mcgm.gov.in",
        "category": "ALL",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-MCGM-PORTAL-02",
        "name": "MCGM Citizen Portal & Works Manual",
        "domain": "portal.mcgm.gov.in",
        "base_url": "https://portal.mcgm.gov.in",
        "category": "ALL",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-MPCB-01",
        "name": "Maharashtra Pollution Control Board (MPCB)",
        "domain": "mpcb.gov.in",
        "base_url": "https://mpcb.gov.in",
        "category": "Sanitation & Garbage",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-CPCB-01",
        "name": "Central Pollution Control Board (CPCB)",
        "domain": "cpcb.nic.in",
        "base_url": "https://cpcb.nic.in",
        "category": "Sanitation & Garbage",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-CPHEEO-01",
        "name": "Central Public Health & Environmental Engineering Organisation (CPHEEO)",
        "domain": "cpheeo.gov.in",
        "base_url": "https://cpheeo.gov.in",
        "category": "Sanitation & Garbage",
        "is_allowlisted": True,
        "is_active": True,
    },
    {
        "id": "SRC-MOEF-01",
        "name": "Ministry of Environment, Forest & Climate Change (MoEF&CC)",
        "domain": "moef.gov.in",
        "base_url": "https://moef.gov.in",
        "category": "Sanitation & Garbage",
        "is_allowlisted": True,
        "is_active": True,
    },
]

DISALLOWED_PATTERNS = [
    r"reddit\.com",
    r"quora\.com",
    r"facebook\.com",
    r"twitter\.com",
    r"x\.com",
    r"instagram\.com",
    r"wordpress\.com",
    r"blogspot\.com",
    r"medium\.com",
    r"ad\.",
    r"doubleclick\.",
    r"contractorblog",
]

class SourceRegistry:
    """
    Controlled Allowlist Registry of Official Government Sources.
    Ensures CIVILENS scrapes and references strictly verified official public entities.
    """
    def __init__(self, allowed_domains: Optional[List[str]] = None):
        self._allowed_domains = set(
            allowed_domains or [s["domain"] for s in INITIAL_ALLOWLIST_SOURCES]
        )
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last_request_times: Dict[str, float] = {}
        self._min_request_interval_sec: float = 1.0

    def is_url_allowed(self, url: str) -> bool:
        """
        Validates if URL belongs strictly to a registered and allowlisted government domain.
        Rejects arbitrary forums, blogs, commercial ads, and non-allowlisted sites.
        """
        if not url or not isinstance(url, str):
            return False

        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower().split(":")[0]

        if not domain:
            return False

        # Reject any blacklisted forum / ad / social pattern
        for pat in DISALLOWED_PATTERNS:
            if re.search(pat, domain, re.IGNORECASE):
                logger.warning(f"Rejected commercial/forum URL pattern: {url}")
                return False

        # Must end with or exactly match an allowlisted domain
        for allowed in self._allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return True

        logger.warning(f"URL domain '{domain}' not in government allowlist.")
        return False

    def add_allowed_domain(self, domain: str) -> None:
        """Allows administrator to register a new verified government source."""
        clean_domain = domain.strip().lower()
        if clean_domain:
            self._allowed_domains.add(clean_domain)

    def remove_allowed_domain(self, domain: str) -> None:
        """Removes a domain from the active allowlist."""
        clean_domain = domain.strip().lower()
        self._allowed_domains.discard(clean_domain)

    def get_allowed_domains(self) -> List[str]:
        return sorted(list(self._allowed_domains))

    def throttle_domain(self, domain: str) -> None:
        """Enforces a gentle rate-limit interval to respect government web servers."""
        last_time = self._last_request_times.get(domain, 0.0)
        elapsed = time.time() - last_time
        if elapsed < self._min_request_interval_sec:
            time.sleep(self._min_request_interval_sec - elapsed)
        self._last_request_times[domain] = time.time()

# Global registry instance
source_registry = SourceRegistry()

def is_domain_allowlisted(domain: str) -> bool:
    clean = domain.strip().lower()
    for allowed in source_registry.get_allowed_domains():
        if clean == allowed or clean.endswith("." + allowed):
            return True
    return False

def validate_source_url(url: str) -> tuple[bool, str, Optional[str]]:
    if not url:
        return False, "", "URL is required"
    parsed = urlparse(url)
    domain = (parsed.netloc or "").lower().split(":")[0]
    if not domain:
        return False, "", "Invalid URL format"
    if not source_registry.is_url_allowed(url):
        return False, domain, f"Domain '{domain}' is not in the approved government allowlist."
    return True, domain, None

# Alias for backward-compatibility
GuidanceRateLimiter = SourceRegistry
