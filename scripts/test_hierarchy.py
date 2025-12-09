"""
Unit Test for Hierarchical Metadata Parsing.

Mocks Google Cloud Document AI structure to verify that DocumentAILayoutMixin
correctly extracts Chapters, Sections, and Rules.
"""
from typing import List
from dataclasses import dataclass, field
from loaders.document_ai_common import DocumentAILayoutMixin

# --- Mocks for google.cloud.documentai ---
@dataclass
class Vertex:
    x: float
    y: float

@dataclass
class BoundingPoly:
    normalized_vertices: List[Vertex]

@dataclass
class Layout:
    bounding_poly: BoundingPoly
    text_anchor: 'TextAnchor'

@dataclass
class TextSegment:
    start_index: int
    end_index: int

@dataclass
class TextAnchor:
    text_segments: List[TextSegment]

@dataclass
class Block:
    layout: Layout

@dataclass
class Page:
    blocks: List[Block]

@dataclass
class DocumentAI_Document:
    text: str
    pages: List[Page]

# --- Helper to build mock blocks ---
def create_block(text_content: str, y: float, full_text: str) -> Block:
    # Append text to mock document buffer (if we were building it dynamically)
    # Here we assume full_text is pre-built and we just point to indices.
    try:
        start = full_text.index(text_content)
        end = start + len(text_content)
    except ValueError:
        # Fallback for repeated text - specific mock setup
        start = 0
        end = len(text_content)

    return Block(
        layout=Layout(
            bounding_poly=BoundingPoly(normalized_vertices=[Vertex(x=0.1, y=y)]),
            text_anchor=TextAnchor(text_segments=[TextSegment(start, end)])
        )
    )

class MockLoader(DocumentAILayoutMixin):
    pass

def test_hierarchy():
    print("--- Testing Hierarchical Extraction ---")
    
    # 1. Setup Mock Data
    # We simulate a page with mixed headers and rules
    doc_text = (
        "Irrelevant\n"
        "PLAYING THE GAME\n"
        "1 Field of play\n"
        "1.1 The field is rectangular.\n"
        "1.2 The lines are white.\n"
        "UMPIRING\n"
        "2 Applying the rules\n"
        "2.1 Umpires shall be..."
    )
    
    # Create blocks mapping to the text above
    # We manually map them for precision
    blocks = []
    
    # Y-coordinates define order
    items = [
        ("PLAYING THE GAME", 0.1),
        ("1 Field of play", 0.2),
        ("1.1", 0.3), ("The field is rectangular.", 0.31), 
        ("1.2", 0.4), ("The lines are white.", 0.41),
        ("UMPIRING", 0.5),
        ("2 Applying the rules", 0.6),
        ("2.1", 0.7), ("Umpires shall be...", 0.71)
    ]
    
    for txt, y in items:
        blocks.append(create_block(txt, y, doc_text))
        
    mock_doc = DocumentAI_Document(text=doc_text, pages=[Page(blocks=blocks)])
    loader = MockLoader()
    
    # 2. Run Parsing
    chunks = loader._layout_chunking([mock_doc], variant="test")
    
    # 3. Verify
    print(f"Generated {len(chunks)} chunks.")
    
    for i, chunk in enumerate(chunks):
        meta = chunk.metadata
        print(f"[{i}] Content: '{chunk.page_content[:20]}...'")
        print(f"    Chapter: {meta.get('chapter')}")
        print(f"    Section: {meta.get('section')}")
        print(f"    Heading: {meta.get('heading')}")
    
    # Assertions
    # Chunk 0: Rule 1.1
    c0 = chunks[0]
    assert c0.metadata["chapter"] == "PLAYING THE GAME", f"Expected PLAYING THE GAME, got {c0.metadata['chapter']}"
    assert c0.metadata["section"] == "1 Field of play", f"Expected 1 Field of play, got {c0.metadata['section']}"
    assert "1.1" in c0.metadata["heading"] or "1.1" in c0.page_content # Heading is current_heading

    # Chunk 2: Rule 2.1 (Should switch chapter!)
    c2 = chunks[2]
    assert c2.metadata["chapter"] == "UMPIRING", f"Expected UMPIRING, got {c2.metadata['chapter']}"
    assert c2.metadata["section"] == "2 Applying the rules", f"Expected 2 Applying the rules, got {c2.metadata['section']}"

    print("\n✅ SUCCESS! Hierarchy extracted correctly.")

if __name__ == "__main__":
    test_hierarchy()
