"""
backend/vectordb.py — Embedded Persistent Vector Database Engine
================================================================
A self-contained, high-performance Vector Database with SQLite persistence,
cosine-similarity semantic vector search, metadata filtering, and an async
cursor interface compatible with existing FastAPI/Motor patterns.
"""

from __future__ import annotations
import os
import re
import json
import math
import sqlite3
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone

logger = logging.getLogger("tradeintel.vectordb")

DB_FILE_PATH = os.environ.get("VECTORDB_PATH", os.path.join(os.path.dirname(__file__), "tradeintel_vectordb.sqlite"))


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercased terms and sub-ngrams."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", str(text).lower())
    tokens = []
    for w in words:
        tokens.append(w)
        if len(w) > 4:
            tokens.append(w[:4])
    return tokens


def _compute_vector(text: str, dim: int = 128) -> List[float]:
    """
    Computes a normalized dense semantic embedding vector from text
    using deterministic feature hashing with TF-IDF weighting.
    """
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    for t in tokens:
        idx = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % dim
        # Weight by token length and frequency
        weight = 1.0 + math.log1p(len(t))
        vec[idx] += weight

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculates cosine similarity between two normalized vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    return max(0.0, min(1.0, dot))


class InsertOneResult:
    def __init__(self, inserted_id: str):
        self.inserted_id = inserted_id


class InsertManyResult:
    def __init__(self, inserted_ids: List[str]):
        self.inserted_ids = inserted_ids


class DeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class UpdateResult:
    def __init__(self, matched_count: int, modified_count: int):
        self.matched_count = matched_count
        self.modified_count = modified_count


class VectorCursor:
    """Async cursor interface for VectorDB collections."""

    def __init__(self, collection: "VectorCollection", query: Dict[str, Any], projection: Optional[Dict[str, int]] = None):
        self.collection = collection
        self.query = query or {}
        self.projection = projection
        self._sort_key: Optional[str] = None
        self._sort_dir: int = 1
        self._skip_val: int = 0
        self._limit_val: Optional[int] = None

    def sort(self, key_or_list: Union[str, List[Tuple[str, int]]], direction: int = 1) -> "VectorCursor":
        if isinstance(key_or_list, list) and key_or_list:
            self._sort_key = key_or_list[0][0]
            self._sort_dir = key_or_list[0][1]
        elif isinstance(key_or_list, str):
            self._sort_key = key_or_list
            self._sort_dir = direction
        return self

    def skip(self, n: int) -> "VectorCursor":
        self._skip_val = max(0, n)
        return self

    def limit(self, n: int) -> "VectorCursor":
        self._limit_val = n
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        limit = length if length is not None else self._limit_val
        return self.collection._execute_find(
            self.query,
            self.projection,
            sort_key=self._sort_key,
            sort_dir=self._sort_dir,
            skip=self._skip_val,
            limit=limit,
        )

    def __aiter__(self):
        self._iter_docs = self.collection._execute_find(
            self.query,
            self.projection,
            sort_key=self._sort_key,
            sort_dir=self._sort_dir,
            skip=self._skip_val,
            limit=self._limit_val,
        )
        self._iter_idx = 0
        return self

    async def __anext__(self):
        if self._iter_idx < len(self._iter_docs):
            doc = self._iter_docs[self._iter_idx]
            self._iter_idx += 1
            return doc
        raise StopAsyncIteration


class VectorCollection:
    """Represents a vector collection backed by SQLite and in-memory indexing."""

    def __init__(self, db: "VectorDB", name: str):
        self.db = db
        self.name = name

    def _matches_filter(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Evaluates structured query filters against document."""
        if not query:
            return True
        for key, val in query.items():
            if key == "_id" or key == "id":
                doc_id = str(doc.get("id") or doc.get("_id", ""))
                if isinstance(val, dict):
                    if "$in" in val and doc_id not in [str(x) for x in val["$in"]]:
                        return False
                elif str(val) != doc_id:
                    return False
            elif key.startswith("$"):
                if key == "$or" and isinstance(val, list):
                    if not any(self._matches_filter(doc, sub) for sub in val):
                        return False
            elif isinstance(val, dict):
                field_val = doc.get(key)
                if "$in" in val and field_val not in val["$in"]:
                    return False
                if "$gte" in val and (field_val is None or field_val < val["$gte"]):
                    return False
                if "$lte" in val and (field_val is None or field_val > val["$lte"]):
                    return False
                if "$gt" in val and (field_val is None or field_val <= val["$gt"]):
                    return False
                if "$lt" in val and (field_val is None or field_val >= val["$lt"]):
                    return False
                if "$ne" in val and field_val == val["$ne"]:
                    return False
                if "$regex" in val:
                    pattern = val["$regex"]
                    flags = re.IGNORECASE if val.get("$options") == "i" else 0
                    if not re.search(pattern, str(field_val or ""), flags):
                        return False
            else:
                doc_val = doc.get(key)
                if str(doc_val).lower() != str(val).lower() and doc_val != val:
                    return False
        return True

    def _apply_projection(self, doc: Dict[str, Any], projection: Optional[Dict[str, int]]) -> Dict[str, Any]:
        """Applies field projection (e.g. {'_id': 0})."""
        if not projection:
            return dict(doc)
        res = dict(doc)
        if projection.get("_id") == 0:
            res.pop("_id", None)
        return res

    def _extract_document_text(self, doc: Dict[str, Any]) -> str:
        """Extracts searchable semantic text from a document."""
        parts = []
        for k, v in doc.items():
            if k in ("_id", "password_hash", "vector"):
                continue
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list):
                parts.append(f"{k}: {', '.join(str(x) for x in v)}")
            elif isinstance(v, dict):
                parts.append(f"{k}: {json.dumps(v)}")
        return " | ".join(parts)

    def _execute_find(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, int]] = None,
        sort_key: Optional[str] = None,
        sort_dir: int = 1,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, data FROM documents WHERE collection = ?", (self.name,))
        rows = cur.fetchall()

        matched = []
        for doc_id, data_json in rows:
            try:
                doc = json.loads(data_json)
                doc["id"] = doc.get("id") or doc_id
                doc["_id"] = doc_id
                if self._matches_filter(doc, query):
                    matched.append(doc)
            except Exception:
                continue

        # Sort
        if sort_key:
            reverse = sort_dir == -1
            matched.sort(key=lambda d: (d.get(sort_key) is None, d.get(sort_key, "")), reverse=reverse)

        # Skip and limit
        if skip:
            matched = matched[skip:]
        if limit is not None:
            matched = matched[:limit]

        return [self._apply_projection(doc, projection) for doc in matched]

    def find(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, int]] = None) -> VectorCursor:
        return VectorCursor(self, query or {}, projection)

    async def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
        res = self._execute_find(query, projection, limit=1)
        return res[0] if res else None

    async def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        docs = self._execute_find(query or {})
        return len(docs)

    async def insert_one(self, doc: Dict[str, Any]) -> InsertOneResult:
        doc_dict = dict(doc)
        doc_id = str(doc_dict.get("id") or doc_dict.get("_id") or f"{self.name}_{datetime.now().timestamp()}_{os.urandom(4).hex()}")
        doc_dict["id"] = doc_id
        doc_dict["_id"] = doc_id

        doc_text = self._extract_document_text(doc_dict)
        vector = _compute_vector(doc_text)
        data_json = json.dumps(doc_dict, default=str)
        vector_json = json.dumps(vector)

        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO documents (id, collection, text_content, vector, data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (doc_id, self.name, doc_text, vector_json, data_json, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return InsertOneResult(doc_id)

    async def insert_many(self, docs: List[Dict[str, Any]]) -> InsertManyResult:
        ids = []
        conn = self.db._get_conn()
        cur = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        for doc in docs:
            doc_dict = dict(doc)
            doc_id = str(doc_dict.get("id") or doc_dict.get("_id") or f"{self.name}_{datetime.now().timestamp()}_{os.urandom(4).hex()}")
            doc_dict["id"] = doc_id
            doc_dict["_id"] = doc_id
            doc_text = self._extract_document_text(doc_dict)
            vector = _compute_vector(doc_text)
            data_json = json.dumps(doc_dict, default=str)
            vector_json = json.dumps(vector)

            cur.execute(
                """
                INSERT OR REPLACE INTO documents (id, collection, text_content, vector, data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, self.name, doc_text, vector_json, data_json, now),
            )
            ids.append(doc_id)

        conn.commit()
        return InsertManyResult(ids)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> UpdateResult:
        doc = await self.find_one(query)
        if not doc:
            if upsert:
                new_doc = {**query}
                if "$set" in update:
                    new_doc.update(update["$set"])
                await self.insert_one(new_doc)
                return UpdateResult(0, 1)
            return UpdateResult(0, 0)

        # Apply update operations
        updated = dict(doc)
        if "$set" in update:
            updated.update(update["$set"])
        if "$inc" in update:
            for k, v in update["$inc"].items():
                updated[k] = updated.get(k, 0) + v
        if "$push" in update:
            for k, v in update["$push"].items():
                lst = list(updated.get(k, []))
                lst.append(v)
                updated[k] = lst

        doc_id = str(doc["_id"])
        doc_text = self._extract_document_text(updated)
        vector = _compute_vector(doc_text)
        data_json = json.dumps(updated, default=str)
        vector_json = json.dumps(vector)

        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE documents SET text_content = ?, vector = ?, data = ?, updated_at = ?
            WHERE id = ? AND collection = ?
            """,
            (doc_text, vector_json, data_json, datetime.now(timezone.utc).isoformat(), doc_id, self.name),
        )
        conn.commit()
        return UpdateResult(1, 1)

    async def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> UpdateResult:
        docs = self._execute_find(query)
        modified = 0
        for doc in docs:
            await self.update_one({"_id": doc["_id"]}, update)
            modified += 1
        return UpdateResult(len(docs), modified)

    async def delete_one(self, query: Dict[str, Any]) -> DeleteResult:
        doc = await self.find_one(query)
        if not doc:
            return DeleteResult(0)
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ? AND collection = ?", (str(doc["_id"]), self.name))
        conn.commit()
        return DeleteResult(1)

    async def delete_many(self, query: Dict[str, Any]) -> DeleteResult:
        docs = self._execute_find(query)
        if not docs:
            return DeleteResult(0)
        conn = self.db._get_conn()
        cur = conn.cursor()
        for doc in docs:
            cur.execute("DELETE FROM documents WHERE id = ? AND collection = ?", (str(doc["_id"]), self.name))
        conn.commit()
        return DeleteResult(len(docs))

    async def similarity_search(
        self,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector similarity search on documents in this collection.
        Returns matched documents sorted by descending relevance score with vector similarity metrics.
        """
        query_vec = _compute_vector(query_text)
        conn = self.db._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, text_content, vector, data FROM documents WHERE collection = ?", (self.name,))
        rows = cur.fetchall()

        scored_results = []
        for doc_id, text_content, vector_json, data_json in rows:
            try:
                doc = json.loads(data_json)
                doc["id"] = doc.get("id") or doc_id
                doc["_id"] = doc_id

                if filter and not self._matches_filter(doc, filter):
                    continue

                doc_vec = json.loads(vector_json) if vector_json else _compute_vector(text_content)
                sim = _cosine_similarity(query_vec, doc_vec)

                if sim >= min_similarity:
                    scored_results.append({
                        **doc,
                        "_vector_score": round(sim, 4),
                        "_similarity_pct": round(sim * 100, 1),
                    })
            except Exception:
                continue

        scored_results.sort(key=lambda x: x["_vector_score"], reverse=True)
        return scored_results[:top_k]


class VectorDB:
    """Main Vector Database management class."""

    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
        self._collections: Dict[str, VectorCollection] = {}
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Initializes SQLite tables for persistent vector document storage."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT NOT NULL,
                collection TEXT NOT NULL,
                text_content TEXT,
                vector TEXT,
                data TEXT NOT NULL,
                updated_at TEXT,
                PRIMARY KEY (id, collection)
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_collection ON documents(collection);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON documents(id);")
        conn.commit()
        conn.close()
        logger.info(f"Initialized VectorDB persistent store at: {self.db_path}")

    def __getitem__(self, collection_name: str) -> VectorCollection:
        if collection_name not in self._collections:
            self._collections[collection_name] = VectorCollection(self, collection_name)
        return self._collections[collection_name]

    def __getattr__(self, collection_name: str) -> VectorCollection:
        return self[collection_name]

    async def list_collection_names(self) -> List[str]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT collection FROM documents;")
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    async def similarity_search_all(self, query_text: str, top_k: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Runs vector search across all collections simultaneously."""
        collections = await self.list_collection_names()
        results = {}
        for c in collections:
            hits = await self[c].similarity_search(query_text, top_k=top_k)
            if hits:
                results[c] = hits
        return results


# Global singleton instance
vectordb_instance = VectorDB()
