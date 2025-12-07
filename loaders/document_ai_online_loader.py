import time
from typing import List
from google.cloud import documentai
from google.cloud import storage
from langchain_core.documents import Document
from .base import BaseLoader
from .document_ai_common import DocumentAILayoutMixin
from .utils import summarize_text
import config
from pypdf import PdfReader, PdfWriter
import io

class DocumentAIOnlineLoader(BaseLoader, DocumentAILayoutMixin):
    """Parses PDF using Document AI Online Processing (Client-Side Sharding)."""

    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.DOCAI_LOCATION
        self.processor_id = config.DOCAI_PROCESSOR_ID
        
        # Clients
        opts = {"api_endpoint": f"{self.location}-documentai.googleapis.com"}
        self.docai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

    def load_and_chunk(self, file_path: str, variant: str, original_filename: str = None, target_pages: List[int] = None) -> List[Document]:
        print(f" -> [DocAI Online] 1. Analyzing {file_path} for splitting...")
        
        # Generator of Document AI Objects (Shards)
        docai_shards = self._process_with_splitting_structural(file_path, target_pages)
        
        print(f" -> [DocAI Online] 2. Structural Chunking...")
        chunks = self._layout_chunking(docai_shards, variant)
        
        print(f" -> [DocAI Online] 3. Summarizing {len(chunks)} chunks...")
        for i, doc in enumerate(chunks):
            print(f"    - Summarizing chunk {i+1}/{len(chunks)}...")
            summary = summarize_text(doc.page_content)
            doc.metadata["summary"] = summary
            doc.metadata["source_file"] = original_filename if original_filename else file_path.split("/")[-1]
            if "page" not in doc.metadata:
                doc.metadata["page"] = "unknown"
            
        return chunks

    def _process_with_splitting_structural(self, file_path: str, target_pages: List[int] = None):
        """Splits PDF and yields Document AI objects."""
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        chunk_size = 15
        
        pages_to_process = range(total_pages)
        if target_pages:
            print(f"    - Filtering for specific pages: {target_pages}")
            pages_to_process = [p for p in target_pages if 0 <= p < total_pages]
            # When filtering, we might as well process them in one chunk if small enough
            # But strictly adhering to chunk_size=15 logic is safer if they ask for many scattered pages.
            # Simplified approach: Create a custom list of pages and chunk that list.
        
        # We'll just iterate the requested pages and batch them into 15 to respect limits
        current_batch = []
        
        for page_num in pages_to_process:
            current_batch.append(page_num)
            
            if len(current_batch) >= chunk_size:
                yield self._process_batch(reader, current_batch)
                current_batch = []
        
        # Yield remaining
        if current_batch:
            yield self._process_batch(reader, current_batch)

    def _process_batch(self, reader, page_nums):
        """Helper to create a PDF from specific page numbers and process it."""
        writer = PdfWriter()
        for p in page_nums:
            writer.add_page(reader.pages[p])
        
        chunk_buffer = io.BytesIO()
        writer.write(chunk_buffer)
        chunk_content = chunk_buffer.getvalue()
        
        print(f"    - Processing Chunk with {len(page_nums)} pages...")
        return self._online_process_structural(chunk_content)

    def _online_process_structural(self, file_content: bytes) -> documentai.Document:
        """Calls Document AI Online Processing and returns full object."""
        name = self.docai_client.processor_path(self.project_id, self.location, self.processor_id)
        
        raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        
        try:
            result = self.docai_client.process_document(request=request)
            return result.document
        except Exception as e:
            print(f"    ❌ Chunk failed: {e}")
            return documentai.Document()
