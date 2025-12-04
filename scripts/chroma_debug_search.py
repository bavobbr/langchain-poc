"""Debug similarity search in a local Chroma collection."""
from langchain_chroma import Chroma
from langchain_google_vertexai import VertexAIEmbeddings

# Config
PROJECT_ID = "langchain-poc-479114" # Use your ID
REGION = "europe-west1"

embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004", 
    project=PROJECT_ID,
    location=REGION
)

# Connect to existing DB
vector_store = Chroma(
    collection_name="hockey_rules",
    embedding_function=embeddings,
    persist_directory="./chroma_db" # Default location
)

def find_missing_rule(rule_text="back of the stick"):
    print(f"--- 🕵️ Debugging: Hunting for '{rule_text}' ---")
    
    # 1. Search for the specific keyword "back of the stick"
    results = vector_store.similarity_search(rule_text, k=3)
    
    found = False
    for i, doc in enumerate(results):
        print(f"\n[Result {i}] Heading: {doc.metadata.get('heading')}")
        print(f"Content Snippet: {doc.page_content[:150]}...")
        
        if rule_text in doc.page_content:
            found = True
            print("✅ FOUND IT! The text is in the database.")
            
    if not found:
        print("\n❌ NOT FOUND. The chunking logic deleted this rule.")

if __name__ == "__main__":
    find_missing_rule("player")
