RAG Service — Gateway Auth & Smoke Test

This file explains how to configure the Gateway <-> RAG service authentication and run a quick smoke test.

1) Set a shared secret on the Gateway (recommended for internal service calls)

On the machine where the Gateway runs, set an environment variable and restart the Gateway:

```bash
export SERVICE_SHARED_SECRET="synthora-internal-secret"
# restart the gateway (example)
cd "/media/uditha/Drives/Dev/Back End/Monorepo/synthora/apps/gateway"
npm run start:dev
```

2) Configure the RAG service to send the shared secret

On the machine where the RAG service runs, set `GATEWAY_SERVICE_TOKEN` to the same value:

```bash
cd "/media/uditha/Drives/Dev/Back End/Monorepo/synthora/apps/rag-service"
echo 'GATEWAY_SERVICE_TOKEN="synthora-internal-secret"' > .env
# restart RAG
./run.sh
```

3) Per-user authorization (optional)

If you prefer per-user authorization (the gateway validates user bearer tokens with the Auth service) then do NOT set `GATEWAY_SERVICE_TOKEN`. Instead, ensure clients pass `Authorization: Bearer <user-token>` on requests to the gateway. The RAG service will forward the incoming Authorization header to the gateway when making LLM/summarizer calls.

4) Smoke tests

- Health check (RAG):

```bash
curl -sS http://localhost:8000/rag/health | jq .
```

- Gateway reachable from RAG (checks gateway health):

```bash
curl -sS http://localhost:8000/rag/query/internal/llm-health | jq .
```

- Document-specific query (example):

```bash
curl -sS -X POST http://localhost:8000/rag/query/document-specific \
  -H "Content-Type: application/json" \
  -d '{"document_id":"47da2815-df53-409d-b143-a39167206ca3","question":"Give me a concise summary of Sri Lanka.","top_k":3}' | jq .
```

If your Gateway requires a shared secret and you did not set `GATEWAY_SERVICE_TOKEN`, you'll get `401 Unauthorized` for LLM/gateway calls. To fix, set `GATEWAY_SERVICE_TOKEN` as shown above or provide a valid user `Authorization` header on client requests.

5) Example client Authorization header (per-user):

```bash
curl -sS -X POST http://localhost:3006/rag/query/document-specific \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <user-or-service-token>" \
  -d '{"document_id":"...","question":"...","top_k":3}' | jq .
```

6) Troubleshooting

- If you still see `401 Unauthorized` in `llm_responses` from the RAG service, verify both the Gateway and RAG env vars match and that both services are restarted.
- Check logs for both services; RAG logs now mask Authorization values for safe debugging.
