# Gateway Service Architecture

## Overview
The Gateway Service acts as the single entry point for the Synthora AI platform, providing authentication, routing, and request processing capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT REQUESTS                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    GATEWAY SERVICE                           │
│                     (Port 3006)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Global Middleware                      │    │
│  │  • CORS Handler                                     │    │
│  │  • Validation Pipe (DTO Validation)                 │    │
│  │  • Exception Filter (Error Handling)                │    │
│  │  • Proxy Middleware (Service Routing)               │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Authentication                         │    │
│  │  • AuthGuard (JWT Validation)                       │    │
│  │  • Token Extraction & Verification                  │    │
│  │  • User Context Injection                           │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │               Controllers                           │    │
│  │  • GatewayController                                │    │
│  │    - POST /gateway/query                            │    │
│  │    - POST /gateway/health                           │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │                Services                             │    │
│  │  • AiRoutingService                                 │    │
│  │    - Model selection logic                          │    │
│  │    - Request routing                                │    │
│  │    - Response summarization                         │    │
│  │    - Error handling                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────┬───────────────┬───────────────┬──────────────────┘
           │               │               │
           ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│  Auth Service   │ │ AI Services │ │ Summarizer  │
│   (Port 3000)   │ │ - Gemini    │ │ (Port 3005) │
│                 │ │ - Cohere    │ │             │
│  • Validate JWT │ │ - Llama     │ │ • Summarize │
│  • Return user  │ │             │ │   responses │
└─────────────────┘ └─────────────┘ └─────────────┘
```

## Request Flow

### 1. AI Query Request Flow
```
Client Request
    │
    ▼
[CORS Check]
    │
    ▼
[Validation Pipe] ──> Validates AiQueryDto
    │                  - model: string (gemini|cohere|llama)
    │                  - prompt: string
    ▼
[AuthGuard] ──────────> Calls Auth Service
    │                   - Validates JWT token
    │                   - Injects user context
    ▼
[GatewayController]
    │
    ▼
[AiRoutingService]
    │
    ├──> Select Model Endpoint
    │    (based on model parameter)
    │
    ├──> Call AI Service
    │    POST /generate
    │    { prompt, userId }
    │
    ├──> Call Summarizer Service
    │    POST /summarize
    │    { text: aiResponse }
    │
    └──> Return Response
         {
           success: true,
           data: {
             response: string,
             model: string,
             timestamp: string
           }
         }
```

### 2. Proxy Request Flow
```
Client Request to /auth/* or /ai/*
    │
    ▼
[ProxyMiddleware]
    │
    ├──> Match Route Pattern
    │    - /auth/*       → Auth Service
    │    - /ai/gemini/*  → Gemini Service
    │    - /ai/cohere/*  → Cohere Service
    │    - /ai/llama/*   → Llama Service
    │    - /ai/summarize → Summarizer Service
    │
    └──> Forward Request
         (with original headers, body, method)
```

## Component Responsibilities

### Controllers Layer
- **GatewayController**
  - Handle HTTP requests
  - Apply guards and validation
  - Format responses
  - Coordinate with services

### Services Layer
- **AiRoutingService**
  - Business logic for query routing
  - Model selection
  - Service orchestration
  - Error handling

### Guards Layer
- **AuthGuard**
  - JWT token validation
  - User authentication
  - Context injection

### Middleware Layer
- **ProxyMiddleware**
  - Route matching
  - Request forwarding
  - Service proxying

### DTOs Layer
- **AiQueryDto**
  - Request validation
  - Type safety
  - Input sanitization

### Filters Layer
- **AllExceptionsFilter**
  - Global error handling
  - Error logging
  - Standardized error responses

### Configuration Layer
- **services.config.ts**
  - Service URLs
  - Environment variables
  - Configuration management

### Constants Layer
- **ai-models.constant.ts**
  - Model types
  - Valid model list
- **http.constant.ts**
  - Error messages
  - Route patterns

### Interfaces Layer
- **api-response.interface.ts**
  - Response structure
  - Type definitions
- **service.interface.ts**
  - Service configuration types
  - User types

## Error Handling Strategy

```
Error Occurs
    │
    ▼
[Try-Catch in Service/Controller]
    │
    ├──> Known Error (HttpException)
    │    - Status code from exception
    │    - Message from exception
    │
    └──> Unknown Error
         - 500 Internal Server Error
         - Generic message
    │
    ▼
[AllExceptionsFilter]
    │
    ├──> Log Error Details
    │    - Method, URL, Status
    │    - Error message & stack
    │
    └──> Return Formatted Response
         {
           success: false,
           statusCode: number,
           timestamp: string,
           path: string,
           method: string,
           message: string,
           error: string
         }
```

## Security Features

1. **Authentication**
   - JWT token validation on all endpoints
   - Token verification via Auth service
   - User context injection

2. **Validation**
   - DTO validation with class-validator
   - Whitelist unknown properties
   - Transform input data

3. **CORS**
   - Configurable origins
   - Credential support
   - Environment-based configuration

4. **Error Handling**
   - No sensitive data in errors
   - Consistent error format
   - Detailed logging (server-side only)

## Performance Considerations

1. **Timeouts**
   - 30-second timeout on AI service calls
   - Prevents hanging requests

2. **Error Recovery**
   - Proper error handling
   - Graceful degradation
   - Clear error messages

3. **Logging**
   - Request/response logging
   - Error tracking
   - Performance monitoring ready

## Configuration

### Environment Variables
All critical configuration is externalized:
- Service URLs (AUTH, GEMINI, COHERE, LLAMA, SUMMARIZER)
- Server port
- CORS origins
- Environment mode

### Defaults
- Development-friendly defaults
- Easy local setup
- Production-ready configuration

## Testing Strategy

1. **Unit Tests**
   - Controller tests (gateway.controller.spec.ts)
   - Service tests
   - Guard tests

2. **E2E Tests**
   - Full request flow
   - Integration with services
   - Error scenarios

3. **Coverage**
   - Comprehensive test coverage
   - Critical path testing

## Scalability

The gateway is designed to scale:
- Stateless design
- No session storage
- Horizontal scaling ready
- Load balancer compatible

## Monitoring & Observability

Current logging includes:
- Request routing
- Authentication events
- Service calls
- Errors and exceptions

Ready for integration with:
- Prometheus metrics
- ELK stack
- Distributed tracing
- APM tools
