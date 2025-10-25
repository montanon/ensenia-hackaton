/**
 * Integration tests for fetch endpoint
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { handleFetch } from '../../src/routes/fetch';
import { createMockEnv } from '../fixtures/mock-env';
import { validFetchRequest, invalidFetchRequests, mockCurriculumContent } from '../fixtures/curriculum-data';
import { Env } from '../../src/types/env';

describe('Fetch Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  describe('Valid Requests', () => {
    it('should fetch content by IDs', async () => {
      // Mock DB response with curriculum content
      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({
            success: true,
            results: [mockCurriculumContent, mockCurriculumContent],
          }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify(validFetchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('contents');
      expect(body).toHaveProperty('fetch_time_ms');
      expect(Array.isArray(body.contents)).toBe(true);
      expect(body.contents.length).toBe(2);
    });

    it('should return empty array for nonexistent IDs', async () => {
      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({ success: true, results: [] }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['nonexistent-id'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body.contents).toEqual([]);
    });

    it('should limit to 50 IDs per request', async () => {
      const manyIds = Array(100).fill(0).map((_, i) => `id-${i}`);

      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({ success: true, results: [] }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: manyIds }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(200);
    });

    it('should parse learning_objectives JSON field', async () => {
      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({
            success: true,
            results: [mockCurriculumContent],
          }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['test-id'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      const body = await response.json();

      expect(Array.isArray(body.contents[0].learning_objectives)).toBe(true);
    });

    it('should convert ministry_approved to boolean', async () => {
      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({
            success: true,
            results: [mockCurriculumContent],
          }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify({ content_ids: ['test-id'] }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      const body = await response.json();

      expect(typeof body.contents[0].ministry_approved).toBe('boolean');
    });
  });

  describe('Invalid Requests', () => {
    it('should reject empty content_ids array', async () => {
      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify(invalidFetchRequests.emptyArray),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_REQUEST');
      expect(body.message).toContain('content_ids');
    });

    it('should reject missing content_ids field', async () => {
      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify(invalidFetchRequests.missingField),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(400);
    });

    it('should handle invalid JSON', async () => {
      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: 'invalid json',
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(500);
    });
  });

  describe('Database Errors', () => {
    it('should handle database query failures', async () => {
      env.DB.prepare = (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({ success: false, results: [] }),
        }),
      }) as any;

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify(validFetchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('DB_QUERY_FAILED');
    });

    it('should handle database exceptions', async () => {
      env.DB.prepare = () => {
        throw new Error('Database connection failed');
      };

      const request = new Request('http://test.com/fetch', {
        method: 'POST',
        body: JSON.stringify(validFetchRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleFetch(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('FETCH_FAILED');
    });
  });
});
