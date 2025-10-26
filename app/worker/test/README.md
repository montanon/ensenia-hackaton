# CloudFlare Worker Test Suite

Comprehensive automated testing for the Ensenia AI Search CloudFlare Worker.

## Test Structure

```
test/
├── fixtures/              # Test data and mocks
│   ├── curriculum-data.ts # Sample curriculum data
│   └── mock-env.ts        # Mock CloudFlare environment
├── utils/                 # Unit tests for utilities
│   └── responses.test.ts  # Response helper tests
├── routes/                # Integration tests for endpoints
│   ├── fetch.test.ts      # Fetch endpoint tests
│   ├── generate.test.ts   # Generate endpoint tests
│   ├── validate.test.ts   # Validate endpoint tests
│   └── search.test.ts     # Search endpoint tests
└── e2e/                   # End-to-end tests
    └── worker.test.ts     # Full worker integration tests
```

## Running Tests

### Run All Tests
```bash
npm test
```

### Run Specific Test File
```bash
npm test -- test/routes/fetch.test.ts
```

### Run Tests in Watch Mode
```bash
npm test -- --watch
```

### Generate Coverage Report
```bash
npm test -- --coverage
```

## Test Coverage

### Unit Tests (utils/)
- ✅ JSON response creation
- ✅ Error response formatting
- ✅ CORS preflight handling
- ✅ JSON body parsing

### Integration Tests (routes/)

#### Fetch Endpoint
- ✅ Valid content fetching
- ✅ Empty array handling
- ✅ Nonexistent ID handling
- ✅ 50 ID limit enforcement
- ✅ JSON field parsing
- ✅ Database error handling
- ✅ Input validation

#### Generate Endpoint
- ✅ Text generation with all styles
- ✅ Chilean context prompts
- ✅ OA code handling
- ✅ Input validation (context, query, grade, subject)
- ✅ AI model error handling
- ✅ Empty response handling

#### Validate Endpoint
- ✅ Content validation
- ✅ Score calculation (weighted)
- ✅ Pass/fail threshold (70%)
- ✅ Issue and recommendation parsing
- ✅ Ministry standards integration
- ✅ Malformed AI response handling
- ✅ Score clamping (0-100)

#### Search Endpoint
- ✅ Semantic search
- ✅ Metadata retrieval
- ✅ Limit parameter enforcement
- ✅ Caching (cache hit/miss)
- ✅ Grade and subject filtering
- ✅ Embedding generation
- ✅ Empty result handling
- ✅ Input validation

### End-to-End Tests (e2e/)
- ✅ Health check endpoint
- ✅ CORS handling
- ✅ Route resolution
- ✅ Error handling
- ✅ Full search → fetch workflow
- ✅ Performance metrics

## Test Fixtures

### Mock Environment
The `createMockEnv()` function provides a fully mocked CloudFlare environment with:
- Mock AI service (embeddings + generation)
- Mock D1 database
- Mock Vectorize index
- Mock KV cache

### Sample Data
- **curriculum-data.ts**: Valid and invalid request fixtures
- All data aligned with Chilean Ministry of Education standards
- Realistic test scenarios for 5° Básico Matemática

## Writing New Tests

### Example: Testing a New Endpoint

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { handleYourEndpoint } from '../../src/routes/your-endpoint';
import { createMockEnv } from '../fixtures/mock-env';

describe('Your Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  it('should do something', async () => {
    const request = new Request('http://test.com/your-endpoint', {
      method: 'POST',
      body: JSON.stringify({ data: 'test' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await handleYourEndpoint(request, env);
    expect(response.status).toBe(200);
  });
});
```

## Test Patterns

### 1. Arrange-Act-Assert
All tests follow the AAA pattern:
```typescript
it('should validate input', async () => {
  // Arrange
  const request = createTestRequest();

  // Act
  const response = await handler(request, env);

  // Assert
  expect(response.status).toBe(400);
});
```

### 2. Test Both Success and Failure
Every endpoint has tests for:
- Valid requests (happy path)
- Invalid requests (error cases)
- Edge cases
- Integration failures

### 3. Mock External Dependencies
- AI services are mocked to return predictable results
- Database queries return controlled test data
- No actual CloudFlare services are called

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: npm test -- --coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Performance Testing

Tests include timing assertions to ensure:
- Health checks: < 100ms
- Database queries: < 10ms (mocked)
- Response time metrics are included

## Debugging Tests

### Verbose Output
```bash
npm test -- --reporter=verbose
```

### Single Test
```bash
npm test -- -t "should fetch content by IDs"
```

### Debug Mode
```bash
npm test -- --inspect-brk
```

## Known Limitations

1. **Workers AI**: Tests use mocks; real AI behavior not tested
2. **Vectorize**: Tests use mocks; actual search quality not verified
3. **Network**: No real HTTP requests; integration with CloudFlare not tested

For full production validation, deploy to CloudFlare and run manual tests with real services.

## Test Metrics

- **Total Tests**: 100+
- **Coverage Target**: > 80%
- **Test Execution Time**: < 10 seconds
- **Reliability**: All tests should pass consistently

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass: `npm test`
3. Check coverage: `npm test -- --coverage`
4. Update this README if needed
