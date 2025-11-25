# RAG Service - Retrieval-Augmented Generation System

A comprehensive RAG (Retrieval-Augmented Generation) service built with FastAPI that integrates with a NestJS microservices backend architecture. This service provides intelligent document processing, vector-based search, and multi-LLM query orchestration.

## 🌟 Features

- **Multi-format Document Support**: PDF, Word (.docx), plain text, and web URLs
- **Flexible Embedding Options**: 
  - Local: sentence-transformers (all-MiniLM-L6-v2)
  - API-based: OpenAI, Cohere
- **Dual Vector Database Support**:
  - Development: FAISS (local, persistent)
  - Production: Pinecone (cloud)
- **Intelligent Query Processing**:
  - General queries: Full LLM pipeline with summarization
  - Document-specific queries: Direct context extraction
- **Gateway Integration**: All LLM calls route through centralized NestJS Gateway
- **Multi-LLM Orchestration**: Parallel querying of Gemini, Llama, and Cohere services
- **Response Summarization**: Automated consolidation of multiple LLM outputs

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      RAG Service                         │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Document  │  │   Embedding  │  │  Vector DB     │  │
│  │ Processor  │──│   Service    │──│  (FAISS/Pine)  │  │
│  └────────────┘  └──────────────┘  └────────────────┘  │
│         │                                    │           │
│         └────────────┬──────────────────────┘           │
│                      │                                   │
│              ┌───────▼───────┐                          │
│              │ Query Service │                          │
│              └───────┬───────┘                          │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │  Gateway Service │
            │    (NestJS)      │
            └────────┬─────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
   ┌───▼───┐   ┌────▼────┐   ┌───▼────┐
   │Gemini │   │  Llama  │   │Cohere  │
   └───┬───┘   └────┬────┘   └───┬────┘
       │            │            │
       └────────────┼────────────┘
                    │
            ┌───────▼────────┐
            │  AI Summarizer │
            └────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Local sentence-transformers model downloaded (or API keys for OpenAI/Cohere)
- Running NestJS Gateway service
- Running LLM microservices (Gemini, Llama, Cohere integrations)

### Installation

1. **Clone and navigate to the service**:
```bash
cd apps/rag-service
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Download local embedding model** (if using local embeddings):
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

5. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

Edit `.env` file:

```bash
# Vector Database (faiss or pinecone)
VECTOR_DB_TYPE=faiss
FAISS_INDEX_PATH=./data/faiss_index

# Embedding Model (local, openai, or cohere)
EMBEDDING_TYPE=local
LOCAL_MODEL_PATH=~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2

# Gateway Service URL (REQUIRED)
GATEWAY_SERVICE_URL=http://localhost:3000/api

# Application Settings
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

### Running the Service

**Development**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Document Management

#### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <PDF/DOCX/TXT file>
```

**Response**:
```json
{
  "document_id": "uuid",
  "filename": "example.pdf",
  "document_type": "pdf",
  "chunks_count": 42,
  "upload_timestamp": "2024-01-01T12:00:00",
  "metadata": {}
}
```

#### Add URL
```http
POST /documents/add-url
Content-Type: application/json

{
  "url": "https://example.com/article",
  "metadata": {}
}
```

#### List Documents
```http
GET /documents
```

#### Delete Document
```http
DELETE /documents/{document_id}
```

### Query Processing

#### General Query (Scenario A)
Full pipeline: Vector search → All LLMs → Summarization

```http
POST /query
Content-Type: application/json

{
  "question": "What are the main benefits of AI?",
  "top_k": 5
}
```

**Response**:
```json
{
  "answer": "Summarized response from all LLMs",
  "query_type": "general",
  "retrieved_contexts": [...],
  "llm_responses": [
    {
      "service": "gemini",
      "response": "...",
      "timestamp": "..."
    },
    ...
  ],
  "processing_time_seconds": 2.34,
  "timestamp": "..."
}
```

#### Document-Specific Query (Scenario B)
Direct extraction from document (no LLM calls)

```http
POST /query/document-specific
Content-Type: application/json

{
  "question": "What does the document say about X?",
  "document_id": "uuid",
  "top_k": 5
}
```

### Health & Management

#### Health Check
```http
GET /health
```

#### Reindex
```http
POST /reindex
```

## 🔧 Configuration Options

### Vector Database

**FAISS (Local)**:
- Best for: Development, small to medium datasets
- Pros: No external dependencies, free, fast
- Cons: Single-machine, no distributed queries

**Pinecone (Cloud)**:
- Best for: Production, large datasets, distributed systems
- Pros: Scalable, managed, distributed
- Cons: Requires API key, costs money

### Embedding Models

**Local (sentence-transformers)**:
- Model: all-MiniLM-L6-v2
- Dimension: 384
- Pros: Free, fast, no API limits
- Cons: Requires local compute, not as powerful

**OpenAI**:
- Model: text-embedding-ada-002
- Dimension: 1536
- Pros: High quality, maintained
- Cons: Costs per token, API limits

**Cohere**:
- Model: embed-english-v3.0
- Dimension: 1024
- Pros: Good quality, specialized features
- Cons: Requires API key, costs

## 🔄 Workflow Details

### Scenario A: General Query
1. User submits question
2. RAG generates query embedding
3. Vector DB returns top-k similar chunks
4. RAG → Gateway → Gemini LLM
5. RAG → Gateway → Llama LLM
6. RAG → Gateway → Cohere LLM
7. RAG → Gateway → AI Summarizer (with all 3 responses)
8. Summarized answer stored in vector DB
9. Final answer returned to user

### Scenario B: Document-Specific Query
1. User submits question + document_id
2. RAG generates query embedding
3. Vector DB returns top-k chunks from that document only
4. Answer generated directly from retrieved context
5. No LLM calls, no summarization
6. Answer returned immediately

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## 📦 Project Structure

```
rag-service/
├── app/
│   ├── main.py                   # FastAPI app
│   ├── config.py                 # Configuration
│   ├── models/
│   │   ├── schemas.py           # Pydantic models
│   │   └── document.py          # Document models
│   ├── services/
│   │   ├── embedding_service.py     # Embedding abstraction
│   │   ├── vector_db_service.py     # Vector DB abstraction
│   │   ├── document_processor.py    # Document processing
│   │   ├── gateway_client.py        # Gateway HTTP client
│   │   ├── llm_orchestrator.py      # LLM coordination
│   │   └── query_service.py         # Query processing
│   ├── utils/
│   │   ├── file_parsers.py      # Document parsers
│   │   └── chunking.py          # Text chunking
│   └── api/
│       └── routes/
│           ├── documents.py     # Document endpoints
│           └── query.py         # Query endpoints
├── tests/
├── data/                        # FAISS index storage
├── .env                         # Configuration
├── requirements.txt
└── README.md
```

## 🔐 Security Considerations

- **API Keys**: Store in environment variables, never commit
- **CORS**: Configure appropriately for production
- **Rate Limiting**: Consider adding rate limiting middleware
- **Input Validation**: All inputs validated via Pydantic
- **Error Handling**: Comprehensive error handling throughout

## 🚧 Troubleshooting

### Gateway Connection Issues
```bash
# Test gateway connectivity
curl http://localhost:3000/api/health
```

### Embedding Model Not Found
```bash
# Download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### FAISS Index Errors
```bash
# Remove and rebuild index
rm -rf data/faiss_index*
# Restart service and re-upload documents
```

## 📈 Performance Optimization

- **Batch Processing**: Process multiple documents concurrently
- **Caching**: Cache embeddings for frequently queried texts
- **Index Optimization**: Use FAISS IVF for large datasets
- **Connection Pooling**: Reuse HTTP connections to gateway
- **Async Operations**: All I/O operations are async

## 🤝 Integration with Existing Services

This RAG service is designed to integrate seamlessly with your NestJS microservices:

- **Gateway Service**: All requests route through the central gateway
- **LLM Services**: Gemini, Llama, Cohere integrations
- **AI Summarizer**: Response consolidation service
- **Auth Service**: Can be integrated for request authentication

## 📝 License

Part of the Synthora monorepo project.

## 👥 Support

For issues or questions, please refer to the main project documentation or create an issue in the repository.
