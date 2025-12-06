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
        
        # Generator of Document AI Objects (Shards)
        docai_shards = self._process_with_splitting_structural(file_path)
        
        print(f" -> [DocAI] 2. Structural Chunking...")
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

    # Combined into _process_with_splitting_structural

    # Removed _upload_to_gcs, _batch_process, _get_results

    def _layout_chunking(self, docai_shards, variant: str) -> List[Document]:
        """Hybrid Chunker: Iterates visually sorted blocks."""
        chunks = []
        current_chunk_text = ""
        current_heading = "Front Matter"
        
        header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
        
        for shard in docai_shards:
            if not shard.pages: continue
            
            for page in shard.pages:
                # 1. Extract and Visual Sort
                # Document AI sometimes returns Column-Major order (Left Col top-down, then Right Col).
                # We want Row-Major (Top-down across columns).
                blocks_with_coords = []
                for block in page.blocks:
                    # Get Y coordinate (Top Left)
                    poly = block.layout.bounding_poly
                    # Default to 0 if no geo info
                    y = poly.normalized_vertices[0].y if poly.normalized_vertices else 0
                    x = poly.normalized_vertices[0].x if poly.normalized_vertices else 0
                    blocks_with_coords.append((block, y, x))
                
                # Sort by Y (rounded to 2 decimal places ~1% page height fuzziness), then X
                # This groups "1.1" (Y=0.2) and "Text..." (Y=0.21) together before "1.2" (Y=0.3)
                blocks_with_coords.sort(key=lambda item: (round(item[1], 3), item[2]))
                
                # 2. Iterate Sorted Blocks
                for block, _, _ in blocks_with_coords:
                    block_text = self._get_text(shard, block.layout.text_anchor).strip()
                    if not block_text: continue
                    
                    # Normalization
                    if len(block_text) < 2 and not block_text[0].isdigit(): continue

                    # Hybrid Logic
                    if header_pattern.match(block_text):
                        if len(current_chunk_text) > 20: 
                            chunks.append(Document(
                                page_content=current_chunk_text.strip(),
                                metadata={"source": "PDF (DocAI-Layout)", "heading": current_heading, "variant": variant}
                            ))
                        
                        current_heading = block_text
                        current_chunk_text = block_text + " "
                    else:
                        current_chunk_text += block_text + "\n"
        
        # Flush last
        if current_chunk_text:
             chunks.append(Document(
                page_content=current_chunk_text.strip(),
                metadata={"source": "PDF (DocAI-Layout)", "heading": current_heading, "variant": variant}
            ))
            
        return chunks

    def _get_text(self, document: documentai.Document, text_anchor: documentai.Document.TextAnchor) -> str:
        """Helper to extract text from a specific anchor."""
        text = ""
        for segment in text_anchor.text_segments:
            start_index = int(segment.start_index)
            end_index = int(segment.end_index)
            text += document.text[start_index:end_index]
        return text
