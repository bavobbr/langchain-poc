"""Inspect Cloud SQL table schema and library view for debugging."""
import asyncio
import sqlalchemy
from langchain_google_cloud_sql_pg import PostgresEngine, Column
import config

# --- 1. APPLY THE SAME PATCH (To test if it works) ---
def column_hash(self):
    return hash(self.name)

def column_eq(self, other):
    # This matches the patch in rag_engine.py
    # It prints debug info if it compares 'variant'
    if self.name == 'variant' or getattr(other, 'name', '') == 'variant':
        print(f"   🔍 Comparing '{self.name}' ({self.data_type}) vs '{other.name}' ({other.data_type})")
        print(f"      Result: {self.name == other.name}")
    return hasattr(other, 'name') and self.name == other.name

Column.__hash__ = column_hash
Column.__eq__ = column_eq
# -----------------------------------------------------

async def inspect_schema():
    print(f"🔌 Connecting to {config.INSTANCE_NAME}...")
    engine = await PostgresEngine.afrom_instance(
        project_id=config.PROJECT_ID,
        region=config.REGION,
        instance=config.INSTANCE_NAME,
        database=config.DATABASE_NAME,
        user=config.DB_USER,
        password=config.DB_PASS
    )

    table_name = config.TABLE_NAME
    print(f"📊 Inspecting Table: {table_name}")

    # 1. RAW SQL INSPECTION (The Truth)
    # We query the system catalog directly to see what Postgres actually holds.
    async with engine._engine.connect() as conn:
        stmt = sqlalchemy.text(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}';
        """)
        result = await conn.execute(stmt)
        rows = result.fetchall()
        
        print("\n--- [1] POSTGRES RAW SCHEMA ---")
        if not rows:
            print("❌ TABLE NOT FOUND! The query returned 0 rows.")
        else:
            found_variant = False
            for r in rows:
                print(f"   - {r[0]} ({r[1]}) | Nullable: {r[2]}")
                if r[0] == 'variant':
                    found_variant = True
            
            if found_variant:
                print("✅ 'variant' column EXISTS in SQL.")
            else:
                print("❌ 'variant' column MISSING from SQL.")

    # 2. LIBRARY INSPECTION (The Python View)
    # We ask the library to load what it thinks the columns are.
    print("\n--- [2] PYTHON LIBRARY VIEW ---")
    try:
        # This is the internal method the library uses to validate
        columns_in_python = await engine._load_document_table(table_name)
        print(f"   Library found {len(columns_in_python)} columns:")
        for col in columns_in_python:
            print(f"   - Column(name='{col.name}', data_type='{col.data_type}')")
            
        # 3. THE EQUALITY TEST
        print("\n--- [3] VALIDATION SIMULATION ---")
        my_column = Column("variant", "text")
        
        if my_column in columns_in_python:
            print("✅ SUCCESS: Python successfully found your column in the list.")
        else:
            print("❌ FAILURE: Python could NOT match your column to the DB list.")
            print("   (This is why the app crashes)")

    except Exception as e:
        print(f"❌ Could not load table via library: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_schema())
