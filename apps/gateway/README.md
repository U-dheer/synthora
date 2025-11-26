# Gateway Service

API Gateway service for the Synthora AI platform. This service acts as a single entry point for all client requests and routes them to appropriate microservices.

## Architecture

The gateway service is built with NestJS and provides:
- **Authentication**: Token validation via Auth service
- **Request Routing**: Routes AI queries to appropriate model services (Gemini, Cohere, Llama)
- **Response Processing**: Automatically summarizes AI responses
- **Proxy Middleware**: Direct proxying for service-specific endpoints
- **Centralized Error Handling**: Consistent error responses across all services

## Project Structure

```
src/
├── config/              # Service configuration and environment variables
├── constants/           # Application constants and enums
├── controllers/         # Request handlers
├── dtos/               # Data Transfer Objects with validation
├── guards/             # Authentication guards
├── interfaces/         # TypeScript interfaces
├── middlewares/        # HTTP proxy middleware
├── services/           # Business logic services
├── app.module.ts       # Main application module
└── main.ts            # Application entry point
```

## Features

### 1. AI Query Routing
- Accepts AI queries with model selection (Gemini, Cohere, Llama)
- Routes to appropriate microservice
- Automatically summarizes responses
- Returns structured response with metadata

### 2. Authentication
- JWT token validation via Auth service
- Protects all gateway endpoints
- Extracts user information from tokens

### 3. Service Proxying
- Direct proxying to backend services
- Supports all HTTP methods
- Automatic origin header handling

## API Endpoints

### POST /gateway/query
Process an AI query.

**Request:**
```json
{
  "model": "gemini",
  "prompt": "Your question here"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "AI generated response",
    "model": "gemini",
    "timestamp": "2025-11-12T00:00:00.000Z"
  },
  "message": "Request processed successfully"
}
```

### POST /gateway/health
Health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "timestamp": "2025-11-12T00:00:00.000Z",
    "service": "gateway"
  }
}
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 3006 |
| NODE_ENV | Environment | development |
| CORS_ORIGIN | CORS allowed origins | * |
| AUTH_SERVICE_URL | Auth service URL | http://localhost:3000 |
| GEMINI_SERVICE_URL | Gemini service URL | http://localhost:3001 |
| COHERE_SERVICE_URL | Cohere service URL | http://localhost:3002 |
| LLAMA_SERVICE_URL | Llama service URL | http://localhost:3004 |
| SUMMARIZER_SERVICE_URL | Summarizer service URL | http://localhost:3005 |

## Installation

```bash
npm install
```

## Running the Service

### Development Mode
```bash
npm run dev
# or
npm run start:dev
```

### Production Mode
```bash
npm run build
npm run start:prod
```

### Debug Mode
```bash
npm run start:debug
```

## Service-to-Service Auth Notice

If you set `SERVICE_SHARED_SECRET` for the gateway, internal services (like the RAG service)
must provide the same secret when calling internal endpoints. Set the environment variable
`GATEWAY_SERVICE_TOKEN` in the RAG service environment to match the gateway secret, for
example:

```bash
export SERVICE_SHARED_SECRET="synthora-internal-secret"
export GATEWAY_SERVICE_TOKEN="synthora-internal-secret"
```

If the RAG service is not configured with `GATEWAY_SERVICE_TOKEN` but the gateway has
`SERVICE_SHARED_SECRET` set, the gateway will reject requests from RAG with `401 Unauthorized`.
The gateway emits a startup warning to help detect this misconfiguration.

## Testing

### Unit Tests
```bash
npm run test
```

### E2E Tests
```bash
npm run test:e2e
```

### Test Coverage
```bash
npm run test:cov
```

## Development

### Code Linting
```bash
npm run lint
```

### Code Formatting
```bash
npm run format
```

## Dependencies

### Required Services
- Auth Service (port 3000)
- AI Model Services:
  - Gemini Service (port 3001)
  - Cohere Service (port 3002)
  - Llama Service (port 3004)
- Summarizer Service (port 3005)

## Error Handling

The gateway provides standardized error responses:

```json
{
  "statusCode": 400,
  "message": "Error description",
  "error": "Bad Request"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid model, validation errors)
- `401` - Unauthorized (invalid/missing token)
- `500` - Internal Server Error (service failures)

## License

UNLICENSED

  <!--[![Backers on Open Collective](https://opencollective.com/nest/backers/badge.svg)](https://opencollective.com/nest#backer)
  [![Sponsors on Open Collective](https://opencollective.com/nest/sponsors/badge.svg)](https://opencollective.com/nest#sponsor)-->

## Description

[Nest](https://github.com/nestjs/nest) framework TypeScript starter repository.

## Project setup

```bash
$ npm install
```

## Compile and run the project

```bash
# development
$ npm run start

# watch mode
$ npm run start:dev

# production mode
$ npm run start:prod
```

## Run tests

```bash
# unit tests
$ npm run test

# e2e tests
$ npm run test:e2e

# test coverage
$ npm run test:cov
```

## Deployment

When you're ready to deploy your NestJS application to production, there are some key steps you can take to ensure it runs as efficiently as possible. Check out the [deployment documentation](https://docs.nestjs.com/deployment) for more information.

If you are looking for a cloud-based platform to deploy your NestJS application, check out [Mau](https://mau.nestjs.com), our official platform for deploying NestJS applications on AWS. Mau makes deployment straightforward and fast, requiring just a few simple steps:

```bash
$ npm install -g @nestjs/mau
$ mau deploy
```

With Mau, you can deploy your application in just a few clicks, allowing you to focus on building features rather than managing infrastructure.

## Resources

Check out a few resources that may come in handy when working with NestJS:

- Visit the [NestJS Documentation](https://docs.nestjs.com) to learn more about the framework.
- For questions and support, please visit our [Discord channel](https://discord.gg/G7Qnnhy).
- To dive deeper and get more hands-on experience, check out our official video [courses](https://courses.nestjs.com/).
- Deploy your application to AWS with the help of [NestJS Mau](https://mau.nestjs.com) in just a few clicks.
- Visualize your application graph and interact with the NestJS application in real-time using [NestJS Devtools](https://devtools.nestjs.com).
- Need help with your project (part-time to full-time)? Check out our official [enterprise support](https://enterprise.nestjs.com).
- To stay in the loop and get updates, follow us on [X](https://x.com/nestframework) and [LinkedIn](https://linkedin.com/company/nestjs).
- Looking for a job, or have a job to offer? Check out our official [Jobs board](https://jobs.nestjs.com).

## Support

Nest is an MIT-licensed open source project. It can grow thanks to the sponsors and support by the amazing backers. If you'd like to join them, please [read more here](https://docs.nestjs.com/support).

## Stay in touch

- Author - [Kamil Myśliwiec](https://twitter.com/kammysliwiec)
- Website - [https://nestjs.com](https://nestjs.com/)
- Twitter - [@nestframework](https://twitter.com/nestframework)

## License

Nest is [MIT licensed](https://github.com/nestjs/nest/blob/master/LICENSE).
