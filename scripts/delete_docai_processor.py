"""
Delete a specific Document AI Processor.
"""
from google.cloud import documentai
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "langchain-poc-479114")
LOCATION = "us"
PROCESSOR_ID = "53a6fece2d33c37"

def delete_processor():
    print(f"🔥 Deleting Processor {PROCESSOR_ID} in {LOCATION}...")
    opts = {"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    
    try:
        operation = client.delete_processor(name=name)
        print("   Waiting for operation...")
        operation.result()
        print("✅ Processor deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete processor: {e}")

if __name__ == "__main__":
    delete_processor()
