import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy import select, update, delete
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.db.database import get_db_session, init_db
from app.db.models import GuidanceSourceRecord, GuidanceDocumentRecord
from app.services.guidance.registry import INITIAL_ALLOWLIST_SOURCES
from app.services.guidance.seed_documents import get_seed_documents

logger = logging.getLogger(__name__)

class GuidanceKnowledgeBase:
    """
    Searchable Knowledge Base of Official Government Standards & Circulars.
    Implements TF-IDF vector ranking and category-filtered document retrieval.
    Excludes DRAFT and SUPERSEDED documents from authoritative guidance queries.
    """
    def __init__(self):
        init_db()

    def seed_if_empty(self) -> None:
        """Seeds initial allowlisted sources and official specifications if empty."""
        with get_db_session() as session:
            # Check sources
            existing_sources = session.scalars(select(GuidanceSourceRecord)).all()
            if not existing_sources:
                for s in INITIAL_ALLOWLIST_SOURCES:
                    record = GuidanceSourceRecord(
                        id=s["id"],
                        name=s["name"],
                        domain=s["domain"],
                        base_url=s["base_url"],
                        category=s["category"],
                        is_active=s.get("is_active", True),
                        is_allowlisted=s.get("is_allowlisted", True),
                        last_status="OK",
                        last_retrieved_at=datetime.now(timezone.utc),
                    )
                    session.add(record)
                session.commit()
                logger.info(f"Seeded {len(INITIAL_ALLOWLIST_SOURCES)} official guidance sources.")

            # Check documents
            existing_docs = session.scalars(select(GuidanceDocumentRecord)).all()
            if not existing_docs:
                seed_docs = get_seed_documents()
                for d in seed_docs:
                    record = GuidanceDocumentRecord(
                        id=d["id"],
                        source_id=d["source_id"],
                        source_domain=d["source_domain"],
                        source_org=d["source_org"],
                        title=d["title"],
                        url=d["url"],
                        publication_date=d["publication_date"],
                        document_version=d["document_version"],
                        document_status=d["document_status"],
                        applicable_category=d["applicable_category"],
                        content_type=d["content_type"],
                        file_hash=d["file_hash"],
                        raw_text=d["raw_text"],
                        summary=d["summary"],
                        sections_json=d["sections_json"],
                        is_approved=d["is_approved"],
                        last_retrieved_at=datetime.now(timezone.utc),
                    )
                    session.add(record)
                session.commit()
                logger.info(f"Seeded {len(seed_docs)} authoritative guidance documents.")

    def search_sections(
        self,
        query: str,
        category: str,
        allowed_statuses: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant sections matching query and complaint category.
        Filters strictly by document_status (default: only CURRENT).
        """
        if allowed_statuses is None:
            allowed_statuses = ["CURRENT"]

        with get_db_session() as session:
            # Query approved documents matching category or generic
            stmt = select(GuidanceDocumentRecord).where(
                GuidanceDocumentRecord.is_approved == True,
                GuidanceDocumentRecord.document_status.in_(allowed_statuses)
            )
            if category:
                stmt = stmt.where(
                    (GuidanceDocumentRecord.applicable_category == category) |
                    (GuidanceDocumentRecord.applicable_category == "ALL")
                )

            docs = session.scalars(stmt).all()

            if not docs:
                return []

            # Flatten sections
            all_sections: List[Dict[str, Any]] = []
            for doc in docs:
                try:
                    sections = json.loads(doc.sections_json)
                except Exception:
                    sections = []

                for sec in sections:
                    all_sections.append({
                        "doc_id": doc.id,
                        "doc_title": doc.title,
                        "source_org": doc.source_org,
                        "source_domain": doc.source_domain,
                        "url": doc.url,
                        "document_version": doc.document_version,
                        "document_status": doc.document_status,
                        "section_id": sec.get("section_id", ""),
                        "section_title": sec.get("section_title", ""),
                        "page_number": sec.get("page_number", 1),
                        "content": sec.get("content", ""),
                        "is_statutory": sec.get("is_statutory", True),
                    })

            if not all_sections:
                return []

            # TF-IDF Ranking
            corpus = [f"{s['section_title']} {s['content']}" for s in all_sections]
            try:
                vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
                tfidf_matrix = vectorizer.fit_transform(corpus)
                query_vec = vectorizer.transform([query])
                scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

                ranked_indices = np.argsort(scores)[::-1]
                results = []
                for idx in ranked_indices[:top_k]:
                    item = dict(all_sections[idx])
                    item["relevance_score"] = float(scores[idx])
                    results.append(item)
                return results
            except Exception as e:
                logger.warning(f"TF-IDF search fallback: {e}")
                return all_sections[:top_k]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Returns document by ID."""
        with get_db_session() as session:
            doc = session.get(GuidanceDocumentRecord, doc_id)
            if not doc:
                return None
            return {
                "id": doc.id,
                "source_id": doc.source_id,
                "source_domain": doc.source_domain,
                "source_org": doc.source_org,
                "title": doc.title,
                "url": doc.url,
                "publication_date": doc.publication_date,
                "document_version": doc.document_version,
                "document_status": doc.document_status,
                "applicable_category": doc.applicable_category,
                "content_type": doc.content_type,
                "file_hash": doc.file_hash,
                "summary": doc.summary,
                "sections": json.loads(doc.sections_json) if doc.sections_json else [],
                "raw_text": doc.raw_text,
                "is_approved": doc.is_approved,
                "last_retrieved_at": doc.last_retrieved_at.isoformat() if doc.last_retrieved_at else None,
            }

    def list_documents(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists documents with optional category or status filters."""
        with get_db_session() as session:
            stmt = select(GuidanceDocumentRecord)
            if category:
                stmt = stmt.where(GuidanceDocumentRecord.applicable_category == category)
            if status:
                stmt = stmt.where(GuidanceDocumentRecord.document_status == status)

            docs = session.scalars(stmt.order_by(GuidanceDocumentRecord.created_at.desc())).all()
            return [
                {
                    "id": d.id,
                    "source_id": d.source_id,
                    "source_domain": d.source_domain,
                    "source_org": d.source_org,
                    "title": d.title,
                    "url": d.url,
                    "publication_date": d.publication_date,
                    "document_version": d.document_version,
                    "document_status": d.document_status,
                    "applicable_category": d.applicable_category,
                    "content_type": d.content_type,
                    "file_hash": d.file_hash,
                    "summary": d.summary,
                    "sections_count": len(json.loads(d.sections_json)) if d.sections_json else 0,
                    "is_approved": d.is_approved,
                    "last_retrieved_at": d.last_retrieved_at.isoformat() if d.last_retrieved_at else None,
                }
                for d in docs
            ]

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates document status or approval flag."""
        with get_db_session() as session:
            doc = session.get(GuidanceDocumentRecord, doc_id)
            if not doc:
                return None

            if "document_status" in updates and updates["document_status"]:
                doc.document_status = updates["document_status"]
            if "is_approved" in updates and updates["is_approved"] is not None:
                doc.is_approved = updates["is_approved"]

            doc.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self.get_document(doc_id)

    def list_sources(self) -> List[Dict[str, Any]]:
        """Returns all registered official sources."""
        with get_db_session() as session:
            sources = session.scalars(select(GuidanceSourceRecord).order_by(GuidanceSourceRecord.name)).all()
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "domain": s.domain,
                    "base_url": s.base_url,
                    "category": s.category,
                    "is_active": s.is_active,
                    "is_allowlisted": s.is_allowlisted,
                    "last_status": s.last_status,
                    "last_retrieved_at": s.last_retrieved_at.isoformat() if s.last_retrieved_at else None,
                    "error_message": s.error_message,
                }
                for s in sources
            ]

    def update_source(self, source_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates source status or category."""
        with get_db_session() as session:
            s = session.get(GuidanceSourceRecord, source_id)
            if not s:
                return None

            if "is_active" in updates and updates["is_active"] is not None:
                s.is_active = updates["is_active"]
            if "category" in updates and updates["category"]:
                s.category = updates["category"]
            if "last_status" in updates and updates["last_status"]:
                s.last_status = updates["last_status"]
            if "error_message" in updates:
                s.error_message = updates["error_message"]
            if "last_retrieved_at" in updates:
                s.last_retrieved_at = updates["last_retrieved_at"]

            s.updated_at = datetime.now(timezone.utc)
            session.commit()
            return {
                "id": s.id,
                "name": s.name,
                "domain": s.domain,
                "base_url": s.base_url,
                "category": s.category,
                "is_active": s.is_active,
                "is_allowlisted": s.is_allowlisted,
                "last_status": s.last_status,
                "last_retrieved_at": s.last_retrieved_at.isoformat() if s.last_retrieved_at else None,
                "error_message": s.error_message,
            }

    def save_ingested_document(
        self,
        doc_data: Dict[str, Any],
        source_id: str,
        category: str,
        version: str = "Ingested-V1"
    ) -> Dict[str, Any]:
        """
        Saves or updates an ingested document in the knowledge base.
        If content hash changed, marks old document as SUPERSEDED and creates a new CURRENT record.
        """
        with get_db_session() as session:
            existing = session.scalars(
                select(GuidanceDocumentRecord).where(GuidanceDocumentRecord.url == doc_data["url"])
            ).first()

            if existing:
                if existing.file_hash == doc_data["file_hash"]:
                    existing.last_retrieved_at = datetime.now(timezone.utc)
                    session.commit()
                    return self.get_document(existing.id)  # type: ignore

                # Content changed: supersede existing
                existing.document_status = "SUPERSEDED"
                existing.updated_at = datetime.now(timezone.utc)

            new_id = f"DOC-{doc_data['source_domain'].replace('.', '-').upper()}-{int(datetime.now(timezone.utc).timestamp())}-{uuid.uuid4().hex[:6]}"
            record = GuidanceDocumentRecord(
                id=new_id,
                source_id=source_id,
                source_domain=doc_data["source_domain"],
                source_org=doc_data.get("source_org", doc_data["source_domain"]),
                title=doc_data["title"],
                url=doc_data["url"],
                publication_date=datetime.now().strftime("%Y-%m-%d"),
                document_version=version,
                document_status="CURRENT",
                applicable_category=category,
                content_type=doc_data.get("content_type", "text/html"),
                file_hash=doc_data["file_hash"],
                raw_text=doc_data["raw_text"],
                summary=doc_data["raw_text"][:300],
                sections_json=json.dumps(doc_data.get("sections", [])),
                is_approved=True,
                last_retrieved_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            return self.get_document(new_id)  # type: ignore

# Global knowledge base singleton
guidance_kb = GuidanceKnowledgeBase()
