from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.documents import Document
import config
import re
from database import PostgresVectorDB  

class FIHRulesEngine:
    def __init__(self):
        # 1. AI Models
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
        
        # 2. Database (Abstracted)
        self.db = PostgresVectorDB()

    # --- INGESTION FLOW ---
    def ingest_pdf(self, file_path, variant):
        # A. Logic: Parse & Chunk
        loader = UnstructuredPDFLoader(file_path, mode="elements")
        docs = self._smarter_chunking(loader.load(), variant)
        
        # B. Logic: Embed
        print(f"   Generating embeddings for {len(docs)} chunks...")
        texts = [d.page_content for d in docs]
        vectors = self.embeddings.embed_documents(texts)
        
        # C. Data Access: Persist
        self.db.insert_batch(texts, vectors, variant)
        
        return len(docs)

    # --- QUERY FLOW ---
    def query(self, user_input, history=[]):
        # A. Logic: Reformulate & Route
        standalone_query = self._contextualize_query(history, user_input)
        
        detected_variant = self._route_query(standalone_query)
        if detected_variant not in config.VARIANTS: 
            detected_variant = "outdoor"

        # B. Logic: Embed Query
        query_vector = self.embeddings.embed_query(standalone_query)

        # C. Data Access: Retrieve
        results = self.db.search(query_vector, detected_variant, k=config.RETRIEVAL_K)
        
        # Convert DB results back to LangChain Documents for consistency
        docs = [Document(page_content=r["content"], metadata={"variant": r["variant"]}) for r in results]
        
        # D. Logic: Synthesize Answer
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

    # --- HELPERS (Pure Logic) ---
    def _smarter_chunking(self, elements, variant):
        chunks = []
        current_chunk_text = ""
        current_heading = "Front Matter"
        header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
        section_pattern = re.compile(r'^[A-Z\s]{4,}$')

        for el in elements:
            text = el.page_content.strip()
            if len(text) < 2 or (text.isdigit() and int(text) > 20): continue
            
            if header_pattern.match(text) or (section_pattern.match(text) and len(text) < 50):
                if len(current_chunk_text) < 20:
                    current_heading = f"{current_heading} > {text}"
                    current_chunk_text += f" {text}"
                    continue
                chunks.append(Document(page_content=current_chunk_text, metadata={"source": "PDF", "heading": current_heading, "variant": variant}))
                current_heading = text
                current_chunk_text = text + " "
            else:
                current_chunk_text += f"\n{text}"
        if current_chunk_text:
            chunks.append(Document(page_content=current_chunk_text, metadata={"source": "PDF", "heading": current_heading, "variant": variant}))
        return chunks

    def _contextualize_query(self, history, query):
        if not history: return query
        history_str = "\n".join([f"{role}: {txt}" for role, txt in history[-4:]])
        prompt = f"Rewrite to be standalone.\nHISTORY:\n{history_str}\nQUESTION: {query}"
        return self.llm.invoke(prompt).strip()

    def _route_query(self, query):
        prompt = f"Analyze Field Hockey question. Return 'outdoor', 'indoor', or 'hockey5s'. Default to 'outdoor'.\nQUESTION: {query}"
        return self.llm.invoke(prompt).strip().lower().replace("'", "").replace('"', "")