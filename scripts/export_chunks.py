"""Export Document AI chunks to a text file for manual inspection."""
import os
import sys
import loaders
import json

# Config
INPUT_PDF = "docs/fih-rules-of-hockey-June23-update.pdf"
OUTPUT_FILE = "debug_output/chunks_export.txt"

def export_chunks():
    print(f"--- Exporting Chunks from {INPUT_PDF} ---")
    
    # 1. Initialize Loader
    # Using Online Loader directly for specific page debug (Index 42 = Page 43)
    from loaders.document_ai_online_loader import DocumentAIOnlineLoader
    loader = DocumentAIOnlineLoader()
    
    # 2. Run Ingestion (This triggers the full DocAI pipeline)
    print("Running DocumentAILoader (Online Mode, Page 43 only)...")
    # Page index 42 because pdf pages are 0-indexed
    chunks = loader.load_and_chunk(INPUT_PDF, variant="outdoor", target_pages=[42])
    
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
