#!/usr/bin/env bash
# Quick tester for LLM endpoints and summarizer via the gateway.
# Usage: GATEWAY_URL=http://localhost:3006 ACCESS_TOKEN=... ./scripts/test_llms.sh

set -euo pipefail
GATEWAY_URL=${GATEWAY_URL:-http://localhost:3006}
ACCESS_TOKEN=${ACCESS_TOKEN:-}
QUESTION=${QUESTION:-"Summarize the following content."}
CONTEXT=${CONTEXT:-"Sample context text to check LLM response."}

headers=( -H "Content-Type: application/json" )
if [ -n "$ACCESS_TOKEN" ]; then
  headers+=( -H "Authorization: Bearer $ACCESS_TOKEN" )
fi

echo "Gateway: $GATEWAY_URL"

call_endpoint() {
  local endpoint="$1"
  local body="$2"
  echo "\n--> POST $endpoint"
  http_status=$(curl -s -w "%{http_code}" -o /tmp/llm_resp.json -X POST "$GATEWAY_URL$endpoint" "${headers[@]}" -d "$body")
  echo "Status: $http_status"
  echo "Body:" 
  jq . /tmp/llm_resp.json || cat /tmp/llm_resp.json
}

# Test Gemini
call_endpoint "/gemini/gemini/make" '{"input":"'