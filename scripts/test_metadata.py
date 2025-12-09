"""
Verification Script for Metadata Support

1. Ingests dummy text with metadata ('heading': 'Rule 99').
2. Searches for the text.
3. Verifies that the returned document includes the original metadata.
"""
import sys
from database import PostgresVectorDB
from langchain_core.documents import Document

def verify_metadata():
    print("--- Verifying Metadata Storage ---")
    db = PostgresVectorDB()
    variant = "metadata_test"
    
    # 0. Clean start
    print(f"0. Cleaning variant '{variant}'...")
    db.delete_variant(variant)

    # 1. Insert Dummy Data with Metadata
    print(f"1. Inserting dummy data...")
    contents = ["A penalty corner is awarded..."]
    vectors = [[0.1]*768] # Dummy vector
    metadatas = [{"heading": "Rule 99.1", "source": "Test Script"}]
    
    db.insert_batch(contents, vectors, variant, metadatas=metadatas)
    
    # 2. Search and Verify
    print(f"2. Searching...")
    # We search with the same vector to ensure a hit
    results = db.search(vectors[0], variant, k=1)
    
    if not results:
        print("❌ Search failed. No results found.")
        sys.exit(1)
        
    doc = results[0]
    print(f"   -> Result Metadata: {doc['metadata']}")
    
    expected_heading = "Rule 99.1"
    actual_heading = doc['metadata'].get("heading")
    
    if actual_heading == expected_heading:
        print(f"✅ SUCCESS! Metadata recovered: heading='{actual_heading}'")
    else:
        print(f"❌ FAILURE! Expected heading '{expected_heading}', got '{actual_heading}'")

if __name__ == "__main__":
    verify_metadata()
