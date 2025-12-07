import re
from typing import List
from google.cloud import documentai
from langchain_core.documents import Document

class DocumentAILayoutMixin:
    """Shared logic for visual/structural chunking of Document AI results."""

    def _layout_chunking(self, docai_shards: List[documentai.Document], variant: str) -> List[Document]:
        """Hybrid Chunker: Iterates visually sorted blocks with Hierarchical Context."""
        chunks = []
        current_chunk_text = ""
        current_heading = "Front Matter"
        current_chapter = "General"
        current_section = "General"
        
        # Regex Patterns
        # 1. Rule Header: "9.12", "Rule 4", "10.1"
        header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
        # 2. Section Header: "1 Field of play" (Digit + Space + Text)
        section_pattern = re.compile(r'^\d+\s+[A-Za-z].*')
        # 3. Chapter Header: "PLAYING THE GAME" (All Caps, min length 4 to avoid short noise)
        chapter_pattern = re.compile(r'^[A-Z\s]{4,}$')

        for shard in docai_shards:
            if not shard.pages: continue
            
            for page in shard.pages:
                blocks_with_coords = []
                for block in page.blocks:
                    poly = block.layout.bounding_poly
                    y = poly.normalized_vertices[0].y if poly.normalized_vertices else 0
                    x = poly.normalized_vertices[0].x if poly.normalized_vertices else 0
                    blocks_with_coords.append((block, y, x))
                
                # Visual Sort (Row-Major)
                blocks_with_coords.sort(key=lambda item: (round(item[1], 3), item[2]))
                
                for block, _, _ in blocks_with_coords:
                    block_text = self._get_text(shard, block.layout.text_anchor).strip()
                    if not block_text: continue
                    
                    # --- Hierarchy Detection ---
                    # Check for Chapter (All Caps)
                    # We assume chapters are distinct lines.
                    if chapter_pattern.match(block_text):
                        # Flush previous chunk BEFORE updating state
                        if current_chunk_text.strip():
                            chunks.append(Document(
                                page_content=current_chunk_text.strip(),
                                metadata={
                                    "source": "PDF (DocAI-Layout)", 
                                    "heading": current_heading, 
                                    "variant": variant,
                                    "chapter": current_chapter,
                                    "section": current_section
                                }
                            ))
                            current_chunk_text = ""
                        
                        current_chapter = block_text
                        continue # Consume header

                    # Check for Section ("1 Field of Play")
                    if section_pattern.match(block_text):
                        # Flush previous chunk BEFORE updating state
                        if current_chunk_text.strip():
                            chunks.append(Document(
                                page_content=current_chunk_text.strip(),
                                metadata={
                                    "source": "PDF (DocAI-Layout)", 
                                    "heading": current_heading, 
                                    "variant": variant,
                                    "chapter": current_chapter,
                                    "section": current_section
                                }
                            ))
                            current_chunk_text = ""
                        
                        current_section = block_text
                        continue # Consume header

                    # --- Rule Detection (Existing Logic) ---
                    if header_pattern.match(block_text):
                        if len(current_chunk_text) > 20: 
                            chunks.append(Document(
                                page_content=current_chunk_text.strip(),
                                metadata={
                                    "source": "PDF (DocAI-Layout)", 
                                    "heading": current_heading, 
                                    "variant": variant,
                                    "chapter": current_chapter,
                                    "section": current_section
                                }
                            ))
                        
                        current_heading = block_text
                        current_chunk_text = block_text + " "
                    else:
                        current_chunk_text += block_text + "\n"
        
        # Flush last
        if current_chunk_text:
             chunks.append(Document(
                page_content=current_chunk_text.strip(),
                metadata={
                    "source": "PDF (DocAI-Layout)", 
                    "heading": current_heading, 
                    "variant": variant,
                    "chapter": current_chapter,
                    "section": current_section
                }
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
