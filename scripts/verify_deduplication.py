"""
Verification Script for Idempotent Ingestion (Deduplication)

1. Inserts dummy records into Postgres for a test variant.
2. Calls `delete_variant`.
3. Verifies records are gone.
"""
import sys
from database import PostgresVectorDB
from sqlalchemy import text

def verify_deduplication():
    print("--- Verifying Deduplication (Idempotency) ---")
    db = PostgresVectorDB()
    variant = "dedup_test_variant"

    display_name = "Dedup Test"
    
    # 0. Clean start
    print(f"0. Cleaning any leftover data for '{variant}'...")
    db.delete_variant(variant)

    # 1. Setup: Insert Dummy Data
    print(f"1. Inserting dummy data for variant '{variant}'...")
    dummy_text = ["test_chunk_1", "test_chunk_2"]
    dummy_vectors = [[0.1]*768, [0.2]*768] # Dim must match DB schema (usually 768)
    
    # Check current dim
    # We assume schema is already set. If invalid dim error, we might need to check config.
    # The default embedding model (Gecko) is 768.
    
    db.insert_batch(dummy_text, dummy_vectors, variant)
    
    # Check count
    import config
    table_name = config.TABLE_NAME

    with db.pool.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE variant = :v"), {"v": variant}).scalar()
        # Note: Table name might be 'params' or 'langchain_pg_embedding' or whatever config says.
        # Let's check config.TABLE_NAME
        
    # Re-reading config to get table name implementation detail
    import config
    table_name = config.TABLE_NAME
    
    with db.pool.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE variant = :v"), {"v": variant}).scalar()
    
    print(f"   -> Rows found: {count}")
    if count != 2:
        print("❌ Setup failed. Rows not inserted.")
        return

    # 2. Test Deletion
    print(f"2. Calling delete_variant('{variant}')...")
    db.delete_variant(variant)

    # 3. Verify
    with db.pool.connect() as conn:
        final_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE variant = :v"), {"v": variant}).scalar()
    
    print(f"   -> Rows found: {final_count}")
    
    if final_count == 0:
        print("✅ SUCCESS! Data successfully cleared.")
    else:
        print(f"❌ FAILURE! {final_count} rows remain.")

if __name__ == "__main__":
    verify_deduplication()
