"""
List Document AI Processors in US and EU regions.
"""
from google.cloud import documentai
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "langchain-poc-479114")

def list_processors(location):
    print(f"--- Listing Processors in {location} ---")
    opts = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    parent = client.common_location_path(PROJECT_ID, location)
    
    try:
        processors = client.list_processors(parent=parent)
        for p in processors:
            print(f"ID: {p.name.split('/')[-1]} | Display Name: {p.display_name} | State: {p.state}")
    except Exception as e:
        print(f"Error listing {location}: {e}")

if __name__ == "__main__":
    list_processors("us")
    list_processors("eu")
