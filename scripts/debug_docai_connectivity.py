import os
import sys
import time
from google.cloud import storage
from google.cloud import documentai
from google.cloud import resourcemanager_v3
from google.iam.v1 import policy_pb2

# Config
PROJECT_ID = "langchain-poc-479114"
LOCATION = "us"
PROCESSOR_ID = "53a6fece2d33c37" # From setup script output
BUCKET_NAME = "fih-rag-staging-us-langchain-poc-479114"

# Known Service Agent formats
SA_CORE = f"service-{881796397796}@gcp-sa-prod-dai-core.iam.gserviceaccount.com"
SA_LEGACY = f"service-{881796397796}@gcp-sa-documentai.iam.gserviceaccount.com"

def check_bucket_access():
    print(f"\n--- 1. Checking Bucket Access ({BUCKET_NAME}) ---")
    client = storage.Client(project=PROJECT_ID)
    try:
        bucket = client.get_bucket(BUCKET_NAME)
        print(f"✅ Can access bucket: {bucket.name}")
        
        # List files to find a candidate
        blobs = list(bucket.list_blobs(max_results=5, prefix="uploads/"))
        if not blobs:
            print("❌ No files found in uploads/ folder.")
            return None
            
        print(f"✅ Found {len(blobs)} files. Using first one:")
        target_blob = blobs[0]
        print(f"   - {target_blob.name} ({target_blob.size} bytes)")
        return f"gs://{BUCKET_NAME}/{target_blob.name}"
    except Exception as e:
        print(f"❌ Failed to access bucket: {e}")
        return None

def check_bucket_iam():
    print(f"\n--- 2. Checking Bucket IAM Policy ---")
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    policy = bucket.get_iam_policy(requested_policy_version=3)
    
    found_sa = False
    for binding in policy.bindings:
        for member in binding['members']:
            if SA_CORE in member:
                print(f"✅ Found SA ({SA_CORE}) with role: {binding['role']}")
                found_sa = True
            elif "documentai" in member:
                print(f"⚠️ Found potential DocAI member: {member} with role: {binding['role']}")
    
    if not found_sa:
        print(f"❌ WARNING: Did not find {SA_CORE} in bucket-level IAM.")

def start_online_process(gcs_uri):
    print(f"\n--- 3. Testing Processor (Online Mode) ---")
    if LOCATION == "us":
        opts = {"api_endpoint": "documentai.googleapis.com"}
    else:
        opts = {"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    
    # Download file locally first
    blob_name = gcs_uri.replace(f"gs://{BUCKET_NAME}/", "")
    client_storage = storage.Client(project=PROJECT_ID)
    bucket = client_storage.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    file_content = blob.download_as_bytes()
    
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    
    print(f"   Sending {len(file_content)} bytes to Online API...")
    
    # Configure request
    raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")
    
    try:
        request = documentai.ProcessRequest(
            name=name,
            raw_document=raw_document
        )
        result = client.process_document(request=request)
        print("✅ Online Processing Successful!")
        print(f"   Extracted {len(result.document.text)} chars.")
        return True
    except Exception as e:
        print(f"❌ Online Operation Failed:\n{e}")
        return False

if __name__ == "__main__":
    file_uri = check_bucket_access()
    # check_bucket_iam() # Skip IAM check for Online
    
    if file_uri:
        # start_batch_process(file_uri)
        start_online_process(file_uri)
