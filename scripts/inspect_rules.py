import re
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document

# A simple wrapper to make a text line look like a LangChain Document
# This allows us to reuse your existing chunking logic without rewriting it.
class SimpleElement:
    def __init__(self, text):
        self.page_content = text
        self.metadata = {}

def extract_chunks(file_path):
    print(f"📄 Loading {file_path} with PDFPlumber...")
    try:
        loader = PDFPlumberLoader(file_path)
        raw_pages = loader.load()
    except Exception as e:
        print(f"❌ Error loading PDF: {e}")
        return []

    print(f"   Loaded {len(raw_pages)} pages. Splitting into lines...")

    # --- STEP 1: Flatten Pages into Lines ---
    # PDFPlumber returns big blocks of text per page. 
    # We split by '\n' to give our Regex a chance to evaluate each line individually.
    elements = []
    for page in raw_pages:
        lines = page.page_content.split('\n')
        for line in lines:
            if line.strip(): # Skip empty lines
                elements.append(SimpleElement(line))

    print(f"   Processing {len(elements)} text lines...")
    
    # --- STEP 2: Apply Your Proven Regex Logic ---
    chunks = []
    current_chunk_text = ""
    current_heading = "Front Matter"
    
    # Matches "9.1", "12.2.1" (Rules 1-19)
    # Matches "Rule 9"
    # Excludes page numbers > 20
    header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
    section_pattern = re.compile(r'^[A-Z\s]{4,}$')

    for el in elements:
        text = el.page_content.strip()
        
        # Noise Filter
        if len(text) < 2 or (text.isdigit() and int(text) > 20): 
            continue
        
        is_header = header_pattern.match(text)
        is_section = section_pattern.match(text) and len(text) < 50
        
        if is_header or is_section:
            # Merge "Lonely Headers" logic
            if len(current_chunk_text) < 20:
                current_heading = f"{current_heading} > {text}"
                current_chunk_text += f" {text}"
                continue

            chunks.append(Document(
                page_content=current_chunk_text, 
                metadata={"heading": current_heading}
            ))
            
            current_heading = text
            current_chunk_text = text + " "
        else:
            current_chunk_text += f"\n{text}"
            
    if current_chunk_text:
        chunks.append(Document(
            page_content=current_chunk_text, 
            metadata={"heading": current_heading}
        ))
        
    return chunks

if __name__ == "__main__":
    target_pdf = "docs/fih-rules-of-hockey-June23-update.pdf"
    
    results = extract_chunks(target_pdf)
    
    print(f"\n✅ Extraction Complete. Found {len(results)} logical rules.\n")
    print("="*60)
    
    for doc in results:
        print(f"rule: {doc.metadata['heading']}")
        print(doc.page_content.strip())
        print("-" * 30)