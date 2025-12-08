
import time
import sys
import os

# Measure time to import rag_engine
start = time.time()
print("Importing rag_engine...")
import rag_engine
end = time.time()
print(f"rag_engine import took {end - start:.4f} seconds")

# Verify langchain_google_vertexai is NOT in sys.modules (meaning it wasn't imported)
if "langchain_google_vertexai" in sys.modules:
    print("❌ FAILURE: langchain_google_vertexai was imported eagerly!")
else:
    print("✅ SUCCESS: langchain_google_vertexai is lazy loaded.")

# Verify loaders is NOT in sys.modules
if "loaders" in sys.modules:
    print("❌ FAILURE: loaders was imported eagerly!")
else:
    print("✅ SUCCESS: loaders is lazy loaded.")
