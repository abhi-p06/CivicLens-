import io
import re
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.guidance.registry import source_registry

logger = logging.getLogger(__name__)

class DocumentScraper:
    """
    Robust Ingestion Service for Official Government Guidance Documents.
    Collects public HTML and PDF documents, strips navigation/boilerplate,
    extracts structured sections, tracks publication metadata and SHA-256 hashes.
    """
    def __init__(self, timeout_sec: float = 10.0):
        self.timeout_sec = timeout_sec

    def hash_content(self, raw_bytes: bytes) -> str:
        """Returns deterministic SHA-256 checksum for document change detection."""
        return hashlib.sha256(raw_bytes).hexdigest()

    def compute_sha256(self, content: Any) -> str:
        """Helper computing SHA-256 for strings or bytes."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def clean_html(self, raw_html: str) -> str:
        """Cleans and extracts visible readable text from HTML markup."""
        extracted = self.extract_html(raw_html.encode("utf-8") if isinstance(raw_html, str) else raw_html, "http://localhost")
        return extracted.get("raw_text", "")

    def fetch_url(self, url: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """
        Safely fetches remote content from allowlisted government domain.
        Returns (content_bytes, content_type, error_message).
        """
        if not source_registry.is_url_allowed(url):
            return None, None, f"Domain not in official allowlist: {url}"

        domain = urlparse(url).netloc.lower().split(":")[0]
        source_registry.throttle_domain(domain)

        try:
            headers = {
                "User-Agent": "CIVILENS-Research-Ingestion/1.0 (+https://civilens.org/bot; civic research and official guideline verification)",
                "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
            }
            with httpx.Client(timeout=self.timeout_sec, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    content_type = resp.headers.get("content-type", "").lower()
                    return resp.content, content_type, None
                else:
                    return None, None, f"HTTP Error {resp.status_code}: {resp.reason_phrase}"
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching guidance URL: {url}")
            return None, None, f"Request timed out after {self.timeout_sec}s"
        except Exception as e:
            logger.error(f"Error fetching guidance URL {url}: {e}")
            return None, None, str(e)

    def extract_html(self, html_bytes: bytes, source_url: str) -> Dict[str, Any]:
        """
        Extracts clean text, structured sections, title, and metadata from HTML.
        Removes scripts, styles, header, footer, navigation bars.
        """
        soup = BeautifulSoup(html_bytes, "html.parser")

        # Strip unneeded boilerplate elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside", "svg", "form"]):
            tag.decompose()

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        if not title:
            title = f"Official Guidance from {urlparse(source_url).netloc}"

        # Clean text
        body = soup.find("main") or soup.find("article") or soup.find("body") or soup
        text = body.get_text(separator="\n", strip=True)

        # Extract structured headings & sections
        sections: List[Dict[str, Any]] = []
        heading_tags = soup.find_all(["h1", "h2", "h3", "h4"])
        for i, h in enumerate(heading_tags):
            sec_title = h.get_text(strip=True)
            if not sec_title:
                continue

            sec_content = []
            curr = h.next_sibling
            while curr and getattr(curr, "name", None) not in ["h1", "h2", "h3", "h4"]:
                if hasattr(curr, "get_text"):
                    t = curr.get_text(strip=True)
                    if t:
                        sec_content.append(t)
                curr = curr.next_sibling

            content_text = " ".join(sec_content)
            sections.append({
                "section_id": f"sec-{i+1}",
                "section_title": sec_title,
                "content": content_text or sec_title,
                "page_number": 1,
            })

        return {
            "title": title,
            "raw_text": text,
            "sections": sections,
            "content_type": "text/html",
        }

    def extract_pdf(self, pdf_bytes: bytes, source_url: str) -> Dict[str, Any]:
        """
        Extracts text, page numbers, and sections from PDF documents.
        Uses pypdf or PyMuPDF (fitz) with graceful fallback.
        """
        text_pages: List[str] = []
        sections: List[Dict[str, Any]] = []

        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            title = reader.metadata.title if reader.metadata and reader.metadata.title else ""

            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text_pages.append(page_text)

                # Identify potential sections
                lines = [l.strip() for l in page_text.splitlines() if l.strip()]
                for line in lines:
                    if re.match(r"^(Section|Clause|Rule|Chapter|\d+\.|\d+\.\d+)\s+", line, re.IGNORECASE):
                        sections.append({
                            "section_id": f"p{page_idx+1}-sec-{len(sections)+1}",
                            "section_title": line[:120],
                            "content": page_text[:800],
                            "page_number": page_idx + 1,
                        })

        except Exception as e:
            logger.warning(f"pypdf extraction failed, attempting fallback: {e}")
            title = ""

        if not title:
            # Infer from first page or filename
            if text_pages and text_pages[0]:
                first_lines = [l for l in text_pages[0].splitlines() if l.strip()]
                title = first_lines[0][:150] if first_lines else "Official Government Specification"
            else:
                title = f"Official Document ({urlparse(source_url).path.split('/')[-1] or 'PDF Document'})"

        full_text = "\n\n--- Page Break ---\n\n".join(text_pages)

        # If no heading matches found, create page-level sections
        if not sections and text_pages:
            for idx, ptxt in enumerate(text_pages):
                sections.append({
                    "section_id": f"p{idx+1}",
                    "section_title": f"Page {idx+1}",
                    "content": ptxt,
                    "page_number": idx + 1,
                })

        return {
            "title": title,
            "raw_text": full_text,
            "sections": sections,
            "content_type": "application/pdf",
        }

    def ingest_url(self, url: str) -> Dict[str, Any]:
        """
        Main entry point: fetches, detects content type, parses, and returns
        extracted document representation with SHA-256 hash.
        """
        content_bytes, content_type, err = self.fetch_url(url)
        if err or not content_bytes:
            return {
                "success": False,
                "url": url,
                "error": err or "No content returned",
            }

        file_hash = self.hash_content(content_bytes)

        if "pdf" in (content_type or "") or url.lower().endswith(".pdf"):
            extracted = self.extract_pdf(content_bytes, url)
        else:
            extracted = self.extract_html(content_bytes, url)

        domain = urlparse(url).netloc.lower()

        return {
            "success": True,
            "url": url,
            "source_domain": domain,
            "file_hash": file_hash,
            "title": extracted["title"],
            "raw_text": extracted["raw_text"],
            "sections": extracted["sections"],
            "content_type": extracted["content_type"],
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    async def fetch_and_parse(self, url: str) -> Dict[str, Any]:
        """Async compatibility wrapper for admin ingestion endpoint."""
        res = self.ingest_url(url)
        return {
            "is_successful": res.get("success", False),
            "error_message": res.get("error"),
            "title": res.get("title", ""),
            "raw_text": res.get("raw_text", ""),
            "summary": (res.get("raw_text", "") or "")[:300],
            "sections": res.get("sections", []),
            "file_hash": res.get("file_hash", ""),
            "content_type": res.get("content_type", "text/html"),
        }

# Global scraper instance
document_scraper = DocumentScraper()
