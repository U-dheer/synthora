import * as dotenv from 'dotenv';
dotenv.config();

const DEFAULT_PORT = 3006;

function normalizeServiceUrl(raw?: string | undefined, name?: string) {
  if (!raw) return undefined;
  try {
    // Use URL parsing to extract origin (protocol + host + port).
    // This intentionally strips any accidental path like `/gemini` which
    // previously caused the gateway to forward requests back to itself
    // (e.g. `http://localhost:3006/gemini` -> gateway recursion).
    const parsed = new URL(raw);
    const origin = parsed.origin; // e.g. http://localhost:3001
    if (parsed.pathname && parsed.pathname !== '/') {
      console.warn(
        `Warning: ${name || 'service'} URL contains a path portion. Stripping path and using origin: ${origin}`,
      );
    }
    return origin;
  } catch (e) {
    // If URL constructor fails, return the raw value so existing behaviour
    // is preserved and the caller can notice the misconfiguration.
    console.warn(`Could not parse ${name || 'service'} URL: ${raw}`);
    return raw;
  }
}

const port = Number(process.env.PORT || DEFAULT_PORT);

// Normalize each service URL to avoid accidental recursion and keep a clear
// shape for consumers of ServicesConfig.
const rawAuth = process.env.AUTH_SERVICE_URL;
const rawGemini = process.env.GEMINI_SERVICE_URL;
const rawCohere = process.env.COHERE_SERVICE_URL;
const rawLlama = process.env.LLAMA_SERVICE_URL;
const rawSummarizer = process.env.SUMMARIZER_SERVICE_URL;
const rawRag = process.env.RAG_SERVICE_URL;
const rawServiceSharedSecret = process.env.SERVICE_SHARED_SECRET;
const rawGeminiKey = process.env.GEMINI_API_KEY;
const rawCohereKey = process.env.COHERE_API_KEY;
const rawLlamaKey = process.env.LLAMA_API_KEY;
const rawGeminiKeyHeader = process.env.GEMINI_API_KEY_HEADER;
const rawCohereKeyHeader = process.env.COHERE_API_KEY_HEADER;
const rawLlamaKeyHeader = process.env.LLAMA_API_KEY_HEADER;

export const ServicesConfig = {
  port,
  auth: normalizeServiceUrl(rawAuth, 'AUTH_SERVICE_URL'),
  gemini: normalizeServiceUrl(rawGemini, 'GEMINI_SERVICE_URL'),
  cohere: normalizeServiceUrl(rawCohere, 'COHERE_SERVICE_URL'),
  llama: normalizeServiceUrl(rawLlama, 'LLAMA_SERVICE_URL'),
  summarizer: normalizeServiceUrl(rawSummarizer, 'SUMMARIZER_SERVICE_URL'),
  rag:
    normalizeServiceUrl(rawRag, 'RAG_SERVICE_URL') || 'http://localhost:8000',
  // Optional pre-shared secret that internal services can use to authenticate
  // to the gateway when calling internal endpoints. If set, services can set
  // `Authorization: Bearer <SERVICE_SHARED_SECRET>` and the gateway will accept
  // that token without forwarding to the auth service.
  serviceSharedSecret: rawServiceSharedSecret || undefined,
  // Comma-separated list of public paths that do NOT require authentication.
  // Supports optional method prefix like `GET:/public/*` or simple patterns `/auth/signup`.
  // Wildcard `*` at the end indicates prefix match.
  publicPaths: (
    process.env.GATEWAY_PUBLIC_PATHS ||
    '/auth/signup,/auth/login,/auth/refresh,/status,/health'
  )
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
};

// Expose any LLM API keys (if present) so upstream services can attach
// them when making outbound requests. Keep raw values here but do NOT
// print them directly; only masked presence is logged below.
(ServicesConfig as any).geminiApiKey = rawGeminiKey || undefined;
(ServicesConfig as any).cohereApiKey = rawCohereKey || undefined;
(ServicesConfig as any).llamaApiKey = rawLlamaKey || undefined;
// Header names to use when sending the API key to the downstream service.
// Default to `Authorization` when not set so existing deployments keep
// current behavior. These allow using `x-api-key` or other custom headers.
(ServicesConfig as any).geminiApiKeyHeader =
  rawGeminiKeyHeader || 'Authorization';
(ServicesConfig as any).cohereApiKeyHeader =
  rawCohereKeyHeader || 'Authorization';
(ServicesConfig as any).llamaApiKeyHeader =
  rawLlamaKeyHeader || 'Authorization';

// Sanity checks to catch the very common misconfiguration where a service URL
// accidentally points to the gateway, causing the gateway to forward to
// itself which results in 401 Unauthorized from the gateway guard.
try {
  const gatewayOrigin = `http://localhost:${port}`;
  ['gemini', 'cohere', 'llama', 'auth', 'summarizer', 'rag'].forEach((k) => {
    const val = (ServicesConfig as any)[k];
    if (!val) return;
    if (typeof val === 'string' && val.startsWith(gatewayOrigin)) {
      console.error(
        `Misconfiguration detected: ${k.toUpperCase()} service URL (${val}) appears to point to the gateway (${gatewayOrigin}). Please set the correct ${k.toUpperCase()} service URL in the environment (e.g. GEMINI_SERVICE_URL=http://localhost:3001).`,
      );
    }
  });
} catch (e) {
  // ignore
}

// Log which LLM API keys are configured (masked) to help operators debug
// authentication issues without leaking secrets.
try {
  function maskKey(k?: string | undefined) {
    if (!k) return 'NOT SET';
    try {
      if (k.length <= 8) return '****';
      return `${k.slice(0, 4)}...${k.slice(-4)}`;
    } catch (e) {
      return '****';
    }
  }

  console.info('LLM API keys (masked):', {
    gemini: maskKey((ServicesConfig as any).geminiApiKey),
    cohere: maskKey((ServicesConfig as any).cohereApiKey),
    llama: maskKey((ServicesConfig as any).llamaApiKey),
  });
  console.info('LLM API key header names:', {
    gemini: (ServicesConfig as any).geminiApiKeyHeader,
    cohere: (ServicesConfig as any).cohereApiKeyHeader,
    llama: (ServicesConfig as any).llamaApiKeyHeader,
  });
} catch (e) {
  // ignore logging errors
}

// Startup warning: if gateway expects a shared secret but RAG service isn't
// configured to send one, emit a warning to help developers catch this common
// misconfiguration. We only log locally — we cannot access RAG env from here
// at build time, so the message guides the operator to set `GATEWAY_SERVICE_TOKEN`
// in the RAG service environment when `SERVICE_SHARED_SECRET` is configured.
try {
  if (ServicesConfig.serviceSharedSecret) {
    const ragToken =
      process.env.GATEWAY_SERVICE_TOKEN || process.env.RAG_GATEWAY_TOKEN;
    if (!ragToken) {
      console.warn(
        'Configuration notice: Gateway has SERVICE_SHARED_SECRET set but RAG service does not have GATEWAY_SERVICE_TOKEN configured. Please set GATEWAY_SERVICE_TOKEN in the RAG service environment to avoid 401 Unauthorized when RAG calls the Gateway.',
      );
    }
  }
} catch (e) {
  // ignore
}
