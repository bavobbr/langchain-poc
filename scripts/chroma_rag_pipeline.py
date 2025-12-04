"""End-to-end RAG pipeline using local Chroma vector store."""
import os
import re
import shutil
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- CONFIGURATION ---
PROJECT_ID = "langchain-poc-479114"
REGION = "europe-west1"
DB_PATH = "./chroma_db"

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

def smarter_chunking(elements):
    print(f"--- Processing {len(elements)} raw elements ---")
    chunks = []
    current_chunk_text = ""
    current_heading = "Front Matter"
    
    # REGEX EXPLANATION:
    # 1. (Rule\s+)?        : Optional "Rule " prefix
    # 2. ([1-9]|1[0-9])    : Main Rules 1-19
    # 3. (\.\d+)+          : MUST have a decimal section (e.g. "9.1", "9.12"). 
    #                        This EXCLUDES standalone page numbers like "12" or "9".
    # 4. | (Rule\s+\d+)    : OR explicit "Rule 9" (if the PDF has that format)
    header_pattern = re.compile(r'^((Rule\s+)?([1-9]|1[0-9])(\.\d+)+|Rule\s+\d+)$', re.IGNORECASE)
    
    section_pattern = re.compile(r'^[A-Z\s]{4,}$')

    for el in elements:
        text = el.page_content.strip()
        # Filter noise: Skip tiny text or page numbers > 20
        if len(text) < 2 or (text.isdigit() and int(text) > 20): continue

        is_rule_num = header_pattern.match(text)
        is_section_title = section_pattern.match(text) and len(text) < 50
        
        if is_rule_num or is_section_title:
            # Merge lonely headers (e.g. "9.4" followed by "9.5")
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
    
    # --- AUDIT ---
    print("\n--- 🕵️ INGESTION AUDIT ---")
    for doc in chunks:
        if "back of the stick" in doc.page_content.lower():
            print(f"🎯 SUCCESS: Found 'back of stick' in chunk: '{doc.metadata['heading']}'")
            # print(f"   Snippet: {doc.page_content[:100]}...")
            return chunks
            
    print("⚠️ WARNING: The text 'back of the stick' was NOT found.")
    return chunks

def run_rag_pipeline(pdf_path, query):
    # 2. Reset DB
    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    # 3. Ingest
    print("\n--- 2. Loading & Chunking ---")
    loader = UnstructuredPDFLoader(pdf_path, mode="elements")
    docs = smarter_chunking(loader.load())
    
    # 4. Embed
    print("\n--- 3. Embedding to Disk ---")
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="hockey_rules",
        persist_directory=DB_PATH
    )
    
    # 5. Retrieve (High Recall)
    print(f"\n--- 4. Querying (k=15): '{query}' ---")
    retriever = vector_store.as_retriever(search_kwargs={"k": 15})
    relevant_docs = retriever.invoke(query)
    
    print(f"   Retrieved {len(relevant_docs)} chunks.")

    # 6. Generate
    print("\n--- 5. Generating Answer ---")
    context_text = "\n\n".join([d.page_content for d in relevant_docs])
    
    prompt = f"""
    You are an expert FIH Hockey Umpire. 
    Answer the question strictly based on the provided Context.
    Cite the Rule Number.
    
    CONTEXT:
    {context_text}
    
    QUESTION:
    {query}
    """
    
    response = llm.invoke(prompt)
    print(f"\n🤖 GEMINI ANSWER:\n{response}")

if __name__ == "__main__":
    pdf_file = "docs/fih-rules-of-hockey-June23-update.pdf" 
    user_query = "What happens if a defender uses the back of their stick inside the circle?"
    run_rag_pipeline(pdf_file, user_query)
