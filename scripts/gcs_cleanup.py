
"""
Cleanup Script for GCS Bucket (Dangerous)

Deletes all objects in the known staging folders:
- uploads/
- processed/
- repro_output/
"""
import config
from google.cloud import storage

def clean_bucket():
    bucket_name = config.GCS_BUCKET_NAME
    print(f"🔥 Targeting Bucket: {bucket_name}")
    
    storage_client = storage.Client(project=config.PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)

    prefixes_to_clean = ["uploads/", "processed/", "repro_output/"]
    
    total_deleted = 0
    
    for prefix in prefixes_to_clean:
        print(f"   Scanning prefix: '{prefix}'...")
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            print("     -> Empty.")
            continue
            
        print(f"     -> Found {len(blobs)} files. Deleting...")
        # Batch delete is more efficient but simple iteration is safer/easier to follow in logs
        for blob in blobs:
            blob.delete()
            total_deleted += 1
            
    print(f"✅ Cleanup Complete. Deleted {total_deleted} files/objects.")

if __name__ == "__main__":
    clean_bucket()
