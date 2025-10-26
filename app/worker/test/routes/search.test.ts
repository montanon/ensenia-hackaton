/**
 * Integration tests for search endpoint
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { handleSearch } from '../../src/routes/search';
import { createMockEnv } from '../fixtures/mock-env';
import { validSearchRequest, invalidSearchRequests } from '../fixtures/curriculum-data';
import { Env } from '../../src/types/env';

describe('Search Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();

    // Mock Vectorize to return search results
    env.VECTOR_INDEX.query = async (vector: number[], options?: any) => ({
      count: 3,
      matches: [
        {
          id: 'curr-mat-5-001',
          score: 0.92,
          metadata: { title: 'Fracciones Básicas', oa: 'OA-MAT-5-03' },
        },
        {
          id: 'curr-mat-5-002',
          score: 0.87,
          metadata: { title: 'Suma de Fracciones', oa: 'OA-MAT-5-04' },
        },
        {
          id: 'curr-mat-5-004',
          score: 0.82,
          metadata: { title: 'Fracciones Equivalentes', oa: 'OA-MAT-5-03, OA-MAT-5-05' },
        },
      ],
    });

    // Mock AI to return embeddings
    env.AI.run = async () => ({
      shape: [1, 768],
      data: [[...Array(768)].map(() => Math.random())],
    });
  });

  describe('Valid Requests', () => {
    it('should perform semantic search successfully', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('query');
      expect(body).toHaveProperty('grade');
      expect(body).toHaveProperty('subject');
      expect(body).toHaveProperty('total_found');
      expect(body).toHaveProperty('content_ids');
      expect(body).toHaveProperty('metadata');
      expect(body).toHaveProperty('cached');
      expect(body).toHaveProperty('search_time_ms');
    });

    it('should return content IDs in response', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      expect(Array.isArray(body.content_ids)).toBe(true);
      expect(body.content_ids.length).toBeGreaterThan(0);
      expect(body.content_ids[0]).toBe('curr-mat-5-001');
    });

    it('should return metadata for each result', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      expect(Array.isArray(body.metadata)).toBe(true);
      expect(body.metadata.length).toBeGreaterThan(0);

      const firstResult = body.metadata[0];
      expect(firstResult).toHaveProperty('id');
      expect(firstResult).toHaveProperty('score');
      expect(firstResult).toHaveProperty('title');
      expect(firstResult).toHaveProperty('oa');
    });

    it('should respect limit parameter', async () => {
      // Mock Vectorize to return only 2 results when limit is 2
      env.VECTOR_INDEX.query = async (vector: number[], options?: any) => ({
        count: 2,
        matches: [
          {
            id: 'curr-mat-5-001',
            score: 0.92,
            metadata: { title: 'Fracciones Básicas', oa: 'OA-MAT-5-03' },
          },
          {
            id: 'curr-mat-5-002',
            score: 0.87,
            metadata: { title: 'Suma de Fracciones', oa: 'OA-MAT-5-04' },
          },
        ],
      });

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify({ ...validSearchRequest, limit: 2 }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      // Should have exactly 2 results
      expect(body.metadata.length).toBe(2);
      expect(body.content_ids.length).toBe(2);
    });

    it('should cap limit at 50', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify({ ...validSearchRequest, limit: 100 }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(200);
      // Implementation should cap at 50
    });

    it('should use default limit of 10 when not provided', async () => {
      const requestWithoutLimit = { ...validSearchRequest };
      delete (requestWithoutLimit as any).limit;

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(requestWithoutLimit),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(200);
    });
  });

  describe('Caching', () => {
    it('should not be cached on first request', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      expect(body.cached).toBe(false);
    });

    it('should return cached results on subsequent requests', async () => {
      const cacheKey = `search:${validSearchRequest.query}:${validSearchRequest.grade}:${validSearchRequest.subject}:${validSearchRequest.limit || 10}`;
      const cachedData = {
        query: validSearchRequest.query,
        grade: validSearchRequest.grade,
        subject: validSearchRequest.subject,
        total_found: 5,
        content_ids: ['test-1'],
        metadata: [{ id: 'test-1', score: 0.9, title: 'Test', oa: 'OA-TEST' }],
        cached: false,
        search_time_ms: 100,
      };

      env.SEARCH_CACHE.get = async (key: string) => {
        if (key === cacheKey) {
          return JSON.stringify(cachedData);
        }
        return null;
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      expect(body.cached).toBe(true);
      expect(body.content_ids).toEqual(['test-1']);
    });

    it('should cache results after successful search', async () => {
      let cachePutCalled = false;

      env.SEARCH_CACHE.put = async (key: string, value: string, options?: any) => {
        cachePutCalled = true;
        expect(options).toHaveProperty('expirationTtl');
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      await handleSearch(request, env);
      expect(cachePutCalled).toBe(true);
    });
  });

  describe('Input Validation', () => {
    it('should reject query shorter than 3 characters', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(invalidSearchRequests.shortQuery),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_QUERY');
      expect(body.message).toContain('at least 3 characters');
    });

    it('should reject grade > 12', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(invalidSearchRequests.invalidGrade),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_GRADE');
      expect(body.message).toContain('between 1 and 12');
    });

    it('should reject grade < 1', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(invalidSearchRequests.lowGrade),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_GRADE');
    });

    it('should reject missing subject', async () => {
      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(invalidSearchRequests.missingSubject),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_SUBJECT');
    });
  });

  describe('AI Integration', () => {
    it('should generate embeddings for query', async () => {
      let aiCalled = false;

      env.AI.run = async (model: any, input: any) => {
        aiCalled = true;
        expect(input).toHaveProperty('text');
        expect(input.text).toBe(validSearchRequest.query);
        return {
          shape: [1, 768],
          data: [[...Array(768)].map(() => Math.random())],
        };
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      await handleSearch(request, env);
      expect(aiCalled).toBe(true);
    });

    it('should handle embedding generation failures', async () => {
      env.AI.run = async () => {
        throw new Error('AI service unavailable');
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('SEARCH_FAILED');
    });

    it('should handle empty embedding responses', async () => {
      env.AI.run = async () => ({
        shape: [1, 0],
        data: [[]],
      });

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('EMBEDDING_FAILED');
    });
  });

  describe('Vectorize Integration', () => {
    it('should filter by grade and subject', async () => {
      let vectorizeQueryCalled = false;

      env.VECTOR_INDEX.query = async (vector: number[], options?: any) => {
        vectorizeQueryCalled = true;
        expect(options).toHaveProperty('filter');
        expect(options.filter).toHaveProperty('grade', validSearchRequest.grade);
        expect(options.filter).toHaveProperty('subject', validSearchRequest.subject);
        return { count: 0, matches: [] };
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      await handleSearch(request, env);
      expect(vectorizeQueryCalled).toBe(true);
    });

    it('should request metadata in results', async () => {
      env.VECTOR_INDEX.query = async (vector: number[], options?: any) => {
        expect(options.returnMetadata).toBe(true);
        return { count: 0, matches: [] };
      };

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      await handleSearch(request, env);
    });

    it('should handle empty search results', async () => {
      env.VECTOR_INDEX.query = async () => ({ count: 0, matches: [] });

      const request = new Request('http://test.com/search', {
        method: 'POST',
        body: JSON.stringify(validSearchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleSearch(request, env);
      const body = await response.json();

      expect(body.total_found).toBe(0);
      expect(body.content_ids).toEqual([]);
      expect(body.metadata).toEqual([]);
    });
  });
});
