# 🚀 Quick Start - RAG Service# RAG Service - Quick Start Guide



## ✅ Final Files## 🚀 Setup in 5 Minutes



### Documentation### Step 1: Install Dependencies

- `README.md` - Complete service documentation```bash

- `POSTMAN_GUIDE.md` - Postman collection guidecd apps/rag-service

python3 -m venv venv

### Postman Collectionsource venv/bin/activate  # Windows: venv\Scripts\activate

- `RAG-Service-Complete.postman_collection.json` - **40+ API requests**pip install -r requirements.txt

- `RAG-Service.postman_environment.json` - Environment variables```



### Scripts### Step 2: Configure Environment

- `run.sh` - Service startup script```bash

cp .env.example .env

## 🏗️ Architecture (CORRECT)```



```Edit `.env` file - minimum required:

Client → Gateway (3006) → RAG (8000) → Gateway (3006) → LLM Services (3001, 3002, 3003)```bash

```VECTOR_DB_TYPE=faiss

EMBEDDING_TYPE=local

**Key Points:**GATEWAY_SERVICE_URL=http://localhost:3000/api

- ✅ ALL client requests → Gateway (port 3006)```

- ✅ RAG calls LLMs → through Gateway (not direct!)

- ❌ NO direct service-to-service calls### Step 3: Download Embedding Model (if using local)

```bash

## 📦 Postman Collection Contentspython -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

```

### 1. Health & Status (2 requests)

- Health Check via Gateway### Step 4: Start the Service

- Service Info```bash

# Option 1: Using script

### 2. Document Management (7 requests)chmod +x start.sh

- Upload PDF/Word/Text./start.sh

- Add URL Content

- List All Documents# Option 2: Direct command

- Get Document by IDuvicorn app.main:app --reload --host 0.0.0.0 --port 8000

- Delete Document```



### 3. Query & Search (4 requests)### Step 5: Test the Service

- General Query (Full RAG Pipeline)Open browser: http://localhost:8000/docs

- Query with Context Window

- Document-Specific Query## 📝 Example Usage

- Semantic Search Only

### Upload a Document

### 4. Testing Scenarios (3 test suites)```bash

- **Complete Workflow Test** (6 steps)curl -X POST "http://localhost:8000/documents/upload" \

  - Health → Upload → List → Query → Search → Delete  -H "Content-Type: multipart/form-data" \

- **URL Ingestion Test** (2 steps)  -F "file=@/path/to/document.pdf"

  - Add Wikipedia → Query Content```

- **Multi-Document Query Test** (3 steps)

  - Upload 2 docs → Query both### Add a URL

```bash

### 5. Architecture Validation (3 requests)curl -X POST "http://localhost:8000/documents/add-url" \

- Gateway Health  -H "Content-Type: application/json" \

- RAG via Gateway  -d '{"url": "https://example.com/article"}'

- Test Full Architecture Flow```



**Total: 40+ requests organized in 5 sections**### Query (General)

```bash

## 🚀 Quick Start Guidecurl -X POST "http://localhost:8000/query" \

  -H "Content-Type: application/json" \

### 1. Import Postman Files  -d '{"question": "What is machine learning?", "top_k": 5}'

```

```bash

# Files to import:### Query (Document-Specific)

apps/rag-service/RAG-Service-Complete.postman_collection.json```bash

apps/rag-service/RAG-Service.postman_environment.jsoncurl -X POST "http://localhost:8000/query/document-specific" \

```  -H "Content-Type: application/json" \

  -d '{

### 2. Start Services    "question": "What does the document say about AI?",

    "document_id": "your-document-id-here",

**Terminal 1 - Gateway:**    "top_k": 5

```bash  }'

cd apps/gateway```

npm run start:dev

# Runs on port 3006## ⚙️ Configuration Scenarios

```

### Scenario 1: Local Development (Default)

**Terminal 2 - RAG Service:**```bash

```bashVECTOR_DB_TYPE=faiss

cd apps/rag-serviceEMBEDDING_TYPE=local

source .venv/bin/activateGATEWAY_SERVICE_URL=http://localhost:3000/api

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000```

```

### Scenario 2: Production with OpenAI

### 3. Test in Postman```bash

VECTOR_DB_TYPE=pinecone

1. Select environment: "RAG Service - Production"EMBEDDING_TYPE=openai

2. Run: **1. Health & Status** → **Health Check via Gateway**OPENAI_API_KEY=sk-...

3. Expected response:PINECONE_API_KEY=...

```jsonPINECONE_ENVIRONMENT=us-east-1

{PINECONE_INDEX_NAME=rag-production

  "status": "healthy",GATEWAY_SERVICE_URL=https://api.yourcompany.com

  "vector_db_type": "faiss",```

  "embedding_type": "local",

  "gateway_url": "http://localhost:3006"### Scenario 3: Hybrid (Local embeddings + Pinecone)

}```bash

```VECTOR_DB_TYPE=pinecone

EMBEDDING_TYPE=local

### 4. Run Complete WorkflowPINECONE_API_KEY=...

PINECONE_ENVIRONMENT=us-east-1

Navigate to: **4. Testing Scenarios** → **Complete Workflow Test**PINECONE_INDEX_NAME=rag-hybrid

GATEWAY_SERVICE_URL=http://localhost:3000/api

Right-click folder → **Run Folder** → Execute all 6 steps automatically:```

1. ✅ Health Check

2. ✅ Upload Document## 🔍 Troubleshooting

3. ✅ List Documents

4. ✅ General Query (calls LLMs via Gateway!)### Error: "Import could not be resolved"

5. ✅ Document-Specific QueryThis is a Pylance warning, not a runtime error. The code will run fine. To fix:

6. ✅ Delete Document1. Ensure virtual environment is activated

2. Install dependencies: `pip install -r requirements.txt`

## 🔍 Key Endpoints3. Restart VS Code



All endpoints use `{{gateway_url}}` = `http://localhost:3006`### Error: "Gateway connection failed"

1. Ensure Gateway service is running: `curl http://localhost:3000/api/health`

| Endpoint | Method | Description |2. Check GATEWAY_SERVICE_URL in .env

|----------|--------|-------------|3. Verify firewall/network settings

| `/rag/health` | GET | Health check |

| `/rag/documents/upload` | POST | Upload file |### Error: "Local model not found"

| `/rag/documents/url` | POST | Scrape URL |```bash

| `/rag/documents` | GET | List documents |python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

| `/rag/documents/{id}` | GET | Get document |```

| `/rag/documents/{id}` | DELETE | Delete document |

| `/rag/query` | POST | Full RAG query |### Error: "FAISS index error"

| `/rag/query/document-specific` | POST | Search in document |Delete and rebuild:

```bash

## 🎯 Example Requestrm -rf data/faiss_index*

# Re-upload documents

**Upload Document via Gateway:**```

```bash

curl -X POST http://localhost:3006/rag/documents/upload \## 📊 Testing

  -F "file=@document.pdf"

```### Run Tests

```bash

**Query via Gateway (Full RAG):**pip install pytest pytest-asyncio

```bashpytest tests/ -v

curl -X POST http://localhost:3006/rag/query \```

  -H "Content-Type: application/json" \

  -d '{### Manual Testing (Interactive Docs)

    "question": "What is machine learning?",1. Open http://localhost:8000/docs

    "top_k": 52. Try each endpoint

  }'3. View request/response schemas

```

## 🎯 Next Steps

**Flow:**

1. Client → Gateway (3006)1. **Upload Test Documents**: Upload 2-3 PDFs or text files

2. Gateway → RAG (8000)2. **Test Queries**: Try both general and document-specific queries

3. RAG searches vector DB3. **Monitor Logs**: Check console for processing details

4. RAG → Gateway (3006) → Gemini (3001)4. **Integrate**: Connect your frontend or other services

5. RAG → Gateway (3006) → Llama (3002)5. **Scale**: Configure for production with Pinecone and OpenAI

6. RAG → Gateway (3006) → Cohere (3003)

7. RAG → Gateway (3006) → Summarizer (3004)## 📚 API Documentation

8. RAG returns final answer

9. Gateway → ClientFull API documentation available at:

- Swagger UI: http://localhost:8000/docs

## 📊 What Was Cleaned Up- ReDoc: http://localhost:8000/redoc



### Removed Files:## 💡 Tips

- ❌ `ARCHITECTURE.md` (redundant)

- ❌ `GATEWAY_INTEGRATION_FIXED.md` (redundant)1. **Chunk Size**: Adjust `CHUNK_SIZE` based on your documents (512 is good default)

- ❌ `LANGCHAIN_MIGRATION.md` (redundant)2. **Top K**: Start with 5, increase for more context

- ❌ `LANGCHAIN_STATUS.md` (redundant)3. **Local vs API**: Local is free but less powerful; API costs but better quality

- ❌ `QUICKSTART.md` (merged into README)4. **FAISS vs Pinecone**: FAISS for dev/testing, Pinecone for production

- ❌ `SETUP_COMPLETE.md` (redundant)5. **Gateway**: Ensure all microservices are running and registered with gateway

- ❌ `ARCHITECTURE_CONFIRMED.md` (redundant)

- ❌ Old Postman collection files## 🤝 Need Help?



### Kept Files:- Check README.md for detailed documentation

- ✅ `README.md` - Main documentation- Review example requests in Postman collection

- ✅ `POSTMAN_GUIDE.md` - Testing guide- Enable debug logging: `LOG_LEVEL=DEBUG` in .env

- ✅ `RAG-Service-Complete.postman_collection.json` - Complete collection- Check service logs for detailed error messages

- ✅ `RAG-Service.postman_environment.json` - Environment
- ✅ `.env` - Configuration
- ✅ `run.sh` - Startup script

## ⚡ Environment Variables

**In Postman:**
- `gateway_url` = `http://localhost:3006`
- `document_id` = (auto-populated)
- `url_document_id` = (auto-populated)
- `doc1_id`, `doc2_id` = (for multi-doc tests)

**In `.env` file:**
```bash
GATEWAY_SERVICE_URL=http://localhost:3006
GEMINI_ENDPOINT=/gemini/gemini/make
LLAMA_ENDPOINT=/llama/hugging-face/chat
COHERE_ENDPOINT=/cohere/cohere/make
SUMMARIZER_ENDPOINT=/summarize/api/summarize/ai-prompts
```

## 🎓 Important Notes

1. **Never call port 8000 directly** - Always use Gateway (3006)
2. **LLM calls go through Gateway** - RAG never calls 3001, 3002, 3003 directly
3. **Auto-save document IDs** - Upload endpoints save IDs to environment
4. **Run workflows** - Use folder runner for sequential tests
5. **Monitor logs** - Watch both Gateway and RAG service logs

## 🔧 Troubleshooting

**Service not responding:**
```bash
# Check Gateway
curl http://localhost:3006/health

# Check RAG via Gateway
curl http://localhost:3006/rag/health
```

**Restart services:**
```bash
# Gateway
cd apps/gateway
npm run start:dev

# RAG
cd apps/rag-service
pkill -f "python.*app.main"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🎉 Summary

- ✅ **Cleaned up**: Removed 7+ redundant documentation files
- ✅ **Complete Postman**: 40+ requests in 5 organized sections
- ✅ **Correct Architecture**: Everything routes through Gateway
- ✅ **Production Ready**: Full RAG pipeline with LLM integration
- ✅ **Easy Testing**: Pre-configured workflows and test scenarios

---

**You're all set!** Import the Postman collection and start testing. 🚀
