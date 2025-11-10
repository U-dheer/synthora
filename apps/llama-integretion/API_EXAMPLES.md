# Hugging Face API Examples

## Chat Completion Endpoint

### Endpoint
```
POST /hugging-face/chat
```

### Request Body
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ]
}
```

### Example with Multiple Messages
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ]
}
```

### Response Format
```json
{
  "success": true,
  "message": {
    "role": "assistant",
    "content": "The capital of France is Paris."
  },
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message here"
}
```

## Testing with cURL

```bash
curl -X POST http://localhost:3000/hugging-face/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ]
  }'
```

## Testing with Postman

1. Set method to POST
2. URL: `http://localhost:3000/hugging-face/chat`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ]
}
```
