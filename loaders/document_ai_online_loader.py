import time
from typing import List
from google.cloud import documentai
from google.cloud import storage
from langchain_core.documents import Document
from .base import BaseLoader
from .document_ai_common import DocumentAILayoutMixin
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

    def load_and_chunk(self, file_path: str, variant: str) -> List[Document]:
        print(f" -> [DocAI Online] 1. Analyzing {file_path} for splitting...")
        
        # Generator of Document AI Objects (Shards)
        docai_shards = self._process_with_splitting_structural(file_path)
        
        print(f" -> [DocAI Online] 2. Structural Chunking...")
        return self._layout_chunking(docai_shards, variant)

    def _process_with_splitting_structural(self, file_path: str):
        """Splits PDF and yields Document AI objects."""
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        chunk_size = 15
        
        print(f"    - Found {total_pages} pages. Splitting into {chunk_size}-page chunks.")
        
        for i in range(0, total_pages, chunk_size):
            # 1. Create Chunk
            writer = PdfWriter()
            end = min(i + chunk_size, total_pages)
            for page_num in range(i, end):
                writer.add_page(reader.pages[page_num])
            
            chunk_buffer = io.BytesIO()
            writer.write(chunk_buffer)
            chunk_content = chunk_buffer.getvalue()
            
            # 2. Process to Object
            print(f"    - Processing Chunk {i//chunk_size + 1}/{total_pages//chunk_size + 1}...")
            yield self._online_process_structural(chunk_content)

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
