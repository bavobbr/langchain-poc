import asyncio
import re
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_google_cloud_sql_pg import PostgresEngine, PostgresVectorStore
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.documents import Document

# --- CONFIGURATION ---
PROJECT_ID = "langchain-poc-479114"
REGION = "europe-west1"
INSTANCE_NAME = "fih-rag-db"  # Must match the gcloud command
DATABASE_NAME = "hockey_db"
TABLE_NAME = "hockey_rules_vectors"

# 1. Initialize Models
print("--- 1. Initializing Cloud Models ---")
llm = VertexAI(
    model_name="gemini-2.0-flash-lite",
    project=PROJECT_ID,
    location=REGION,
    temperature=0
)

embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004", 
    project=PROJECT_ID,
    location=REGION
)

# --- THE PROVEN CHUNKING LOGIC ---
def smarter_chunking(elements):
    print(f"--- Processing {len(elements)} raw elements ---")
    chunks = []
    current_chunk_text = ""
    current_heading = "Front Matter"
    
    # The Regex that worked: 
    # Catch Rules 1-19 (ignoring page numbers > 20)
    # Must have decimal OR be explicit "Rule X"
    header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
    section_pattern = re.compile(r'^[A-Z\s]{4,}$')

    for el in elements:
        text = el.page_content.strip()
        if len(text) < 2 or (text.isdigit() and int(text) > 20): continue

        is_rule_num = header_pattern.match(text)
        is_section_title = section_pattern.match(text) and len(text) < 50
        
        if is_rule_num or is_section_title:
            if len(current_chunk_text) < 20:
                current_heading = f"{current_heading} > {text}"
                current_chunk_text += f" {text}" 
                continue 

            chunks.append(Document(
                page_content=current_chunk_text, 
                metadata={"source": "FIH_Rules", "heading": current_heading}
            ))
            
            current_heading = text 
            current_chunk_text = text + " "
        else:
            current_chunk_text += f"\n{text}"

    if current_chunk_text:
        chunks.append(Document(
            page_content=current_chunk_text, 
            metadata={"source": "FIH_Rules", "heading": current_heading}
        ))
    
    print(f"✅ Aggregated into {len(chunks)} semantic chunks.")
    return chunks

async def main():
    # 2. Connect to Cloud SQL (Securely)
    print(f"--- 2. Connecting to Cloud SQL ({INSTANCE_NAME})... ---")
    # Change the engine creation to use the admin user/password explicitly
    engine = await PostgresEngine.afrom_instance(
        project_id=PROJECT_ID,
        region=REGION,
        instance=INSTANCE_NAME,
        database=DATABASE_NAME,
        user="postgres",           # <--- Force admin user
        password="StartWithStrongPassword123!" # <--- Your password
    )

    # 3. Initialize/Create the Vector Table
    print("--- 3. Checking Database Schema ---")
    await engine.ainit_vectorstore_table(
        table_name=TABLE_NAME,
        vector_size=768  # Matches text-embedding-004
    )

    vector_store = await PostgresVectorStore.create(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embeddings
    )

    # 4. Ingestion Check
    # We perform a quick search. If it's empty, we ingest.
    # This prevents re-uploading every time you run the script.
    print("--- 4. Verifying Data ---")
    results = await vector_store.asimilarity_search("hockey", k=1)
    
    if not results:
        print("   Database is empty. Ingesting PDF now...")
        loader = UnstructuredPDFLoader("docs/fih-rules-of-hockey-June23-update.pdf", mode="elements")
        docs = smarter_chunking(loader.load())
        await vector_store.aadd_documents(docs)
        print(f"   ✅ Uploaded {len(docs)} chunks to Postgres!")
    else:
        print("   ✅ Database already contains data. Skipping ingestion.")

    # 5. Retrieval & Generation
    query = "What happens if a defender uses the back of their stick inside the circle?"
    print(f"\n--- 5. Querying: '{query}' ---")
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 15})
    relevant_docs = await retriever.ainvoke(query)
    
    print(f"   Retrieved {len(relevant_docs)} chunks from Cloud SQL.")

    print("\n--- 6. Generating Answer ---")
    context_text = "\n\n".join([d.page_content for d in relevant_docs])
    
    prompt = f"""
    You are an expert FIH Hockey Umpire. 
    Answer strictly based on the Context. Cite the Rule Number.
    
    CONTEXT:
    {context_text}
    
    QUESTION:
    {query}
    """
    
    # Note: VertexAI (LLM) is synchronous, so we don't await the invoke
    response = llm.invoke(prompt)
    print(f"\n🤖 GEMINI ANSWER:\n{response}")

if __name__ == "__main__":
    asyncio.run(main())