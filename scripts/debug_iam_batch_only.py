
"""
Minimal Reproduction Script for Document AI 403 Error (Support Case)

This script isolates the interaction between Document AI and GCS.
1. Lists a file in the GCS bucket to confirm client access.
2. Calls `batch_process_documents` with that file.
3. Prints the Operation ID (Success) or the Error (Failure).

REQUIREMENTS:
- google-cloud-documentai
- google-cloud-storage
- Authenticated environment (Application Default Credentials)
"""

import os
import sys
from google.cloud import documentai
from google.cloud import storage

# --- CONFIGURATION (EU Region) ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "langchain-poc-479114")
LOCATION = os.getenv("DOCAI_LOCATION", "eu")
PROCESSOR_ID = os.getenv("DOCAI_PROCESSOR_ID", "2699879b692a67f") 
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "fih-rag-staging-langchain-poc-479114")
# ------------------------------------------------------------

def reproduce_iam_issue():
    print(f"--- Document AI IAM Reproduction Script ---")
    print(f"Project: {PROJECT_ID}")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Processor: projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}")
    print("-" * 50)

    # 1. Verify GCS Access (Client Check)
    print("STEP 1: Finding a file in GCS bucket...")
    storage_client = storage.Client(project=PROJECT_ID)
    try:
        blobs = list(storage_client.list_blobs(BUCKET_NAME, max_results=50))
        pdf_blob = None
        for blob in blobs:
            if blob.name.lower().endswith(".pdf"):
                pdf_blob = blob
                break
        
        if not pdf_blob:
            print("❌ No PDF found in bucket! Please upload a test PDF first.")
            return
        
        gcs_input_uri = f"gs://{BUCKET_NAME}/{pdf_blob.name}"
        print(f"✅ Found File: {gcs_input_uri}")

    except Exception as e:
        print(f"❌ Failed to list GCS bucket: {e}")
        return

    # 2. Trigger Document AI Batch Job
    print("\nSTEP 2: Triggering Document AI Batch Process...")
    docai_client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    )
    
    name = docai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    destination_uri = f"gs://{BUCKET_NAME}/repro_output/"

    # Input Config
    input_config = documentai.BatchDocumentsInputConfig(
        gcs_documents=documentai.GcsDocuments(
            documents=[{"gcs_uri": gcs_input_uri, "mime_type": "application/pdf"}]
        )
    )
    # Output Config
    output_config = documentai.DocumentOutputConfig(
        gcs_output_config={"gcs_uri": destination_uri}
    )

    try:
        request = documentai.BatchProcessRequest(
            name=name,
            input_documents=input_config,
            document_output_config=output_config,
        )
        
        operation = docai_client.batch_process_documents(request=request)
        print(f"✅ SUCCESS! Job submitted.")
        print(f"Operation Name: {operation.operation.name}")
        print("\nNote: Validating if Service Agent has access... (this might take a few seconds to fail if async)")
        # Just check status briefly or return
        print("Support info: If you see an Operation Name, the API call succeeded.")
        
    except Exception as e:
        print(f"❌ FAILED to submit job.")
        print(f"Error details:\n{e}")

if __name__ == "__main__":
    reproduce_iam_issue()
