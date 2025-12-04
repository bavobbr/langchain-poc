"""Truncate the vector table in Cloud SQL (dangerous, for dev use)."""
import sqlalchemy
from langchain_google_cloud_sql_pg import PostgresEngine
import config
import asyncio

async def wipe_database():
    print(f"🔥 Connecting to {config.INSTANCE_NAME}...")
    
    # 1. Initialize the Engine (using your existing Config)
    engine = await PostgresEngine.afrom_instance(
        project_id=config.PROJECT_ID,
        region=config.REGION,
        instance=config.INSTANCE_NAME,
        database=config.DATABASE_NAME,
        user=config.DB_USER,
        password=config.DB_PASS
    )

    # 2. Define the Table Name
    table_name = config.TABLE_NAME

    # 3. Execute Truncate (Wipe all data)
    print(f"⚠️  Wiping table '{table_name}'...")
    
    # We use a raw SQL command here
    async with engine._engine.connect() as conn:
        await conn.execute(sqlalchemy.text(f"TRUNCATE TABLE {table_name};"))
        await conn.commit()
        
    print("✅ Database is empty. Ready for new labeled data!")

if __name__ == "__main__":
    asyncio.run(wipe_database())
