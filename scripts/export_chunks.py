import os
import sys
from loaders.document_ai_loader import DocumentAILoader
import json

# Config
INPUT_PDF = "docs/fih-rules-of-hockey-June23-update.pdf"
OUTPUT_FILE = "debug_output/chunks_export.txt"

def export_chunks():
    print(f"--- Exporting Chunks from {INPUT_PDF} ---")
    
    # 1. Initialize Loader
    loader = DocumentAILoader()
    
    # 2. Run Ingestion (This triggers the full DocAI pipeline)
    print("Running DocumentAILoader...")
    chunks = loader.load_and_chunk(INPUT_PDF, variant="outdoor")
    
    print(f"✅ Generated {len(chunks)} chunks.")
    
    # 3. Write to File
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Source: {INPUT_PDF}\n")
        f.write(f"Total Chunks: {len(chunks)}\n")
        f.write("="*50 + "\n\n")
        
        for i, doc in enumerate(chunks):
            f.write(f"--- Chunk {i} ---\n")
            
            # Format Metadata nicely
            metadata_str = json.dumps(doc.metadata, indent=4)
            f.write(f"METADATA:\n{metadata_str}\n\n")
            
            f.write(f"CONTENT:\n{doc.page_content}\n")
            f.write("\n" + "="*50 + "\n\n")
            
    print(f"✅ Exported details to {OUTPUT_FILE}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_PDF):
        print(f"❌ Input file not found: {INPUT_PDF}")
        sys.exit(1)
        
    export_chunks()
