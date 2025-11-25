# Postman Collection - Synthora Gateway API

## 📦 Quick Start

### 1. Import the Collection
1. Open Postman
2. Click **Import** button
3. Select the file: `Synthora-Gateway.postman_collection.json`
4. The collection will appear in your Collections sidebar

### 2. Configure Variables
After importing, set up the collection variables:

1. Click on the collection name → **Variables** tab
2. Set these variables:

| Variable | Current Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:3006` | Gateway service URL |
| `auth_token` | `your_jwt_token_here` | JWT token from auth service |

## 🔐 Getting Authentication Token

Before using the AI query endpoints, you need a valid JWT token:

### Step 1: Register a User (if not already registered)
```
POST {{base_url}}/auth/register

Body:
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

### Step 2: Login to Get Token
```
POST {{base_url}}/auth/login

Body:
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

### Step 3: Set Token Variable
1. Copy the `token` from the login response
2. Go to Collection → Variables → `auth_token`
3. Paste the token value
4. Click **Save**

## 📋 API Endpoints Overview

### Gateway Endpoints (Requires Authentication)

#### 1. **AI Query - Gemini** ✨
Send queries to Google's Gemini AI model
- **Method:** POST
- **Endpoint:** `/gateway/query`
- **Body:**
```json
{
  "model": "gemini",
  "prompt": "Explain quantum computing in simple terms"
}
```
- **Response:**
```json
{
  "success": true,
  "data": {
    "response": "Quantum computing uses quantum mechanics principles...",
    "model": "gemini",
    "timestamp": "2025-11-12T10:30:00.000Z"
  },
  "message": "Request processed successfully"
}
```

#### 2. **AI Query - Cohere** 🤖
Send queries to Cohere AI model
- **Method:** POST
- **Endpoint:** `/gateway/query`
- **Body:**
```json
{
  "model": "cohere",
  "prompt": "Write a short story about artificial intelligence"
}
```

#### 3. **AI Query - Llama** 🦙
Send queries to Llama AI model via Hugging Face
- **Method:** POST
- **Endpoint:** `/gateway/query`
- **Body:**
```json
{
  "model": "llama",
  "prompt": "What are the benefits of renewable energy?"
}
```

### Direct Service Access (Proxy)

These endpoints bypass the gateway logic and directly proxy to backend services:

#### Auth Service (Port 3000)
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/validate` - Token validation

#### AI Services
- `POST /ai/gemini/generate` - Direct Gemini access
- `POST /ai/cohere/generate` - Direct Cohere access
- `POST /ai/llama/generate` - Direct Llama access
- `POST /ai/summarize` - Direct Summarizer access

## 🧪 Testing Error Cases

### 1. Invalid Model Name
```json
{
  "model": "invalid_model",
  "prompt": "Test prompt"
}
```
**Expected Response:** `400 Bad Request`
```json
{
  "success": false,
  "statusCode": 400,
  "message": "model must be one of the following values: gemini, cohere, llama",
  "error": "Bad Request"
}
```

### 2. Missing Authentication
Remove the `Authorization` header
**Expected Response:** `401 Unauthorized`
```json
{
  "success": false,
  "statusCode": 401,
  "message": "Invalid or missing authentication token",
  "error": "Unauthorized"
}
```

### 3. Empty Prompt
```json
{
  "model": "gemini",
  "prompt": ""
}
```
**Expected Response:** `400 Bad Request`
```json
{
  "success": false,
  "statusCode": 400,
  "message": "prompt should not be empty",
  "error": "Bad Request"
}
```

### 4. Invalid Token
Use an expired or malformed token
**Expected Response:** `401 Unauthorized`

## 📊 Request Flow

```
1. Client sends request with JWT token
   ↓
2. Gateway validates token via Auth Service
   ↓
3. Gateway routes to appropriate AI service
   ↓
4. AI service generates response
   ↓
5. Gateway sends response to Summarizer
   ↓
6. Summarizer returns condensed response
   ↓
7. Gateway returns final response to client
```

## 🎯 Example Use Cases

### Use Case 1: Simple Question
```json
{
  "model": "gemini",
  "prompt": "What is the capital of France?"
}
```

### Use Case 2: Creative Writing
```json
{
  "model": "cohere",
  "prompt": "Write a haiku about technology"
}
```

### Use Case 3: Technical Explanation
```json
{
  "model": "llama",
  "prompt": "Explain REST APIs and their benefits"
}
```

### Use Case 4: Complex Query
```json
{
  "model": "gemini",
  "prompt": "Compare the differences between machine learning and deep learning, including use cases for each"
}
```

## 🔧 Troubleshooting

### Issue: 401 Unauthorized
**Solution:** 
- Ensure you have a valid JWT token
- Check if token is expired (login again)
- Verify token is set in collection variables
- Make sure Authorization header format is: `Bearer <token>`

### Issue: 400 Bad Request
**Solution:**
- Check request body format
- Ensure `model` is one of: `gemini`, `cohere`, `llama`
- Ensure `prompt` is not empty
- Verify Content-Type header is `application/json`

### Issue: 500 Internal Server Error
**Solution:**
- Check if all backend services are running:
  - Auth Service (port 3000)
  - Gemini Service (port 3001)
  - Cohere Service (port 3002)
  - Llama Service (port 3004)
  - Summarizer Service (port 3005)
- Check Gateway logs for detailed error

### Issue: Request Timeout
**Solution:**
- Default timeout is 30 seconds
- AI services may take time for complex prompts
- Check if backend services are responding
- Verify network connectivity

## 📝 Environment Variables

If you're running on different environments, update these:

### Local Development
```
base_url: http://localhost:3006
```

### Staging
```
base_url: https://staging-api.synthora.com
```

### Production
```
base_url: https://api.synthora.com
```

## 🚀 Best Practices

1. **Always use valid tokens** - Refresh tokens before they expire
2. **Test incrementally** - Start with simple prompts, then complex ones
3. **Monitor response times** - AI queries can take 5-30 seconds
4. **Handle errors gracefully** - Check status codes and error messages
5. **Use appropriate models** - Each model has different strengths:
   - **Gemini**: General purpose, good for explanations
   - **Cohere**: Great for creative writing and generation
   - **Llama**: Strong for technical and analytical tasks

## 📚 Additional Resources

- [Gateway README](./README.md) - Full service documentation
- [Architecture](./ARCHITECTURE.md) - System architecture details
- [NestJS Documentation](https://docs.nestjs.com) - Framework docs

## 💡 Tips

- Use the **Pre-request Script** tab to automate token refresh
- Use the **Tests** tab to add custom assertions
- Create **Environments** for different deployment stages
- Use **Collection Runner** for automated testing
- Export collection regularly to backup your tests

---

**Need Help?** Check the Gateway service logs for detailed error information:
```bash
cd apps/gateway
npm run dev
```
