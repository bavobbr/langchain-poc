import os
import sys
import loaders

# Config
INPUT_PDF = "docs/fih-rules-of-hockey-June23-update.pdf"
OUTPUT_FILE = "debug_output/docai_structure_dump.txt"

def inspect_structure():
    print(f"--- Inspecting Document AI Structure for {INPUT_PDF} ---")
    
    loader = loaders.get_document_ai_loader()
    
    # Use the internal splitter to get just the first shard (first 15 pages)
    # This avoids processing the whole file just for debugging
    print("Getting first shard...")
    gen = loader._process_with_splitting_structural(INPUT_PDF)
    first_shard = next(gen) 
    
    print(f"✅ Retrieved Shard with {len(first_shard.pages)} pages.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"RAW STRUCTURE DUMP (First 15 pages)\n")
        f.write("="*50 + "\n\n")
        
        for p_idx, page in enumerate(first_shard.pages):
            f.write(f"=== PAGE {p_idx + 1} ===\n")
            
            for b_idx, block in enumerate(page.blocks):
                # Text extraction helper from loader
                block_text = loader._get_text(first_shard, block.layout.text_anchor).strip()
                
                # Visual Metadata
                # Check formatting/confidence and Bounding Box
                # normalized_vertices[0] is top-left usually
                poly = block.layout.bounding_poly
                if poly.normalized_vertices:
                    y_top = poly.normalized_vertices[0].y
                    x_left = poly.normalized_vertices[0].x
                    geo_info = f"(Y: {y_top:.4f}, X: {x_left:.4f})"
                else:
                    geo_info = "(No Geo)"

                normalized = block_text.replace("\n", "\\n")
                
                f.write(f"  [Block {b_idx}] {geo_info} (Len: {len(block_text)})\n")
                f.write(f"    Content: \"{normalized}\"\n")
                f.write("\n")
            f.write("\n")

    print(f"✅ Dumped structure to {OUTPUT_FILE}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_PDF):
        print(f"❌ Input file not found: {INPUT_PDF}")
    else:
        inspect_structure()
