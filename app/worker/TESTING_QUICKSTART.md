# Testing Quick Start Guide

## TL;DR

```bash
# Install dependencies (if not done)
npm install

# Run all tests
npm test

# Watch mode (recommended for development)
npm run test:watch

# Coverage report
npm run test:coverage
```

## What We've Built

✅ **83 automated test cases** across 6 test files
✅ **~1,700 lines of test code**
✅ **Complete coverage** of all endpoints
✅ **Mock CloudFlare environment** (no real API calls)

## Test Files Overview

| File | Size | Tests | Purpose |
|------|------|-------|---------|
| `responses.test.ts` | 3.9K | 15 | Utility functions |
| `fetch.test.ts` | 6.5K | 13 | Fetch endpoint |
| `generate.test.ts` | 8.2K | 17 | Generate endpoint |
| `validate.test.ts` | 10K | 20 | Validate endpoint |
| `search.test.ts` | 12K | 23 | Search endpoint |
| `worker.test.ts` | 7.6K | 15 | E2E integration |

## Common Commands

### Development
```bash
# Auto-run tests on file changes
npm run test:watch

# Run specific test file
npm test -- test/routes/fetch.test.ts

# Run tests matching a pattern
npm test -- -t "should fetch content"
```

### CI/CD
```bash
# Run all tests (exit on failure)
npm test

# Generate coverage report
npm run test:coverage

# Type checking
npm run type-check
```

### Debugging
```bash
# Verbose output
npm test -- --reporter=verbose

# Single test
npm test -- -t "should validate input"

# UI mode (browser-based)
npm run test:ui
```

## Example Test Run

```
$ npm test

✓ test/utils/responses.test.ts (15)
  ✓ jsonResponse creates valid responses
  ✓ errorResponse formats errors correctly
  ✓ CORS headers are present

✓ test/routes/fetch.test.ts (13)
  ✓ fetches content by IDs
  ✓ handles empty arrays
  ✓ validates input

✓ test/routes/generate.test.ts (17)
  ✓ generates text with AI
  ✓ handles all styles
  ✓ validates Chilean context

✓ test/routes/validate.test.ts (20)
  ✓ validates content
  ✓ calculates scores
  ✓ parses AI responses

✓ test/routes/search.test.ts (23)
  ✓ performs semantic search
  ✓ caches results
  ✓ filters by grade/subject

✓ test/e2e/worker.test.ts (15)
  ✓ health check works
  ✓ CORS is configured
  ✓ routes are resolved

Test Files  6 passed (6)
Tests  83 passed (83)
Duration  4.23s
```

## What's Tested

### ✅ All Endpoints
- GET /health
- POST /search
- POST /fetch
- POST /generate
- POST /validate

### ✅ All Validation
- Input length checks
- Grade range (1-12)
- Subject presence
- Array non-empty
- JSON parsing

### ✅ All Error Cases
- 400 (Bad Request)
- 404 (Not Found)
- 405 (Method Not Allowed)
- 500 (Internal Server Error)

### ✅ All Integrations
- D1 Database
- Workers AI
- Vectorize
- KV Cache

### ✅ Chilean Education Context
- OA codes
- Ministry standards
- Spanish prompts
- Grade levels

## Test Structure

```
test/
├── fixtures/              # Shared test data
│   ├── mock-env.ts       # Mock CloudFlare environment
│   └── curriculum-data.ts # Sample requests/responses
│
├── utils/                 # Unit tests
│   └── responses.test.ts
│
├── routes/                # Integration tests
│   ├── fetch.test.ts
│   ├── generate.test.ts
│   ├── validate.test.ts
│   └── search.test.ts
│
└── e2e/                   # End-to-end tests
    └── worker.test.ts
```

## Writing a Test

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { handleFetch } from '../../src/routes/fetch';
import { createMockEnv } from '../fixtures/mock-env';

describe('Fetch Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  it('should fetch content by IDs', async () => {
    // Arrange
    const request = new Request('http://test.com/fetch', {
      method: 'POST',
      body: JSON.stringify({ content_ids: ['test-id'] }),
      headers: { 'Content-Type': 'application/json' },
    });

    // Act
    const response = await handleFetch(request, env);

    // Assert
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body).toHaveProperty('contents');
  });
});
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run type-check
      - run: npm test
      - run: npm run test:coverage
```

## Troubleshooting

### Tests Won't Run
```bash
# Check Node version (need 18+)
node --version

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Tests Are Slow
```bash
# Run specific file instead of all
npm test -- test/routes/fetch.test.ts

# Use watch mode (faster)
npm run test:watch
```

### Coverage Not Generated
```bash
# Install coverage provider
npm install -D @vitest/coverage-v8

# Run coverage
npm run test:coverage
```

## Next Steps

1. **Run tests locally**: `npm test`
2. **Check coverage**: `npm run test:coverage`
3. **Set up CI/CD**: Add GitHub Actions
4. **Keep tests updated**: Add tests for new features
5. **Monitor coverage**: Aim for > 80%

## Documentation

- **test/README.md**: Comprehensive test documentation
- **TEST_SUITE_SUMMARY.md**: Complete test inventory
- **This file**: Quick start guide

## Support

Tests failing? Check:
1. Node version: `node --version` (need 18+)
2. Dependencies installed: `npm install`
3. TypeScript compiles: `npm run type-check`
4. Test files exist: `ls test/**/*.test.ts`

---

**Happy Testing! 🧪**
