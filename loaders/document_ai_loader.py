import re
import time
from typing import List
from google.cloud import documentai
from google.cloud import storage
from langchain_core.documents import Document
from .base import BaseLoader
import config
from pypdf import PdfReader, PdfWriter
import io

class DocumentAILoader(BaseLoader):
    """Parses PDF using Google Cloud Document AI (Batch Mode)."""

    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.DOCAI_LOCATION
        self.processor_id = config.DOCAI_PROCESSOR_ID
        self.gcs_bucket_name = config.GCS_BUCKET_NAME
        
        # Clients
        self.storage_client = storage.Client(project=self.project_id)
        opts = {"api_endpoint": f"{self.location}-documentai.googleapis.com"}
        self.docai_client = documentai.DocumentProcessorServiceClient(client_options=opts)

    def load_and_chunk(self, file_path: str, variant: str) -> List[Document]:
        print(f" -> [DocAI] 1. Analyzing {file_path} for splitting...")
        
        # New Strategy: Online Processing with Client-Side Sharding
        # This avoids GCS permission issues and is faster for < 100 pages.
        full_text = self._process_with_splitting(file_path)
        
        print(f" -> [DocAI] 2. Chunking merged text ({len(full_text)} chars)...")
        
        # Create a dummy DocAI object to reuse existing chunker signature
        dummy_doc = documentai.Document()
        dummy_doc.text = full_text
        
        return self._smart_chunking(dummy_doc, variant)

    def _process_with_splitting(self, file_path: str) -> str:
        """Splits PDF into 15-page chunks and processes them synchronously."""
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        chunk_size = 15
        full_text = ""
        
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
            
            # 2. Process Chunk Online
            print(f"    - Processing Chunk {i//chunk_size + 1}/{total_pages//chunk_size + 1} (Pages {i}-{end})...")
            text = self._online_process(chunk_content)
            full_text += text + "\n"
            
        return full_text

    def _online_process(self, file_content: bytes) -> str:
        """Calls Document AI Online Processing."""
        name = self.docai_client.processor_path(self.project_id, self.location, self.processor_id)
        
        raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        
        try:
            result = self.docai_client.process_document(request=request)
            return result.document.text
        except Exception as e:
            print(f"    ❌ Chunk failed: {e}")
            return ""

    # Removed _upload_to_gcs, _batch_process, _get_results

    def _smart_chunking(self, docai_doc: documentai.Document, variant: str) -> List[Document]:
        """Adaptation of the regex chunker for Document AI's full text output."""
        chunks = []
        current_chunk_text = ""
        current_heading = "Front Matter"
        
        # Reuse existing regex
        header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
        section_pattern = re.compile(r'^[A-Z\s]{4,}$')
        
        # Document AI text is one giant string with \n. 
        # We process line by line.
        lines = docai_doc.text.split("\n")
        
        for line in lines:
            text = line.strip()
            # Heuristics
            if len(text) < 2 or (text.isdigit() and int(text) > 20): continue
            
            if header_pattern.match(text) or (section_pattern.match(text) and len(text) < 50):
                if len(current_chunk_text) < 20:
                    current_heading = f"{current_heading} > {text}"
                    current_chunk_text += f" {text}"
                    continue
                    
                chunks.append(Document(
                    page_content=current_chunk_text,
                    metadata={"source": "PDF (DocAI)", "heading": current_heading, "variant": variant}
                ))
                current_heading = text
                current_chunk_text = text + " "
            else:
                current_chunk_text += f"\n{text}"
                
        if current_chunk_text:
            chunks.append(Document(
                page_content=current_chunk_text,
                metadata={"source": "PDF (DocAI)", "heading": current_heading, "variant": variant}
            ))
            
        return chunks
