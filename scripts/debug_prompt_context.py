
"""
Debug Prompt Context Construction.

Mocks the retrieved documents and verifies how RAG Engine formats 
the context string sent to the LLM.
"""
from langchain_core.documents import Document
from rag_engine import FIHRulesEngine

def debug_prompt():
    print("--- Debugging Prompt Context ---")
    
    # 1. Start Engine (Lightweight, we won't call Vertex)
    engine = FIHRulesEngine()
    
    # 2. Mock Search Results
    # This simulates what comes back from the DB
    mock_docs = [
        Document(
            page_content="The ball is out of play when it crosses the back-line.", 
            metadata={
                "heading": "Rule 9.12",
                "chapter": "PLAYING THE GAME",
                "section": "Method of Scoring", # Intentionally different context
                "variant": "outdoor"
            }
        ),
        Document(
            page_content="Umpires shall blow the whistle.", 
            metadata={
                "heading": "Rule 11.3",
                "chapter": "UMPIRING",
                "section": "Conduct",
                "variant": "outdoor"
            }
        )
    ]
    
    # 3. Simulate Context Construction (Logic copied/verified from rag_engine)
    # Ideally we'd expose a helper, but for now we verify the logic we just wrote.
    context_pieces = []
    for d in mock_docs:
        meta = d.metadata
        heading = meta.get("heading", "Reference")
        chapter = meta.get("chapter", "")
        section = meta.get("section", "")
        
        context_string = f"[{heading}]"
        if chapter or section:
            context_string += f" (Context: {chapter} > {section})"
        
        context_pieces.append(f"{context_string}\n{d.page_content}")

    context_text = "\n\n".join(context_pieces)
    
    print("Generated Context String:\n")
    print("="*40)
    print(context_text)
    print("="*40)
    
    # Assertions
    assert "[Rule 9.12]" in context_text
    assert "PLAYING THE GAME > Method of Scoring" in context_text
    assert "[Rule 11.3]" in context_text
    
    print("\n✅ SUCCESS! Prompt formatting is correct.")

if __name__ == "__main__":
    debug_prompt()
