import re
from typing import List
from google.cloud import documentai
from langchain_core.documents import Document

class DocumentAILayoutMixin:
    """Shared logic for visual/structural chunking of Document AI results."""

    def _layout_chunking(self, docai_shards: List[documentai.Document], variant: str) -> List[Document]:
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
