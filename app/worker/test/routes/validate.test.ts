/**
 * Integration tests for validate endpoint
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { handleValidate } from '../../src/routes/validate';
import { createMockEnv } from '../fixtures/mock-env';
import { validValidateRequest, invalidValidateRequests, mockMinistryStandard } from '../fixtures/curriculum-data';
import { Env } from '../../src/types/env';

describe('Validate Endpoint', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();

    // Mock DB to return ministry standards
    env.DB.prepare = (query: string) => ({
      bind: (...params: any[]) => ({
        all: async () => ({
          success: true,
          results: [mockMinistryStandard],
        }),
      }),
    }) as any;

    // Mock AI to return structured validation response
    env.AI.run = async () => ({
      response: `OA_SCORE: 85
GRADE_SCORE: 90
CHILEAN_SCORE: 88
COVERAGE_SCORE: 80
ISSUES: ninguno
RECOMMENDATIONS: El contenido cumple con los estándares`,
    });
  });

  describe('Valid Requests', () => {
    it('should validate content successfully', async () => {
      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      expect(body).toHaveProperty('is_valid');
      expect(body).toHaveProperty('score');
      expect(body).toHaveProperty('validation_details');
      expect(body).toHaveProperty('validation_time_ms');
      expect(typeof body.is_valid).toBe('boolean');
      expect(typeof body.score).toBe('number');
    });

    it('should validate as true when score >= 70', async () => {
      env.AI.run = async () => ({
        response: `OA_SCORE: 80
GRADE_SCORE: 75
CHILEAN_SCORE: 70
COVERAGE_SCORE: 65
ISSUES: ninguno
RECOMMENDATIONS: Buen contenido`,
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      expect(body.is_valid).toBe(true);
      expect(body.score).toBeGreaterThanOrEqual(70);
    });

    it('should validate as false when score < 70', async () => {
      env.AI.run = async () => ({
        response: `OA_SCORE: 50
GRADE_SCORE: 60
CHILEAN_SCORE: 55
COVERAGE_SCORE: 40
ISSUES: Contenido incompleto, falta terminología chilena
RECOMMENDATIONS: Mejorar alineación con OAs`,
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      expect(body.is_valid).toBe(false);
      expect(body.score).toBeLessThan(70);
    });

    it('should include validation details', async () => {
      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      expect(body.validation_details).toHaveProperty('oa_alignment_score');
      expect(body.validation_details).toHaveProperty('grade_appropriate_score');
      expect(body.validation_details).toHaveProperty('chilean_terminology_score');
      expect(body.validation_details).toHaveProperty('learning_coverage_score');
      expect(body.validation_details).toHaveProperty('issues');
      expect(body.validation_details).toHaveProperty('recommendations');
    });

    it('should parse issues from AI response', async () => {
      env.AI.run = async () => ({
        response: `OA_SCORE: 60
GRADE_SCORE: 70
CHILEAN_SCORE: 50
COVERAGE_SCORE: 60
ISSUES: Falta terminología chilena, Contenido muy técnico para el nivel
RECOMMENDATIONS: Simplificar lenguaje, Añadir ejemplos locales`,
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      expect(Array.isArray(body.validation_details.issues)).toBe(true);
      expect(body.validation_details.issues.length).toBeGreaterThan(0);
    });

    it('should work without expected_oa', async () => {
      const requestWithoutOA = { ...validValidateRequest, expected_oa: [] };

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(requestWithoutOA),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(200);
    });
  });

  describe('Input Validation', () => {
    it('should reject content shorter than 10 characters', async () => {
      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(invalidValidateRequests.shortContent),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_CONTENT');
      expect(body.message).toContain('at least 10 characters');
    });

    it('should reject invalid grade', async () => {
      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(invalidValidateRequests.invalidGrade),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_GRADE');
    });

    it('should reject missing subject', async () => {
      const invalidRequest = { ...validValidateRequest, subject: '' };

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(invalidRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(400);

      const body = await response.json();
      expect(body.code).toBe('INVALID_SUBJECT');
    });
  });

  describe('Score Calculation', () => {
    it('should apply weighted scoring correctly', async () => {
      env.AI.run = async () => ({
        response: `OA_SCORE: 100
GRADE_SCORE: 100
CHILEAN_SCORE: 100
COVERAGE_SCORE: 100
ISSUES: ninguno
RECOMMENDATIONS: Excelente`,
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      // With all scores at 100, weighted average should be 100
      expect(body.score).toBe(100);
    });

    it('should handle malformed AI responses gracefully', async () => {
      env.AI.run = async () => ({
        response: 'Invalid response format without proper structure',
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(200);

      const body = await response.json();
      // Should use default neutral scores (50)
      expect(body.score).toBeDefined();
    });

    it('should clamp scores to 0-100 range', async () => {
      env.AI.run = async () => ({
        response: `OA_SCORE: 150
GRADE_SCORE: -10
CHILEAN_SCORE: 200
COVERAGE_SCORE: -50
ISSUES: ninguno
RECOMMENDATIONS: ninguno`,
      });

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      const body = await response.json();

      expect(body.validation_details.oa_alignment_score).toBeLessThanOrEqual(100);
      expect(body.validation_details.oa_alignment_score).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Database Integration', () => {
    it('should query ministry standards when OAs provided', async () => {
      let queryCalled = false;

      env.DB.prepare = (query: string) => {
        if (query.includes('ministry_standards')) {
          queryCalled = true;
        }
        return {
          bind: (...params: any[]) => ({
            all: async () => ({
              success: true,
              results: [mockMinistryStandard],
            }),
          }),
        } as any;
      };

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      await handleValidate(request, env);
      expect(queryCalled).toBe(true);
    });

    it('should handle database failures gracefully', async () => {
      env.DB.prepare = () => {
        throw new Error('Database error');
      };

      const request = new Request('http://test.com/validate', {
        method: 'POST',
        body: JSON.stringify(validValidateRequest),
        headers: { 'Content-Type': 'application/json' },
      });

      const response = await handleValidate(request, env);
      expect(response.status).toBe(500);

      const body = await response.json();
      expect(body.code).toBe('VALIDATION_FAILED');
    });
  });
});
