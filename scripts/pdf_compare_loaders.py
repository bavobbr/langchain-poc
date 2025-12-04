"""Compare PDF loaders (PyPDF, PDFPlumber, Unstructured) with diagnostics."""
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader, UnstructuredPDFLoader

def test_loader(name, loader_class, file_path):
    print(f"\n--- Testing {name} ---")
    try:
        # Load the document
        loader = loader_class(file_path)
        docs = loader.load()
        
        # Grab text from a specific page (e.g., Page 13 in your screenshot)
        # Note: Arrays are 0-indexed, so Page 13 is index 12
        target_page_index = 13
        
        if len(docs) > target_page_index:
            content = docs[target_page_index].page_content
            # Print the first 500 characters to see the reading order
            print(f"📄 Content Preview (Page {target_page_index + 1}):")
            print(content[:500]) 
            print("...")
            
            # Diagnostic Check
            # We want to see: "2.1 A maximum..."
            # We DO NOT want: "2.1 2.2 ... A maximum"
            if "2.1" in content and "A maximum" in content:
                index_num = content.find("2.1")
                index_text = content.find("A maximum")
                print(f"\n📊 Diagnostics:")
                print(f"   Position of '2.1': {index_num}")
                print(f"   Position of 'A maximum': {index_text}")
                
                if index_num < index_text:
                    print("   ✅ SUCCESS: Header appears BEFORE text.")
                else:
                    print("   ❌ FAILURE: Header appears AFTER text (Columnar read error).")
        else:
            print("   ⚠️ Page not found.")
            
    except Exception as e:
        print(f"   ❌ Crashed: {e}")

if __name__ == "__main__":
    pdf_path = "docs/fih-rules-of-hockey-June23-update.pdf"
    
    # 1. Test PyPDF (Likely the winner)
    test_loader("PyPDF (Stream Based)", PyPDFLoader, pdf_path)
    
    # 2. Test PDFPlumber (Precision)
    test_loader("PDFPlumber (Layout Based)", PDFPlumberLoader, pdf_path)
    
    # 3. Test Unstructured Fast (Baseline)
    # Note: We pass strategy="fast" via kwargs if we were initializing directly, 
    # but the LangChain wrapper defaults vary. 
    test_loader("Unstructured (Default)", UnstructuredPDFLoader, pdf_path)
