"""Export Document AI chunks to a text file for manual inspection."""
import os
import sys
import loaders
import json

# Config
INPUT_PDF = "docs/fih-rules-of-hockey-June23-update.pdf"
OUTPUT_FILE = "debug_output/chunks_export.txt"

import argparse

def export_chunks():
    parser = argparse.ArgumentParser(description="Export Document AI chunks to a text file.")
    parser.add_argument("--start-page", type=int, default=43, help="Start page number (1-based)")
    parser.add_argument("--end-page", type=int, default=43, help="End page number (1-based)")
    args = parser.parse_args()

    start_idx = args.start_page - 1
    end_idx = args.end_page - 1
    
    # Generate list of page indices
    # range(start, end + 1) because end is inclusive in user intent but exclusive in range()
    target_pages = list(range(start_idx, end_idx + 1))
    
    print(f"--- Exporting Chunks from {INPUT_PDF} ---")
    print(f"Target Pages: {args.start_page} to {args.end_page} (Indices: {target_pages})")
    
    # 1. Initialize Loader
    from loaders.document_ai_online_loader import DocumentAIOnlineLoader
    loader = DocumentAIOnlineLoader()
    
    # 2. Run Ingestion (This triggers the full DocAI pipeline)
    print("Running DocumentAILoader (Online Mode)...")
    chunks = loader.load_and_chunk(INPUT_PDF, variant="outdoor", target_pages=target_pages)
    
    print(f"✅ Generated {len(chunks)} chunks.")
    
    # 3. Write to File
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Source: {INPUT_PDF}\n")
        f.write(f"Pages: {args.start_page}-{args.end_page}\n")
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
