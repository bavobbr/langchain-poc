"""Core RAG engine for FIH Rules.

Provides ingestion (chunking + embeddings + persistence) and query handling
(contextualization, routing, retrieval, and synthesis).
"""

from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_core.documents import Document
import config
from database import PostgresVectorDB
import loaders

class FIHRulesEngine:
    """High-level interface to embeddings, LLM, and vector DB."""

    def __init__(self):
        # Models
        self.embeddings = VertexAIEmbeddings(
            model_name=config.EMBEDDING_MODEL, 
            project=config.PROJECT_ID, 
            location=config.REGION
        )
        self.llm = VertexAI(
            model_name=config.LLM_MODEL,
            project=config.PROJECT_ID,
            location=config.REGION,
            temperature=0
        )
        # Database
        self.db = PostgresVectorDB()

    # Ingestion
    def ingest_pdf(self, file_path, variant):
        """Parse a PDF, chunk, embed and persist under a ruleset variant."""
        # 2. Ingest
        # Dynamically load the configured loader (Online vs Batch)
        docai_loader = loaders.get_document_ai_loader()
        docs = docai_loader.load_and_chunk(file_path, variant)

        if not docs:
            print("   ⚠️ No chunks generated!")
            return 0
        
        # Deduplication: Clear existing data for this variant
        print(f"   Cleaning existing '{variant}' data...")
        self.db.delete_variant(variant)
        
        # Embed
        print(f"   Generating embeddings for {len(docs)} chunks...")
        texts = [d.page_content for d in docs]
        vectors = self.embeddings.embed_documents(texts)
        # Persist
        self.db.insert_batch(texts, vectors, variant)
        
        return len(docs)

    # Querying
    def query(self, user_input, history=[]):
        """Answer a user question using contextualization, routing, and RAG."""
        # Reformulate & route
        standalone_query = self._contextualize_query(history, user_input)
        
        detected_variant = self._route_query(standalone_query)
        if detected_variant not in config.VARIANTS: 
            detected_variant = "outdoor"
        # Embed query
        query_vector = self.embeddings.embed_query(standalone_query)
        # Retrieve
        results = self.db.search(query_vector, detected_variant, k=config.RETRIEVAL_K)
        
        # Convert DB results back to LangChain Documents for consistency
        docs = [Document(page_content=r["content"], metadata={"variant": r["variant"]}) for r in results]
        
        # Synthesize answer
        context_text = "\n\n".join([d.page_content for d in docs])
        
        if not context_text:
            return {
                "answer": f"I checked the **{detected_variant}** rules but couldn't find an answer.",
                "standalone_query": standalone_query,
                "variant": detected_variant,
                "source_docs": []
            }

        full_prompt = f"""
        Expert FIH Umpire for {detected_variant.upper()}. 
        Answer based on Context. Cite Rules.
        
        CONTEXT:
        {context_text}
        
        QUESTION:
        {standalone_query}
        """
        answer = self.llm.invoke(full_prompt)
        
        return {
            "answer": answer,
            "standalone_query": standalone_query,
            "variant": detected_variant,
            "source_docs": docs
        }

    def _contextualize_query(self, history, query):
        """Rewrite the latest user message as a standalone query."""
        if not history: return query
        history_str = "\n".join([f"{role}: {txt}" for role, txt in history[-4:]])
        prompt = f"Rewrite to be standalone.\nHISTORY:\n{history_str}\nQUESTION: {query}"
        return self.llm.invoke(prompt).strip()

    def _route_query(self, query):
        """Return 'outdoor' | 'indoor' | 'hockey5s' based on content."""
        prompt = f"Analyze Field Hockey question. Return 'outdoor', 'indoor', or 'hockey5s'. Default to 'outdoor'.\nQUESTION: {query}"
        return self.llm.invoke(prompt).strip().lower().replace("'", "").replace('"', "")
