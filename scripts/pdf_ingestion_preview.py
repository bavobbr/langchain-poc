"""Preview Unstructured PDF ingestion and a simple Vertex AI smoke test."""
import os
from langchain_google_vertexai import VertexAI
from langchain_google_vertexai import VertexAI
from loaders import DocumentAILoader

# --- CONFIGURATION ---
# If you authenticated via `gcloud auth application-default login`, 
# you technically don't need to set credentials manually, but defining 
# the project ID explicitly is good practice.
PROJECT_ID = "langchain-poc-479114" 
REGION = "europe-west1"              # Changed from 'us-central1' to Belgium
MODEL_NAME = "gemini-2.0-flash-lite"     

def test_gemini_connection():
    """Smoke test to verify we can talk to Google's Brain."""
    print(f"--- 1. Testing connection to Vertex AI ({PROJECT_ID}) in {REGION}... ---")
    try:
        # Initialize the Model
        llm = VertexAI(
            model_name=MODEL_NAME,
            project=PROJECT_ID,
            location=REGION,
            temperature=0.1
        )
        
        # Simple invocation
        response = llm.invoke("Hello Gemini! Are you ready to parse some Hockey rules?")
        print(f"✅ SUCCESS! Gemini replied:\n{response}\n")
        return True
    except Exception as e:
        print(f"❌ ERROR: Could not connect to Vertex AI.\n{e}")
        return False

def ingest_pdf_preview(file_path):
    """
    Parses the PDF using Unstructured. 
    We only print the first few elements to verify it handles the layout.
    """
    print(f"--- 2. Ingesting PDF: {file_path} ---")
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found at {file_path}")
        return

    # DocumentAILoader handles GCS upload + Batch Processing + Parsing
    loader = DocumentAILoader()
    
    try:
        # Note: In the new interface, we pass a variant. For preview, "preview" is fine.
        docs = loader.load_and_chunk(file_path, variant="preview")
        print(f"✅ SUCCESS! Parsed {len(docs)} chunks from the PDF (via Document AI).")
        
        print("\n--- PREVIEW (First 5 Chunks) ---")
        for i, doc in enumerate(docs[:5]):
            print(f"[{i}] Heading: {doc.metadata.get('heading')} | Content: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"❌ ERROR: Parsing failed.\n{e}")

if __name__ == "__main__":
    # 1. Test LLM
    if test_gemini_connection():
        # 2. Test PDF Ingestion
        # REPLACE THIS with your actual filename
        ingest_pdf_preview("docs/fih-rules-of-hockey-June23-update.pdf")
