# Ensenia CloudFlare Worker

MCP Server for AI-powered semantic search in Chilean education curriculum.

## Architecture

This CloudFlare Worker provides four main endpoints:

1. **POST /search** - Semantic search using Vectorize embeddings
2. **POST /fetch** - Retrieve curriculum content from D1 database
3. **POST /generate** - Generate Chilean-context educational content
4. **POST /validate** - Validate curriculum compliance
5. **GET /health** - Health check and service status

## Prerequisites

- Node.js 18+
- CloudFlare account with Workers enabled
- Wrangler CLI installed globally: `npm install -g wrangler`

## Setup

### 1. Install Dependencies

```bash
cd worker
npm install
```

### 2. Configure CloudFlare Account

Update `wrangler.toml` with your CloudFlare account ID:

```toml
account_id = "your-account-id-here"
```

### 3. Create D1 Database

```bash
wrangler d1 create ensenia-curriculum
```

Copy the database ID to `wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "ensenia-curriculum"
database_id = "your-database-id-here"
```

### 4. Create Vectorize Index

```bash
wrangler vectorize create curriculum-embeddings \
  --dimensions=768 \
  --metric=cosine
```

### 5. Create KV Namespace

```bash
wrangler kv:namespace create "SEARCH_CACHE"
```

Copy the namespace ID to `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "SEARCH_CACHE"
id = "your-kv-namespace-id-here"
```

### 6. Initialize Database Schema

Create database schema:

```bash
wrangler d1 execute ensenia-curriculum --file=../docs/schema.sql
```

### 7. Load Sample Data

Load sample curriculum data:

```bash
wrangler d1 execute ensenia-curriculum --file=../docs/sample-data.sql
```

## Development

Run local development server:

```bash
npm run dev
```

The worker will be available at `http://localhost:8787`

## Deployment

Deploy to CloudFlare:

```bash
npm run deploy
```

## Testing Endpoints

### Health Check

```bash
curl http://localhost:8787/health
```

### Search

```bash
curl -X POST http://localhost:8787/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Qué son las fracciones?",
    "grade": 5,
    "subject": "Matemática",
    "limit": 5
  }'
```

### Fetch Content

```bash
curl -X POST http://localhost:8787/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "content_ids": ["curr-mat-5-001", "curr-mat-5-002"]
  }'
```

### Generate Explanation

```bash
curl -X POST http://localhost:8787/generate \
  -H "Content-Type: application/json" \
  -d '{
    "context": "Las fracciones representan partes de un todo...",
    "query": "¿Cómo sumo fracciones?",
    "grade": 5,
    "subject": "Matemática",
    "oa_codes": ["OA-MAT-5-03"],
    "style": "explanation"
  }'
```

### Validate Content

```bash
curl -X POST http://localhost:8787/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Las fracciones son números que representan partes de un entero...",
    "grade": 5,
    "subject": "Matemática",
    "expected_oa": ["OA-MAT-5-03"]
  }'
```

## Type Checking

```bash
npm run type-check
```

## Project Structure

```
worker/
├── src/
│   ├── index.ts           # Main router
│   ├── types/
│   │   ├── env.ts         # Environment bindings
│   │   └── schemas.ts     # Request/response schemas
│   ├── routes/
│   │   ├── search.ts      # Search endpoint
│   │   ├── fetch.ts       # Fetch endpoint
│   │   ├── generate.ts    # Generate endpoint
│   │   └── validate.ts    # Validate endpoint
│   └── utils/
│       └── responses.ts   # Response utilities
├── wrangler.toml          # CloudFlare configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies
```

## Performance

- Search: ~500ms (with caching: ~10ms)
- Fetch: ~100ms
- Generate: ~500ms
- Validate: ~300ms
- **Total end-to-end: < 3 seconds**

## Caching Strategy

- **Hot cache (1 hour)**: Frequent search queries
- **Warm cache (24 hours)**: Regular content
- **Cold cache (7 days)**: Static ministry standards

## Environment Variables

Set in `wrangler.toml`:

- `ENVIRONMENT`: development | production
- `EMBEDDING_MODEL`: @cf/baai/bge-base-en-v1.5
- `GENERATION_MODEL`: @cf/meta/llama-3.1-8b-instruct
- `DEBUG`: true | false

## CloudFlare Services Used

- **Workers AI**: Embeddings + Text Generation
- **D1 Database**: Curriculum content storage
- **Vectorize**: Semantic search index
- **KV**: Response caching

## License

MIT
