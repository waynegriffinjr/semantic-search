# Determine the relevance level based on the ChromaDB distance.
relevance, color = get_relevance_badge(distance)

# Display the source filename.
st.subheader(metadata["source"])

# Display a colored relevance badge.
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
# =============================================================================
# Keeping these values in one place makes the application easier to configure.
# Instead of searching through the entire program for numbers like 400 or 50,
# we can change them here and the rest of the application uses the new values.

# Folder containing the documents we want to search.
DOCS_DIR = Path("docs")

# Maximum number of characters in each chunk of text.
#
# IMPORTANT:
# This is CHARACTER-based chunking, not word-based chunking.
# A value of 400 means each chunk will be approximately 400 characters long.
CHUNK_SIZE = 400

# Number of characters from the previous chunk that should overlap
# with the next chunk.
#
# Overlap helps preserve context when an important sentence happens to fall
# across the boundary between two chunks.
#
# Example:
#
# Chunk 1: characters 0 - 399
# Chunk 2: characters 350 - 749
#
# The two chunks therefore share 50 characters.
OVERLAP = 50

# Default number of search results to return.
N_RESULTS = 5


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
# MODEL & CHROMADB SETUP
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

    # Load a pretrained sentence-transformer model.
    #
    # Sentence Transformers convert text into numerical vectors called
    # embeddings. Text with similar meanings should have similar vectors.
    #
    # NOTE:
    # The model is loaded here but is not explicitly used later in this
    # version of the program. ChromaDB can create embeddings itself using
    # its configured/default embedding function.
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Create a persistent ChromaDB client.
    #
    # "PersistentClient" means ChromaDB stores its data on disk instead of
    # keeping everything only in memory.
    #
    # The database will be stored in:
    #
    #     ./chroma_db
    #
    # This means the indexed documents survive when Streamlit restarts.
    client = chromadb.PersistentClient(path="./chroma_db")

    # Get an existing collection named "docs_search", or create it if
    # it doesn't exist yet.
    #
    # A ChromaDB collection is roughly analogous to a table/container
    # that holds our documents, metadata, IDs, and embeddings.
    collection = client.get_or_create_collection(
        name="docs_search"
    )

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

    Why do we chunk documents?

    A large document is not ideal for semantic search as one giant piece of
    text. Instead, we divide it into smaller pieces.

    Each chunk becomes an individual searchable item in ChromaDB.

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
    #
    # sorted() makes the processing order predictable.
    for filename in sorted(os.listdir(directory)):

        # We only want Markdown and text files.
        #
        # Any other file type is skipped.
        if not filename.endswith((".txt", ".md")):
            continue

        # Build the complete path to the document.
        #
        # Example:
        #
        #     docs/python.md
        #
        filepath = os.path.join(directory, filename)

        # Open the document for reading.
        # encoding="utf-8" allows us to correctly read normal Unicode text.
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Normalize whitespace.
        #
        # split() separates the text based on whitespace.
        # join() then puts it back together using single spaces.
        #
        # This removes excessive spaces, tabs, and newlines.
        content = " ".join(content.split())

        # "start" represents the character position where our current
        # chunk begins.
        start = 0

        # Each chunk gets a sequential number:
        #
        #     0
        #     1
        #     2
        #     ...
        chunk_index = 0

        # Continue creating chunks until we've reached the end of
        # the document.
        while start < len(content):

            # Determine where the current chunk ends.
            #
            # If start = 0 and size = 400:
            #
            #     end = 400
            #
            end = start + size

            # Extract the current section of text.
            #
            # .strip() removes whitespace from the beginning and end.
            chunk = content[start:end].strip()

            # IMPORTANT:
            #
            # We check "chunk", NOT "chunks".
            #
            # "chunk" is the current piece of text.
            # "chunks" is the entire list of chunks created so far.
            #
            # This prevents empty chunks from being stored.
            if chunk:

                # Store information about this chunk in a dictionary.
                chunks.append({
                    "text": chunk,

                    # Keep track of which document this chunk came from.
                    "source": filename,

                    # Create a unique ID for this chunk.
                    #
                    # Example:
                    #
                    #     python.md_0
                    #     python.md_1
                    #     python.md_2
                    #
                    "chunk_id": f"{filename}_{chunk_index}",

                    # Store the chunk's position within the document.
                    "chunk_index": chunk_index,
                })

            # Move forward to the beginning of the next chunk.
            #
            # We subtract OVERLAP so that part of the previous chunk
            # is repeated in the next chunk.
            #
            # With size=400 and overlap=50:
            #
            #     400 - 50 = 350
            #
            # So the next chunk begins 350 characters after the current
            # chunk began.
            start += size - overlap

            # Move to the next chunk number.
            chunk_index += 1

    # Return the complete list of chunks.
    return chunks


# =============================================================================
# SIDEBAR — DOCUMENT MANAGEMENT
# =============================================================================

with st.sidebar:

    st.title("📂 Document Manager")

    # -------------------------------------------------------------------------
    # RE-INDEX DOCUMENTS BUTTON
    # -------------------------------------------------------------------------
    #
    # st.button() returns True only when the user clicks the button.
    #
    # This prevents the indexing operation from happening on every
    # Streamlit rerun.
    if st.button("🔃 Re-index Documents"):

        # Read all supported documents from the docs/ directory
        # and turn them into chunks.
        chunks = load_and_chunk("docs")

        # Temporary/diagnostic information showing us how many chunks
        # were created.
        #
        # This is particularly useful while developing and debugging.
        st.write(f"Found {len(chunks)} chunks")

        # Only continue if we actually found some chunks.
        if chunks:

            # Get the IDs of everything currently stored in ChromaDB.
            #
            # We do this because re-indexing should replace the old
            # contents with the current contents of the docs/ folder.
            existing_ids = collection.get()["ids"]

            # If the collection already contains documents, delete them.
            #
            # ChromaDB does NOT accept:
            #
            #     collection.delete(where={})
            #
            # because an empty "where" filter is invalid.
            #
            # Instead, we explicitly provide the IDs we want to delete.
            if existing_ids:
                collection.delete(ids=existing_ids)

            # Add the newly created chunks to ChromaDB.
            collection.add(

                # The actual text that will be searched.
                documents=[
                    c["text"]
                    for c in chunks
                ],

                # Metadata gives us additional information about each
                # chunk that can be used for display and filtering.
                metadatas=[
                    {
                        "source": c["source"],
                        "chunk_index": str(c["chunk_index"])
                    }
                    for c in chunks
                ],

                # Every item in a ChromaDB collection needs a unique ID.
                ids=[
                    c["chunk_id"]
                    for c in chunks
                ],
            )

            # Tell the user what happened.
            #
            # set() removes duplicate filenames, so we can report the
            # number of actual source documents rather than the number
            # of chunks.
            st.success(
                f"Indexed {len(chunks)} chunks from "
                f"{len(set(c['source'] for c in chunks))} files"
            )

        else:

            # This means load_and_chunk() didn't find any supported
            # documents or couldn't create any chunks.
            st.warning(
                "No .txt or .md files found in docs/ folder"
            )


    # -------------------------------------------------------------------------
    # DATABASE STATISTICS
    # -------------------------------------------------------------------------

    # collection.count() returns the number of chunks stored in ChromaDB.
    #
    # Technically, this is NOT the number of documents because one document
    # can contain many chunks.
    st.metric(
        "Documents in DB",
        collection.count()
    )

    st.divider()


    # -------------------------------------------------------------------------
    # SEARCH RESULT COUNT
    # -------------------------------------------------------------------------

    # Give the user control over how many search results are displayed.
    n_results = st.slider(
        "Results to show",
        1,
        10,
        5
    )


    # -------------------------------------------------------------------------
    # SOURCE FILTERS
    # -------------------------------------------------------------------------

    st.sidebar.header("Filters")

    # Retrieve metadata for everything currently stored in ChromaDB.
    #
    # include=["metadatas"] tells ChromaDB that we only need metadata,
    # not the actual document text.
    metadata_list = collection.get(
        include=["metadatas"]
    )["metadatas"]


    # Build a list of unique source filenames.
    #
    # Each chunk has a "source" metadata field telling us which document
    # it came from.
    #
    # A set() automatically removes duplicate filenames.
    source_filenames = sorted({
        meta.get("source")
        for meta in metadata_list
        if isinstance(meta, dict)
        and meta.get("source")
    })


    # Let the user choose which source documents should be searched.
    #
    # By default, all available sources are selected.
    selected_sources = st.multiselect(
        "Select Your Sources",
        options=source_filenames,
        default=source_filenames,
    )


# =============================================================================
# MAIN SEARCH INTERFACE
# =============================================================================

st.title("🔍 Semantic Search")

st.write(
    "Search your documents by meaning, not just keywords."
)


# Create the search input box.
#
# The value typed by the user is stored in the "query" variable.
query = st.text_input(
    "Enter your search query",
    placeholder="Type a question or phrase..."
)


# =============================================================================
# PERFORM SEARCH
# =============================================================================
#
# We only perform a search if:
#
# 1. The user entered a query
# 2. ChromaDB contains at least one chunk
if query and collection.count() > 0:

    # -------------------------------------------------------------------------
    # BUILD THE SOURCE FILTER
    # -------------------------------------------------------------------------
    #
    # ChromaDB uses a "where" expression to filter results based on metadata.
    #
    # If one source is selected:
    #
    #     {"source": "python.md"}
    #
    # If multiple sources are selected:
    #
    #     {"source": {"$in": ["python.md", "sql.md"]}}
    #
    # If nothing is selected, we don't provide a filter.
    if len(selected_sources) == 1:

        where_filter = {
            "source": selected_sources[0]
        }

    elif len(selected_sources) > 1:

        where_filter = {
            "source": {
                "$in": selected_sources
            }
        }

    else:

        where_filter = None


    # -------------------------------------------------------------------------
    # QUERY CHROMADB
    # -------------------------------------------------------------------------

    results = collection.query(

        # The text the user entered.
        #
        # ChromaDB converts this query into an embedding and compares it
        # with the embeddings associated with the stored chunks.
        query_texts=[query],

        # Don't ask for more results than the collection contains.
        n_results=min(
            n_results,
            collection.count()
        ),

        # Restrict the search to the selected source documents.
        where=where_filter
    )


    # -------------------------------------------------------------------------
    # DISPLAY RESULTS
    # -------------------------------------------------------------------------

    # ChromaDB returns a list of results for each query.
    #
    # Because we're currently sending only ONE query, we access the
    # first list using [0].
    if results["documents"] and results["documents"][0]:

        # Number of source documents available.
        total_documents = len(source_filenames)

        # Tell the user how many results we're displaying.
        #
        # NOTE:
        # The "X" is actually the number of returned CHUNKS, while
        # "Y" represents the number of source documents.
        #
        # A more technically precise version could say:
        #
        #     "Showing 5 matching chunks from 3 documents"
        #
        # But we're keeping the wording aligned with the exercise.
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

            # Retrieve the actual chunk of text.
            doc = results["documents"][0][i]

            # Retrieve metadata associated with that chunk.
            metadata = results["metadatas"][0][i]

            # Retrieve the distance between the query and this chunk.
            #
            # Lower distance generally means the embedding of the chunk
            # is closer to the embedding of the query.
            distance = results["distances"][0][i]


            # -----------------------------------------------------------------
            # CREATE A SHORT PREVIEW
            # -----------------------------------------------------------------

            # Take only the first 150 characters.
            preview = doc[:150]

            # If the original chunk is longer than 150 characters,
            # add an ellipsis so the user knows the preview was shortened.
            if len(doc) > 150:
                preview += "..."


            # -----------------------------------------------------------------
            # DISPLAY RESULT INFORMATION
            # -----------------------------------------------------------------

            # Show the source filename and similarity distance.
            st.subheader(
                f"{metadata['source']} — "
                f"Distance: {distance:.3f}"
            )


            # Show the shortened preview.
            st.write(preview)


            # -----------------------------------------------------------------
            # FULL TEXT EXPANDER
            # -----------------------------------------------------------------

            # Keep the interface compact by hiding the complete chunk
            # until the user wants to see it.
            with st.expander("Show full text"):
                st.write(doc)


    else:

        # This happens when the query produced no matching results
        # for the selected sources.
        st.warning(
            "No results found for the selected sources."
        )


# =============================================================================
# EMPTY DATABASE MESSAGE
# =============================================================================

# If there aren't any chunks in ChromaDB, tell the user how to populate it.
elif collection.count() == 0:

    st.info(
        "👈 Click 'Re-index Documents' in the sidebar "
        "to load your documents first."
    )


# =============================================================================
# FINAL DATABASE COUNT
# =============================================================================
#
# This stores the total number of chunks in a variable.
#
# Currently it isn't displayed anywhere, but it can be useful for
# debugging or for adding another statistic to the interface later.
total = collection.count()
```
