"""Minimal data access layer for Cloud SQL (Postgres + pgvector).

Creates a SQLAlchemy pool via the Cloud SQL Python Connector and exposes
simple batch insert and similarity search operations used by the engine.
"""

from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy import text
import config

class PostgresVectorDB:
    """Thin wrapper around a Postgres connection pool with vector ops."""

    def __init__(self):
        self.connector = Connector()
        self.pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=self._get_conn,
        )
        self._init_schema()

    def _get_conn(self):
        """Return a fresh pg8000 connection via the Cloud SQL connector.

        Raises a clear error if required credentials are missing to avoid
        ambiguous connection failures.
        """
        # Fail fast if required secrets are missing
        if not getattr(config, "DB_PASS", None):
            raise RuntimeError("DB_PASS environment variable is required but not set.")
        if not getattr(config, "DB_USER", None):
            raise RuntimeError("DB_USER environment variable is required but not set.")
        return self.connector.connect(
            f"{config.PROJECT_ID}:{config.REGION}:{config.INSTANCE_NAME}",
            "pg8000",
            user=config.DB_USER,
            password=config.DB_PASS,
            db=config.DATABASE_NAME
        )

    def _init_schema(self):
        """Ensure the pgvector extension exists (idempotent)."""
        with self.pool.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

    def insert_batch(self, contents, vectors, variant):
        """Insert a batch of text chunks and their embeddings.

        contents: list[str] — raw text chunks
        vectors: list[list[float]] — embedding vectors (same length as contents)
        variant: str — ruleset label stored alongside the content
        """
        data = []
        for content, vector in zip(contents, vectors):
            # pg8000 requires the vector to be a string format like '[0.1, 0.2...]'
            data.append({
                "content": content,
                "embedding": str(vector),
                "variant": variant
            })

        with self.pool.connect() as conn:
            stmt = text(f"""
                INSERT INTO {config.TABLE_NAME} (content, embedding, variant)
                VALUES (:content, :embedding, :variant)
            """)
            conn.execute(stmt, data)
            conn.commit()

    def search(self, query_vector, variant, k=15):
        """Return top-k similar chunks for a variant using <=> distance."""
        with self.pool.connect() as conn:
            stmt = text(f"""
                SELECT content, variant
                FROM {config.TABLE_NAME}
                WHERE variant = :variant
                ORDER BY embedding <=> :vector
                LIMIT :k
            """)
            
            result = conn.execute(stmt, {
                "variant": variant,
                "vector": str(query_vector),
                "k": k
            })
            
            # Unpack results into a clean list of dicts or tuples
            return [{"content": row[0], "variant": row[1]} for row in result]
