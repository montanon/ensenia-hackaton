/**
 * End-to-end tests for the worker
 */

import { describe, it, expect, beforeEach } from 'vitest';
import worker from '../../src/index';
import { createMockEnv, createMockContext } from '../fixtures/mock-env';
import { mockCurriculumContent } from '../fixtures/curriculum-data';
import { Env } from '../../src/types/env';

describe('Worker E2E Tests', () => {
  let env: Env;
  let ctx: ExecutionContext;

  beforeEach(() => {
    env = createMockEnv();
    ctx = createMockContext();

    // Setup common mocks
    env.DB.prepare = (query: string) => ({
      bind: (...params: any[]) => ({
        all: async () => ({ success: true, results: [mockCurriculumContent] }),
        first: async () => ({ success: true }),
      }),
      first: async () => ({ success: true }),
    }) as any;
  });

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const request = new Request('http://test.com/health');

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body.status).toBe('healthy');
      expect(body.services.database).toBe('healthy');
    });

    it('should report degraded status on database failure', async () => {
      env.DB.prepare = () => {
        throw new Error('Database connection failed');
      };

      const request = new Request('http://test.com/health');

      const response = await worker.fetch(request, env, ctx);
      const body = await response.json();

      expect(body.status).toBe('degraded');
      expect(body.services.database).toBe('unhealthy');
    });
  });

  describe('CORS Handling', () => {
    it('should handle OPTIONS preflight requests', async () => {
      const request = new Request('http://test.com/search', {
        method: 'OPTIONS',
      });

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(204);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    it('should include CORS headers in responses', async () => {
      const request = new Request('http://test.com/health');

      const response = await worker.fetch(request, env, ctx);
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toBeTruthy();
    });
  });

  describe('Routing', () => {
    it('should route /health to health check handler', async () => {
      const request = new Request('http://test.com/health');

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('status');
    });

    it('should route /fetch to fetch handler', async () => {
      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['test-id'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('contents');
    });

    it('should return 404 for unknown routes', async () => {
      const request = new Request('http://test.com/unknown-endpoint');

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(404);

      const body = await response.json();
      expect(body.code).toBe('NOT_FOUND');
      expect(body.message).toContain('/unknown-endpoint');
    });

    it('should return 405 for unsupported methods', async () => {
      const request = new Request('http://test.com/search', {
        method: 'GET',
      });

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(405);

      const body = await response.json();
      expect(body.code).toBe('METHOD_NOT_ALLOWED');
    });
  });

  describe('Error Handling', () => {
    it('should catch and return 500 for unexpected errors', async () => {
      env.DB.prepare = () => {
        throw new Error('Unexpected database error');
      };

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['test'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await worker.fetch(request, env, ctx);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body).toHaveProperty('error');
      expect(body).toHaveProperty('code');
    });

    it('should include error messages in responses', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify({ query: 'ab', grade: 5, subject: 'Matemática' }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await worker.fetch(request, env, ctx);
      const body = await response.json();

      expect(body).toHaveProperty('message');
      expect(body.message.length).toBeGreaterThan(0);
    });
  });

  describe('Full Workflow', () => {
    it('should complete search -> fetch workflow', async () => {
      // Setup mocks for full workflow
      env.AI.run = async () => ({
        shape: [1, 768],
        data: [[...Array(768)].map(() => Math.random())],
      });

      env.VECTOR_INDEX.query = async () => ({
        count: 1,
        matches: [
          {
            id: 'curr-mat-5-001',
            score: 0.95,
            metadata: { title: 'Test Content', oa: 'OA-MAT-5-03' },
          },
        ],
      });

      // Step 1: Search
      const searchRequest = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify({
          query: '¿Qué son las fracciones?',
          grade: 5,
          subject: 'Matemática',
        }),
        headers: { 'Content-Type': 'application/json' },
      });

      const searchResponse = await worker.fetch(searchRequest, env, ctx);
      expect(searchResponse.status).toBe(200);

      const searchBody = await searchResponse.json();
      expect(searchBody.content_ids.length).toBeGreaterThan(0);

      // Step 2: Fetch content using IDs from search
      const fetchRequest = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: searchBody.content_ids }),
        headers: { 'Content-Type': 'application/json' },
      });

      const fetchResponse = await worker.fetch(fetchRequest, env, ctx);
      expect(fetchResponse.status).toBe(200);

      const fetchBody = await fetchResponse.json();
      expect(fetchBody.contents.length).toBeGreaterThan(0);
    });
  });

  describe('Performance', () => {
    it('should respond quickly to health checks', async () => {
      const start = Date.now();
      const request = new Request('http://test.com/health');

      await worker.fetch(request, env, ctx);
      const duration = Date.now() - start;

      expect(duration).toBeLessThan(100); // Should be < 100ms
    });

    it('should include timing information in responses', async () => {
      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['test-id'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await worker.fetch(request, env, ctx);
      const body = await response.json();

      expect(body).toHaveProperty('fetch_time_ms');
      expect(typeof body.fetch_time_ms).toBe('number');
      expect(body.fetch_time_ms).toBeGreaterThanOrEqual(0);
    });
  });
});
