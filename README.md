



I've created a comprehensive example that demonstrates PDF vectorization and MongoDB storage. Here's what the code does:
Key Features:

PDF Text Extraction - Uses PyPDF2 to extract text from PDFs and split into chunks by page and paragraph
Embedding Generation - Uses the sentence-transformers library with the 'all-MiniLM-L6-v2' model to create 384-dimensional vector embeddings
MongoDB Storage - Stores both the text chunks and their embeddings in MongoDB with metadata (page numbers, source, timestamps)
Similarity Search - Includes a function to search for similar documents using cosine similarity

MongoDB Document Structure:
json{
  "document_name": "Example.pdf",
  "text": "The actual text chunk",
  "page_number": 1,
  "chunk_index": 0,
  "source": "/path/to/file.pdf",
  "embedding": [0.123, -0.456, ...],
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimension": 384,
  "created_at": "2025-10-20T10:30:00Z"
}
To use this code:

Install dependencies: pip install pymongo PyPDF2 sentence-transformers numpy
Make sure MongoDB is running locally or update the connection string
Replace the PDF path with your actual file

Note: For production-scale vector search, consider using MongoDB Atlas with vector search indexes, or alternatives like Pinecone, Weaviate, or ChromaDB

# REDIS ADD

Perfect! I've refactored the code to support both Redis and MongoDB as vector stores. Here's what's new:

Key Features:

1. Pluggable Architecture

- Abstract VectorStore base class
- Two implementations: MongoVectorStore and RedisVectorStore
- Easy to switch between stores or add new ones

2. Redis Support

Uses RedisSearch with vector similarity search
Native vector indexing with COSINE distance metric
Much faster similarity searches (optimized KNN)
Stores embeddings as binary float32 arrays

3. MongoDB Support

Original MongoDB implementation maintained
Stores embeddings as JSON arrays
Cosine similarity calculated in Python


## Usage Examples:

### Using MongoDB:

pythonvectorizer = DocumentVectorizer(
    vector_store_type="mongodb",
    mongo_uri="mongodb://localhost:27017/",
    db_name="document_vectors",
    collection_name="embeddings"
)

### Using Redis:

pythonvectorizer = DocumentVectorizer(
    vector_store_type="redis",
    host="localhost",
    port=6379,
    db=0,
    index_name="doc_embeddings"
)


## Performance Comparison:

![alt text](<PerformanceCompare.png>)

### Quick Start:

Just change the VECTOR_STORE variable in the main section:

pythonVECTOR_STORE = "mongodb"  # or "redis"

The API remains the same regardless of which vector store you choose!

### Overview

The sentence-transformers library makes local calls - it downloads the model once and runs entirely on your machine.
How it works:

First time: When you run SentenceTransformer('all-MiniLM-L6-v2'), it downloads the model files (~80-90MB) from Hugging Face and caches them locally (usually in ~/.cache/torch/sentence_transformers/)
Subsequent runs: The model loads from your local cache - no internet required
Inference: All embedding generation happens locally on your CPU/GPU - no API calls, no external services

Benefits:

✅ Free (no API costs)
✅ Private (your data never leaves your machine)
✅ Fast after initial download
✅ Works offline after first download
✅ No rate limits

Performance note:

CPU: Works fine, but slower for large documents
GPU: Much faster if you have CUDA-enabled GPU

Alternative API-based options (if you prefer):

OpenAI embeddings (text-embedding-3-small) - requires API key & costs money
Cohere embeddings - requires API key
Google's embeddings - requires API key

The local approach with sentence-transformers is ideal for most use cases unless you need the absolute best embedding quality (where OpenAI's models might perform slightly better for certain tasks).


### 1. Multi-format Support:

extract_text_from_pdf()     - Handles PDF files
extract_text_from_txt()     - Handles plain text files
extract_text_from_docx()    - Handles Word documents
extract_text()              - Auto-detects file type by extension


### 2. Unified Processing:

Single process_document() method works for all formats
Automatically detects file type and routes to appropriate extractor


### 3. Enhanced Metadata:

Added file_type field to track document format
All chunks maintain their original format information


### 4. Additional Features:

get_statistics() - View counts by file type
similarity_search() - Now supports filtering by file type
Better error handling and user feedback

pip install pymongo PyPDF2 sentence-transformers numpy python-docx

vectorizer = DocumentVectorizer()

# Process any supported format
vectorizer.process_document("report.pdf")
vectorizer.process_document("notes.txt")
vectorizer.process_document("analysis.docx")

# Search with optional file type filter
results = vectorizer.similarity_search(
    "machine learning", 
    top_k=5,
    file_type_filter="pdf"  # Optional: only search PDFs
)

**By: George Leonard**
- georgelza@gmail.com
- https://www.linkedin.com/in/george-leonard-945b502/
- https://medium.com/@georgelza

