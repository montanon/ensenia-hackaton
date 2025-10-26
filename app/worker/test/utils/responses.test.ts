/**
 * Unit tests for response utility functions
 */

import { describe, it, expect } from 'vitest';
import {
  jsonResponse,
  errorResponse,
  corsPreflightResponse,
  parseJsonBody,
} from '../../src/utils/responses';

describe('Response Utilities', () => {
  describe('jsonResponse', () => {
    it('should create a JSON response with default status 200', async () => {
      const data = { message: 'test' };
      const response = jsonResponse(data);

      expect(response.status).toBe(200);
      expect(response.headers.get('Content-Type')).toBe('application/json');
      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');

      const body = await response.json();
      expect(body).toEqual(data);
    });

    it('should create a JSON response with custom status', async () => {
      const data = { message: 'created' };
      const response = jsonResponse(data, 201);

      expect(response.status).toBe(201);
      const body = await response.json();
      expect(body).toEqual(data);
    });

    it('should include CORS headers', () => {
      const response = jsonResponse({ test: true });

      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toContain('POST');
      expect(response.headers.get('Access-Control-Allow-Headers')).toContain('Content-Type');
    });
  });

  describe('errorResponse', () => {
    it('should create an error response with required fields', async () => {
      const response = errorResponse(400, 'TEST_ERROR', 'Test error message');

      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body).toMatchObject({
        error: 'Error',
        code: 'TEST_ERROR',
        message: 'Test error message',
      });
    });

    it('should include optional details', async () => {
      const details = { field: 'query', value: 'invalid' };
      const response = errorResponse(400, 'VALIDATION_ERROR', 'Validation failed', details);

      const body = await response.json();
      expect(body.details).toEqual(details);
    });

    it('should omit details if not provided', async () => {
      const response = errorResponse(404, 'NOT_FOUND', 'Resource not found');

      const body = await response.json();
      expect(body).not.toHaveProperty('details');
    });
  });

  describe('corsPreflightResponse', () => {
    it('should return 204 No Content', () => {
      const response = corsPreflightResponse();
      expect(response.status).toBe(204);
    });

    it('should include all CORS headers', () => {
      const response = corsPreflightResponse();

      expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(response.headers.get('Access-Control-Allow-Methods')).toBe('GET, POST, OPTIONS');
      expect(response.headers.get('Access-Control-Allow-Headers')).toBe('Content-Type');
      expect(response.headers.get('Access-Control-Max-Age')).toBe('86400');
    });
  });

  describe('parseJsonBody', () => {
    it('should parse valid JSON body', async () => {
      const data = { test: 'value' };
      const request = new Request('http://test.com', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' },
      });

      const parsed = await parseJsonBody(request);
      expect(parsed).toEqual(data);
    });

    it('should throw error for invalid JSON', async () => {
      const request = new Request('http://test.com', {
        method: 'POST',
        body: 'invalid json',
        headers: { 'Content-Type': 'application/json' },
      });

      await expect(parseJsonBody(request)).rejects.toThrow('Invalid JSON body');
    });

    it('should throw error for empty body', async () => {
      const request = new Request('http://test.com', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      await expect(parseJsonBody(request)).rejects.toThrow();
    });
  });
});
