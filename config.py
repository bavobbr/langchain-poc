import os

# Google Cloud & Infra
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "langchain-poc-479114")
REGION = os.getenv("GCP_REGION", "europe-west1")

# Database Credentials
INSTANCE_NAME = os.getenv("CLOUDSQL_INSTANCE", "fih-rag-db")
DATABASE_NAME = "hockey_db"
TABLE_NAME = "hockey_rules_vectors"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "StartWithStrongPassword123!")

# Model Config
EMBEDDING_MODEL = "text-embedding-004"
LLM_MODEL = "gemini-2.0-flash-lite"
RETRIEVAL_K = 15

# NEW: Supported Variants
# Key = Database Label, Value = UI Display Name
VARIANTS = {
    "outdoor": "Outdoor Hockey (Default)",
    "indoor": "Indoor Hockey",
    "hockey5s": "Hockey 5s"
}