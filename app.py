"""Streamlit UI for the FIH Rules RAG app.

Responsibilities:
- Initialize the engine and report health
- Ingest PDFs with a selected variant
- Provide a lightweight chat interface with routing info
"""

import traceback
import streamlit as st
import tempfile
import config
from rag_engine import FIHRulesEngine

st.set_page_config(page_title="FIH Rules Expert", page_icon="🏑")
st.title("🏑 FIH Rules AI Agent")

# Engine initialization (cached across reruns)
@st.cache_resource
def get_app_engine():
    """Create and cache the application engine (LLM + DB)."""
    return FIHRulesEngine()

try:
    engine = get_app_engine()
    st.success("✅ Connected to Cloud Knowledge Base")
except Exception as e:
    st.error(f"Failed to initialize engine: {e}")
    # Surface full traceback in the UI for local/cloud debugging
    st.markdown("### Debug Traceback:")
    st.exception(e)
    # Also emit to logs for post‑mortem diagnostics
    print("CRITICAL INITIALIZATION ERROR:")
    print(traceback.format_exc())
    st.stop()

# Sidebar: ingest a PDF with a selected ruleset variant
with st.sidebar:
    st.header("📚 Knowledge Base")
    
    # Select which ruleset the uploaded PDF belongs to
    selected_variant = st.selectbox(
        "Select Ruleset Variant",
        options=list(config.VARIANTS.keys()),
        format_func=lambda x: config.VARIANTS[x]
    )
    
    uploaded_file = st.file_uploader("Upload Rules PDF", type="pdf")
    
    if uploaded_file and st.button("Ingest"):
        with st.spinner(f"Indexing as {config.VARIANTS[selected_variant]}..."):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            # Persist with the selected variant label
            count = engine.ingest_pdf(tmp_path, selected_variant, original_filename=uploaded_file.name)
            st.success(f"Successfully indexed {count} rules for {selected_variant}!")

# --- CHAT UI ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question (e.g., 'What about indoor penalty corners?')..."):
    st.chat_message("user").markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Consulting the rulebook..."):
            history_list = [(m["role"], m["content"]) for m in st.session_state.messages]
            
            # Query the engine with recent message history
            result = engine.query(prompt, history=history_list)
            
            st.markdown(result["answer"])
            
            # Show routed ruleset and short source previews
            # Use a unique key to ensure the expander state (collapsed) is reset for every new query
            with st.expander("Debug: Routing & Sources", expanded=False):
                st.info(f"🚦 Router selected: **{result['variant'].upper()}**")
                st.write(f"**Reformulated Query:** {result['standalone_query']}")
                st.write("**Sources:**")
                for doc in result["source_docs"]:
                    source_file = doc.metadata.get("source_file", "unknown")
                    page_num = doc.metadata.get("page", "?")
                    st.caption(f"[{doc.metadata.get('variant', 'unknown')}] {doc.metadata.get('chapter', '')}  {doc.metadata.get('section', '')} {doc.metadata.get('heading', '')} ({source_file} p.{page_num})")
                    st.text("Summary:   ")
                    st.text(doc.metadata.get("summary", "No summary available"))

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
