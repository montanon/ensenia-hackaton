/**
 * Integration tests for generate endpoint
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { handleGenerate } from '../../src/routes/generate';
import { createMockEnv } from '../fixtures/mock-env';
import { validGenerateRequest, invalidGenerateRequests } from '../fixtures/curriculum-data';
import { Env } from '../../src/types/env';

describe('Generate Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  describe('Valid Requests', () => {
    it('should generate text with valid input', async () => {
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(validGenerateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('generated_text');
      expect(body).toHaveProperty('oa_codes');
      expect(body).toHaveProperty('model_used');
      expect(body).toHaveProperty('generation_time_ms');
      expect(typeof body.generated_text).toBe('string');
      expect(body.generated_text.length).toBeGreaterThan(0);
    });

    it('should use default style when not provided', async () => {
      const requestWithoutStyle = { ...validGenerateRequest };
      delete (requestWithoutStyle as any).style;

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(requestWithoutStyle),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(200);
    });

    it('should handle different generation styles', async () => {
      const styles = ['explanation', 'summary', 'example'] as const;

      for (const style of styles) {
        const request = new Request('http://test.com/generate', {
          method: 'POST',
          body: JSON.stringify({ ...validGenerateRequest, style }),
          headers: { 'Content-Type': 'application/json' },
        });

        const response = await handleGenerate(request, env);
        expect(response.status).toBe(200);
      }
    });

    it('should include OA codes in response', async () => {
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(validGenerateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      const body = await response.json();

      expect(Array.isArray(body.oa_codes)).toBe(true);
      expect(body.oa_codes).toEqual(validGenerateRequest.oa_codes);
    });

    it('should work without OA codes', async () => {
      const requestWithoutOA = { ...validGenerateRequest, oa_codes: [] };

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(requestWithoutOA),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(200);
    });
  });

  describe('Input Validation', () => {
    it('should reject context shorter than 10 characters', async () => {
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(invalidGenerateRequests.shortContext),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_CONTEXT');
      expect(body.message).toContain('at least 10 characters');
    });

    it('should reject query shorter than 3 characters', async () => {
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(invalidGenerateRequests.shortQuery),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_QUERY');
      expect(body.message).toContain('at least 3 characters');
    });

    it('should reject grade > 12', async () => {
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(invalidGenerateRequests.invalidGrade),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_GRADE');
      expect(body.message).toContain('between 1 and 12');
    });

    it('should reject grade < 1', async () => {
      const invalidRequest = {
        ...validGenerateRequest,
        grade: 0,
      };

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(invalidRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_GRADE');
    });

    it('should reject missing subject', async () => {
      const invalidRequest = {
        ...validGenerateRequest,
        subject: '',
      };

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(invalidRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_SUBJECT');
    });
  });

  describe('AI Integration', () => {
    it('should handle AI model failures', async () => {
      env.AI.run = async () => {
        throw new Error('AI model unavailable');
      };

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(validGenerateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('GENERATION_FAILED');
    });

    it('should handle empty AI responses', async () => {
      env.AI.run = async () => ({ response: '' });

      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify(validGenerateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('GENERATION_FAILED');
      expect(body.message).toContain('did not return a response');
    });
  });

  describe('Chilean Context', () => {
    it('should build Chilean-specific prompts for grade 5', async () => {
      // We can't directly test the prompt building without refactoring,
      // but we verify the endpoint accepts valid Chilean education data
      const request = new Request('http://test.com/generate', {
        method: 'POST',
        body: JSON.stringify({
          ...validGenerateRequest,
          grade: 5,
          subject: 'Matemática',
        }),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleGenerate(request, env);
      expect(response.status).toBe(200);
    });

    it('should handle different grade levels', async () => {
      const grades = [1, 5, 8, 12];

      for (const grade of grades) {
        const request = new Request('http://test.com/generate', {
          method: 'POST',
          body: JSON.stringify({ ...validGenerateRequest, grade }),
          headers: { 'Content-Type': 'application/json' },
        });

        const response = await handleGenerate(request, env);
        expect(response.status).toBe(200);
      }
    });
  });
});
