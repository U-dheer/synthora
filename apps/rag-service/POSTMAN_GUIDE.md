# RAG Service Postman Collection

Complete API testing collection for the RAG (Retrieval-Augmented Generation) Service.

## 🏗️ Architecture

**IMPORTANT:** All requests go through Gateway (Port 3006).

```
Client → Gateway (3006) → RAG Service (8000) → Gateway (3006) → LLM Services (3001, 3002, 3003)
```

## 📦 Files

- **`RAG-Service-Complete.postman_collection.json`** - Complete API collection (40+ requests)
- **`RAG-Service.postman_environment.json`** - Environment variables

## 🚀 Quick Start

### 1. Import into Postman

**Import Collection:**
1. Open Postman
2. Click **Import** button
3. Select `RAG-Service-Complete.postman_collection.json`
4. Collection will appear in your workspace

**Import Environment:**
1. Click **Environments** (left sidebar)
2. Click **Import**
3. Select `RAG-Service.postman_environment.json`
4. Select "RAG Service - Production" from dropdown

### 2. Start Services

**Start Gateway:**
```bash
cd apps/gateway
npm run start:dev
# Gateway runs on port 3006
```

**Start RAG Service:**
```bash
cd apps/rag-service
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# RAG service runs on port 8000
```

Wait for both services to start.

### 3. Test the Connection

Run the **Health Check via Gateway** request from the collection:
- Folder: **1. Health & Status** → **Health Check via Gateway**
- Should return: `{"status": "healthy", ...}`

## 📋 Collection Structure

### 1. Health & Status
Service health checks:
- **Health Check via Gateway** - Verify service is running
- **Service Info** - Get service information

### 2. Document Management
Upload and manage documents (7 requests):
- **Upload PDF Document** - Process PDF files
- **Upload Word Document** - Process DOCX files
- **Upload Text File** - Process TXT files
- **Add URL Content** - Scrape and index web content
- **List All Documents** - Get all uploaded documents
- **Get Document by ID** - Retrieve specific document
- **Delete Document** - Remove document from system

### 3. Query & Search
Query the knowledge base (4 requests):
- **General Query (Full RAG Pipeline)** - Full RAG with LLM responses
- **Query with Context Window** - Query with larger context
- **Document-Specific Query** - Search within specific document
- **Semantic Search Only** - Pure semantic search

### 4. Testing Scenarios
Pre-configured workflows (3 test suites):
- **Complete Workflow Test** - Full end-to-end test (6 steps)
  1. Health Check
  2. Upload Document
  3. List Documents
  4. General Query
  5. Document-Specific Query
  6. Delete Document
- **URL Ingestion Test** - Test web scraping (2 steps)
- **Multi-Document Query Test** - Test cross-document queries (3 steps)

### 5. Architecture Validation
Verify routing architecture (3 requests):
- **Gateway Health** - Check Gateway service
- **RAG via Gateway** - Verify Gateway → RAG routing
- **Test Full Architecture Flow** - Complete flow validation

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `gateway_url` | `http://localhost:3006` | Gateway service URL (ALL requests go here) |
| `document_id` | (empty) | Auto-populated from uploads |
| `url_document_id` | (empty) | For URL ingestion tests |
| `doc1_id` | (empty) | For multi-document tests |
| `doc2_id` | (empty) | For multi-document tests |

## 📝 Usage Examples

### Example 1: Upload and Query a Document

1. **Upload Document**
   - Request: `Document Management` → `Upload PDF Document`
   - Select your PDF file
   - Response will include `document_id` (auto-saved to environment)

2. **Query the Document**
   - Request: `Query & Search` → `General Query (with LLM)`
   - Body: `{"question": "What is this document about?", "top_k": 5}`
   - Get AI-generated answer based on document content

### Example 2: Add Web Content

1. **Scrape URL**
   - Request: `Document Management` → `Add URL Content`
   - Body: `{"url": "https://en.wikipedia.org/wiki/Machine_learning"}`
   - Content is scraped, chunked, and indexed

2. **Query Web Content**
   - Request: `Query & Search` → `General Query (with LLM)`
   - Ask questions about the web content

### Example 3: Document-Specific Search

1. **Get Document ID**
   - Request: `Document Management` → `List All Documents`
   - Copy a `document_id`

2. **Search Specific Document**
   - Request: `Query & Search` → `Document-Specific Query`
   - Body: `{"question": "key points", "document_id": "...", "top_k": 5}`
   - Returns relevant chunks without LLM processing

### Example 4: Complete Workflow Test

Run the **Complete Workflow Test** folder:
1. Select folder: `Testing Scenarios` → `Complete Workflow Test`
2. Click **Run** button
3. All 6 steps execute automatically
4. View results in **Collection Runner**

## 🎯 Request Details

### Upload Document Request

```http
POST http://localhost:3006/rag/documents/upload
Content-Type: multipart/form-data

file: [binary file data]
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "document.pdf",
  "document_type": "pdf",
  "chunk_count": 25,
  "upload_timestamp": "2025-11-17T...",
  "metadata": {...}
}
```

### Query Request (Full RAG Pipeline)

```http
POST http://localhost:3006/rag/query
Content-Type: application/json

{
  "question": "What is machine learning?",
  "top_k": 5
}
```

**Workflow:**
1. RAG searches vector DB
2. RAG → Gateway → Gemini LLM
3. RAG → Gateway → Llama LLM
4. RAG → Gateway → Cohere LLM
5. RAG → Gateway → Summarizer
6. Returns final answer

**Response:**
```json
{
  "answer": "Machine learning is...",
  "query_type": "GENERAL",
  "retrieved_contexts": [...],
  "processing_time_seconds": 1.23,
  "timestamp": "2025-11-17T..."
}
```

### Add URL Request

```http
POST http://localhost:3006/rag/documents/url
Content-Type: application/json

{
  "url": "https://example.com/article"
}
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "https://example.com/article",
  "document_type": "url",
  "chunk_count": 15,
  "upload_timestamp": "2025-11-17T...",
  "metadata": {...}
}
```

## 🔍 Testing Tips

### 1. Automatic Variable Setting
The **Upload Document** requests have a test script that automatically saves `document_id` to environment variables. You can use `{{document_id}}` in subsequent requests.

### 2. Run Entire Folders
Right-click any folder → **Run Folder** to execute all requests sequentially.

### 3. View Interactive Docs
Visit `http://localhost:8000/docs` for Swagger UI (direct access for development).

### 4. Monitor Logs
Watch service logs:
```bash
# Gateway logs
cd apps/gateway
# Check terminal

# RAG service logs
tail -f apps/rag-service/rag-service.log
```

### 5. Architecture is Correct
All requests in the collection use `{{gateway_url}}` which points to `http://localhost:3006`.

**Never call `http://localhost:8000` directly in production!**

## 🏗️ Architecture Flow

```
Client (Postman)
      ↓
      ↓ [ALL Requests]
      ↓
Gateway Service (Port 3006)
      ↓
      ├─→ /rag/* ─────────────────→ RAG Service (Port 8000)
      │                                    ↓
      │                    [RAG needs LLM responses]
      │                                    ↓
      │                    [Calls Gateway, NOT direct!]
      │                                    ↓
      │    ◄───────────────────────────────┘
      │
      ├─→ /gemini/gemini/make ─────→ Gemini (Port 3001)
      ├─→ /llama/hugging-face/chat ─→ Llama (Port 3002)
      ├─→ /cohere/cohere/make ─────→ Cohere (Port 3003)
      └─→ /summarize/... ──────────→ Summarizer (Port 3004/3005)
```

**Key Principle:**
- ✅ Client → Gateway (3006)
- ✅ RAG → Gateway (3006) → LLM Services
- ❌ RAG → LLM Services (direct) - NEVER HAPPENS!

## 📊 Response Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed successfully |
| 201 | Created | Document uploaded successfully |
| 204 | No Content | Document deleted successfully |
| 400 | Bad Request | Invalid request data |
| 404 | Not Found | Document not found |
| 422 | Validation Error | Invalid input format |
| 500 | Server Error | Internal service error |

## 🐛 Troubleshooting

### Service Not Responding
```bash
# Check Gateway
curl http://localhost:3006/health

# Check RAG via Gateway
curl http://localhost:3006/rag/health

# Restart Gateway
cd apps/gateway
npm run start:dev

# Restart RAG service
cd apps/rag-service
pkill -f "python.*app.main"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Connection Refused
- Ensure Gateway is running on port 3006: `curl http://localhost:3006/health`
- Ensure RAG service is running: `ps aux | grep app.main`
- Check Gateway logs for routing errors
- Verify RAG service logs: `tail -f rag-service.log`

### Upload Fails
- Check file path in formdata is correct
- Ensure file exists and is readable
- Verify supported format (PDF, DOCX, TXT)

### Query Returns Empty
- Verify documents are uploaded: `GET http://localhost:3006/rag/documents`
- Check `top_k` value is not too low
- Ensure vector DB has indexed documents
- Check RAG service logs for processing errors

### Gateway Errors
- Ensure Gateway is running on port 3006
- Check Gateway service logs in terminal
- Verify Gateway configuration: `apps/gateway/src/config/services.config.ts`
- Ensure RAG_SERVICE_URL is set correctly in Gateway

### LLM Service Errors
- RAG calls LLM services through Gateway only
- Check Gateway can reach LLM services (3001, 3002, 3003)
- Verify LLM services are running
- Check RAG service logs for Gateway client errors

## 🎓 Learning Path

1. **Start Simple**
   - Health Check via Gateway
   - Upload a small PDF through Gateway
   - Query it through Gateway

2. **Explore Features**
   - Try URL ingestion
   - Test document-specific queries
   - Experiment with different `top_k` values

3. **Test Workflows**
   - Run Complete Workflow Test (all 6 steps)
   - Test URL ingestion workflow
   - Try multi-document queries

4. **Validate Architecture**
   - Use Architecture Validation folder
   - Verify all requests go through Gateway
   - Check logs to confirm routing

5. **Advanced Usage**
   - Upload multiple documents
   - Query across all documents
   - Analyze LLM response times

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (Direct access for dev)
- **Service README**: `apps/rag-service/README.md`
- **Gateway Service**: `apps/gateway/`

## 💡 Tips

1. **Use Gateway URL**: ALL production requests must use `{{gateway_url}}`
2. **Auto Variables**: Upload endpoints auto-save `document_id` to environment
3. **Run Folders**: Right-click any folder → **Run Folder** for sequential execution
4. **Monitor Both Services**: Watch Gateway AND RAG service logs
5. **Test Architecture**: Use "Architecture Validation" folder to verify routing

## ⚠️ Important Notes

- **NEVER call `http://localhost:8000` directly in production**
- **ALL requests MUST go through Gateway (`http://localhost:3006`)**
- RAG service calls LLM services through Gateway, not directly
- Document IDs are automatically saved to environment variables
- The collection includes 40+ requests organized in 5 sections

---

**Happy Testing!** 🚀

For issues or questions, check the service logs or refer to the documentation files.
