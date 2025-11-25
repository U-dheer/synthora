#!/usr/bin/env bash
# Simple runnable script with curl commands for a common flow:
# 1) Login
# 2) Upload a document to RAG
# 3) Query the RAG
# 4) Use /ask orchestration
# Requires: curl, jq (for JSON parsing)

set -euo pipefail

# Config - edit as needed
GATEWAY_URL=${GATEWAY_URL:-http://localhost:3006}
EMAIL=${EMAIL:-user@example.com}
PASSWORD=${PASSWORD:-Password123}
PDF_FILE=${PDF_FILE:-./example.pdf}

echo "Using GATEWAY_URL=$GATEWAY_URL"

# 1) Login
echo "\n==> Logging in as $EMAIL"
LOGIN_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

echo "Login response: $LOGIN_RESPONSE"

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.accessToken // .access_token // empty')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refreshToken // .refresh_token // empty')
USER_ID=$(echo "$LOGIN_RESPONSE" | jq -r '.userId // .user_id // empty')

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to obtain access token from login response. Exiting." >&2
  exit 1
fi

echo "Obtained ACCESS_TOKEN (truncated): ${ACCESS_TOKEN:0:20}..."

# 2) Upload a PDF to RAG (form-data)
if [ -f "$PDF_FILE" ]; then
  echo "\n==> Uploading file $PDF_FILE to /rag/documents/upload"
  UPLOAD_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/rag/documents/upload" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "file=@$PDF_FILE" )
  echo "Upload response: $UPLOAD_RESPONSE"
  DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id // .documentId // .id // empty')
  if [ -n "$DOCUMENT_ID" ]; then
    echo "Stored DOCUMENT_ID=$DOCUMENT_ID"
  else
    echo "No document id returned by upload (response may differ)." >&2
  fi
else
  echo "PDF file $PDF_FILE not found — skipping upload step. Set PDF_FILE to a valid path." >&2
fi

# 3) Query RAG
echo "\n==> Querying RAG for: 'What is transfer learning?'"
RAG_QUERY_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/rag/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"question":"What is transfer learning?","top_k":5}')

echo "RAG query response: $RAG_QUERY_RESPONSE"

# 4) Call /ask orchestration
echo "\n==> Calling /ask orchestration"
ASK_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/ask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"question":"Explain transfer learning in simple terms"}')

echo "Ask response: $ASK_RESPONSE"

# 5) Example: Refresh token (optional)
if [ -n "$REFRESH_TOKEN" ]; then
  echo "\n==> Refreshing tokens using refreshToken"
  REFRESH_RESPONSE=$(curl -s -X POST "$GATEWAY_URL/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refreshToken\": \"$REFRESH_TOKEN\"}")
  echo "Refresh response: $REFRESH_RESPONSE"
fi

echo "\nFlow complete."
