import re
from typing import List
from langchain_core.documents import Document
from .base import BaseLoader

class UnstructuredLoader(BaseLoader):
    """Legacy loader using local Unstructured.io processing + Regex chunking."""

    def load_and_chunk(self, file_path: str, variant: str) -> List[Document]:
        # Deferred import to avoid crash if 'unstructured' is not installed
        try:
            from langchain_community.document_loaders import UnstructuredPDFLoader
        except ImportError:
            raise ImportError(
                "The 'unstructured' library is required for this legacy loader. "
                "Please install it with `pip install unstructured[pdf]`."
            )
            
        # 1. Parse raw elements
        loader = UnstructuredPDFLoader(file_path, mode="elements")
        raw_elements = loader.load()
        
        # 2. Apply custom chunking logic
        return self._smarter_chunking(raw_elements, variant)

    def _smarter_chunking(self, elements, variant) -> List[Document]:
        """Aggregate PDF elements into rule-aware chunks with headings.

        Uses a regex for rule numbers (e.g., 9.12) and compact section titles,
        skipping page numbers (>20) and merging short "lonely" headers.
        """
        chunks = []
        current_chunk_text = ""
        current_heading = "Front Matter"
        # Regex patterns from original rag_engine.py
        header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
        section_pattern = re.compile(r'^[A-Z\s]{4,}$')

        for el in elements:
            text = el.page_content.strip()
            # Simple heuristic filters
            if len(text) < 2 or (text.isdigit() and int(text) > 20): continue
            
            if header_pattern.match(text) or (section_pattern.match(text) and len(text) < 50):
                # If current chunk is too small, just append to it (merging headers)
                if len(current_chunk_text) < 20:
                    current_heading = f"{current_heading} > {text}"
                    current_chunk_text += f" {text}"
                    continue
                
                # Setup new chunk
                chunks.append(Document(
                    page_content=current_chunk_text, 
                    metadata={"source": "PDF", "heading": current_heading, "variant": variant}
                ))
                current_heading = text
                current_chunk_text = text + " "
            else:
                current_chunk_text += f"\n{text}"
        
        # Flush last chunk
        if current_chunk_text:
            chunks.append(Document(
                page_content=current_chunk_text, 
                metadata={"source": "PDF", "heading": current_heading, "variant": variant}
            ))
            
        return chunks
