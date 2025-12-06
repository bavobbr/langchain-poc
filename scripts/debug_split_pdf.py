from pypdf import PdfReader, PdfWriter
import os

INPUT_PATH = "docs/fih-rules-of-hockey-June23-update.pdf"
OUTPUT_DIR = "debug_output/splits"
CHUNK_SIZE = 15

def split_pdf():
    reader = PdfReader(INPUT_PATH)
    total_pages = len(reader.pages)
    print(f"Total Pages: {total_pages}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    splits = []
    for i in range(0, total_pages, CHUNK_SIZE):
        writer = PdfWriter()
        end = min(i + CHUNK_SIZE, total_pages)
        for page_num in range(i, end):
            writer.add_page(reader.pages[page_num])
            
        filename = f"{OUTPUT_DIR}/split_{i}_{end}.pdf"
        with open(filename, "wb") as f:
            writer.write(f)
        
        print(f"Created {filename} ({end-i} pages)")
        splits.append(filename)
        
    return splits

if __name__ == "__main__":
    if not os.path.exists(INPUT_PATH):
        print(f"Input file not found: {INPUT_PATH}")
    else:
        split_pdf()
