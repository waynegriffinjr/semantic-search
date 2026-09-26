import streamlit as st
import chromadb
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer


# =============================================================================
# CONFIGURATION
# =============================================================================
# Keeping these values in one place makes the application easier to configure.
# Instead of searching through the entire program for numbers like 400 or 50,
# we can change them here and the rest of the application uses the new values.

# Folder containing the documents we want to search.
DOCS_DIR   = Path("docs")

# Maximum number of characters in each chunk of text.
# (CHARACTER-based chunking), not word-based chunking. 
CHUNK_SIZE = 500

# Overlap helps preserve context when an important sentence happens to fall 
# across the boundary between two chunks.
OVERLAP    = 100

# Default number of search results to return.
N_RESULTS  = 5

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
# This controls the browser tab title, page icon, and overall layout.

st.set_page_config(
    page_title="Semantic Search",
    page_icon="🔍",
    layout="wide"
)
# =============================================================================
# Model & ChromaDB
# =============================================================================
@st.cache_resource
def load_resources():
    """
        Load the resources that should persist between Streamlit reruns.
    
        @st.cache_resource tells Streamlit:
            "Create these resources once and reuse them."
    
        Returns:
            model: SentenceTransformer model used for creating embeddings.
            collection: ChromaDB collection containing our document chunks.
        """
    
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="docs_search")
    return model, collection

# Run the function once and store the returned resources.
model, collection = load_resources()


# =============================================================================
# DOCUMENT LOADING & CHUNKING
# =============================================================================
def load_and_chunk(
    directory: str,
    size: int = CHUNK_SIZE,
    overlap: int = OVERLAP
):
    """
    Load .txt and .md files and divide their contents into chunks.
    Args:
            directory:
                Folder containing the documents.
            size:
                Maximum number of characters per chunk.
            overlap:
                Number of characters shared between consecutive chunks.
    Returns:
        A list of dictionaries. Each dictionary represents one chunk.   
        """
    
    # This list will eventually contain every chunk from every document.
    chunks = []
    
    # os.listdir() gives us the filenames inside the directory.
    # sorted() makes the processing order predictable.
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(('.txt', '.md')):
            continue
        # Build the complete path to the document.
        filepath = os.path.join(directory, filename)
        # Open the document for reading.
        # encoding="utf-8" allows us to correctly read normal Unicode text.
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
                
        # Normalize white space
        # split() separates the text based on whitespace.
        # join() then puts it back together using single spaces.
        # This removes excessive spaces, tabs, and newlines.
        content = " ".join(content.split())
        
        start = 0
        chunk_index = 0
        
        # Continue creating chunks until we've reached the end of
        # the document.
        while start < len(content):
            end = start + size
            
            chunk = content[start:end].strip()
        
         
            if chunk:
                chunks.append({
                    "text"       : chunk,
                    "source"     : filename,
                    "chunk_id"   : f"{filename}_{chunk_index}",
                    "chunk_index": chunk_index,
                })
            
            start += size - overlap
            chunk_index += 1
    
    return chunks

 
def get_relevance_badge(distance):
    """
    Converts the ChromaDB distance into a relevance level.
    ChromaDB distance:
        Lower distance = more similar
        Higher distance = less similar
    Returns:
        A relevance label and a color for the badge.
    """
    if distance < 0.5:
        return "Highly Relevant", "green"
    elif distance < 1:
        return "Moderately Relevant", "yellow"
    else:
        return "Low Relevance", "red"
 
# =============================================================================
# SIDEBAR — DOCUMENT MANAGEMENT
# ============================================================================= 
with st.sidebar:
    st.title("📂 Document Manager")
    
    if st.button("🔃 Re-index Documents"):
        
        chunks = load_and_chunk("docs")
        st.write(f"Found {len(chunks)} chunks")
        
        # Remove all existing chunks
        existing_ids = collection.get()["ids"]

        if chunks:
            
            existing_ids = collection.get()["ids"]
            
            if existing_ids:
                collection.delete(ids=existing_ids)
        
        
            collection.add(
                documents=[c["text"] for c in chunks],
                metadatas=[
                    {"source": c ["source"],
                     "chunk_index": str(c["chunk_index"])
                     }
                    for c in chunks
                ],
                ids=[c["chunk_id"] for c in chunks],
            )
            
            
            # Tell the user what happened.
            # set() removes duplicate filenames, so we can report the
            # number of actual source documents rather than the number
            # of chunks.
            st.success(
                f"Indexed {len(chunks)} chunks from "
                f"{len(set(c['source'] for c in chunks))} files"
            )
            
        else:
            st.warning("No .txt or .md files found in docs/ folder")
            
    st.metric("Documents in DB", collection.count())
    
    st.divider()
    n_results = st.slider("Results to show", 1, 10, 5)
    
    #-----Filters______________________________________________________________
    st.sidebar.header("Filters")

    # Fetch all metadata dictionaries from the Chroma collection
    metadata_list = collection.get(include=["metadatas"])["metadatas"]

    # Extract the unique source filenames (handling potential missing keys)
    source_filenames = sorted({meta.get("source") for meta in metadata_list if isinstance(meta, dict) and meta.get("source")})
        
    selected_sources = st.multiselect(
    "Select Your Sources",
    options=source_filenames,
    default=source_filenames,
    ) 

    

# --- Main Search Interface ---
st.title("🔍 Semantic Search")
st.write("Search your documents by meaning, not just keywords.")

query = st.text_input("Enter your search query", placeholder="Type a question or phrase...")

if query and collection.count() > 0:
    
    if len(selected_sources) == 1:
        where_filter = {"source": selected_sources[0]}
    elif len(selected_sources) > 1:
        where_filter = {"source": {"$in": selected_sources}}
    else:
        where_filter = None 

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        where=where_filter
    )
    
    if results["documents"] and results["documents"][0]:
        
        # Show how many documents are being searched
        total_documents = len(source_filenames)

        st.write(
            f"Showing {len(results['documents'][0])} "
            f"of {total_documents} total documents"
        )

        # ---------------------------------------------------------------------
        # LOOP THROUGH EACH SEARCH RESULT
        # ---------------------------------------------------------------------
        for i in range(
            len(results["documents"][0])
        ):

            doc = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            # Create a 150-character preview
            preview = doc[:150]

            if len(doc) > 150:
                preview += "..."

            # ============================
            # Display source and distance
            # ============================
            # Determine the relevance level based on the ChromaDB distance
            relevance, color = get_relevance_badge(distance)
            
            # Display the source filename
            st.subheader(metadata["source"])
            
            # Display a colored relevance badge
            st.markdown(
                f"""
                <span style="
                    background-color: {color};
                    color: white;
                    padding: 5px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 0.85rem;
                ">
                    {relevance}
                </span>
                &nbsp;&nbsp;
                <span>
                    Distance: {distance:.3f}
                </span>
                """,
                unsafe_allow_html=True
)

            # Display preview
            st.write(preview)

            # Expand to show complete chunk
            with st.expander("Show full text"):
                st.write(doc)

        else: st.warning("No results found for the selected sources.")
    
# If there aren't any chunks in ChromaDB, tell the user how to populate it.
elif collection.count() == 0:
    st.info(
        "👈 Click 'Re-index Documents' in the sidebar to load your documents first."
    )
 
# This stores the total number of chunks in a variable for later use debugging or for adding another statistic to the interface.
total = collection.count()

  

                