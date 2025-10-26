/**
 * Tests for admin endpoint - Populate Vectorize
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { handlePopulateVectorize } from '../../src/routes/admin';
import { createMockEnv } from '../fixtures/mock-env';
import { Env, AiEmbeddingResponse, VectorizeMutation } from '../../src/types/env';

interface PopulateResultItem {
  id: string;
  title?: string;
  status: 'success' | 'error';
  message?: string;
}

interface PopulateResults {
  total: number;
  success: number;
  errors: number;
  items: PopulateResultItem[];
}

interface PopulateVectorizeResponse {
  message: string;
  results: PopulateResults;
  processing_time_ms: number;
  code?: string;
}

describe('Admin: Populate Vectorize', () => {
  let env: Env;
  const endpoint = 'http://test.com/admin/populate-vectorize';

  const makeAuthedRequest = () =>
    new Request(endpoint, {
      method: 'POST',
      headers: {
        'x-admin-token': env.ADMIN_API_TOKEN ?? 'test-admin-token',
      },
    });

  beforeEach(() => {
    env = createMockEnv();

    // Mock D1 to return sample curriculum content
    env.DB.prepare = (query: string) => ({
      all: async () => ({
        success: true,
        results: [
          {
            id: 'MAT-5-C001',
            title: 'Números hasta el millón',
            grade: 5,
            subject: 'Matemática',
            content_text: 'Los números naturales pueden ser muy grandes...',
            learning_objectives: '["MAT-5-OA01"]',
            ministry_standard_ref: 'Bases Curriculares 2012 - Matemática OA 01',
            keywords: 'números, millones, valor posicional',
          },
          {
            id: 'MAT-5-C002',
            title: 'Multiplicación: Cálculo Mental',
            grade: 5,
            subject: 'Matemática',
            content_text: 'El cálculo mental nos ayuda a resolver...',
            learning_objectives: '["MAT-5-OA02"]',
            ministry_standard_ref: 'Bases Curriculares 2012 - Matemática OA 02',
            keywords: 'multiplicación, cálculo mental, estrategias',
          },
        ],
      }),
    }) as any;

    // Mock AI embedding generation
    env.AI.run = async () => ({
      shape: [1, 768],
      data: [[...Array(768)].map(() => Math.random())],
    }) as any;

    // Mock Vectorize insert
    env.VECTOR_INDEX.insert = async (vectors) => {
      return {
        ids: vectors.map(v => v.id),
        count: vectors.length,
      } as VectorizeMutation;
    };
  });

  describe('Success Cases', () => {
    it('should fetch all curriculum content from D1', async () => {
      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      expect(response.status).toBe(200);

      const body = await response.json() as PopulateVectorizeResponse;
      expect(body.results.total).toBe(2);
    });

    it('should generate embeddings for each content item', async () => {
      let aiCallCount = 0;

      env.AI.run = (async (_model, input) => {
        aiCallCount++;
        expect(input).toHaveProperty('text');
        expect((input as { text: string }).text).toContain('Números hasta el millón');
        return { shape: [1, 768], data: [[...Array(768)].map(() => Math.random())] };
      }) as any;

      const request = makeAuthedRequest();

      await handlePopulateVectorize(request, env);
      expect(aiCallCount).toBe(2); // One for each content item
    });

    it('should insert vectors into Vectorize with correct metadata', async () => {
      const insertedVectors: any[] = [];

      env.VECTOR_INDEX.insert = async (vectors) => {
        insertedVectors.push(...vectors);
        return {
          ids: vectors.map(v => v.id),
          count: vectors.length,
        } as VectorizeMutation;
      };

      const request = makeAuthedRequest();

      await handlePopulateVectorize(request, env);

      // Should have inserted 2 vectors
      expect(insertedVectors.length).toBe(2);

      // Check first vector
      const firstVector = insertedVectors[0];
      expect(firstVector.id).toBe('MAT-5-C001');
      expect(firstVector.metadata.title).toBe('Números hasta el millón');
      expect(firstVector.metadata.grade).toBe(5);
      expect(firstVector.metadata.subject).toBe('Matemática');
      expect(firstVector.metadata.oa).toBe('MAT-5-OA01');
      expect(firstVector.metadata.keywords).toBe('números, millones, valor posicional');

      // Check vector values exist and have correct dimensions
      expect(Array.isArray(firstVector.values)).toBe(true);
      expect(firstVector.values.length).toBe(768);
    });

    it('should include searchable text in embedding', async () => {
      let embeddingTexts: string[] = [];

      env.AI.run = (async (_model, input) => {
        embeddingTexts.push((input as { text: string }).text);
        return { shape: [1, 768], data: [[...Array(768)].map(() => Math.random())] };
      }) as any;

      const request = makeAuthedRequest();

      await handlePopulateVectorize(request, env);

      // Should include title, content, and keywords
      expect(embeddingTexts[0]).toContain('Números hasta el millón');
      expect(embeddingTexts[0]).toContain('Los números naturales');
      expect(embeddingTexts[0]).toContain('Palabras clave:');
      expect(embeddingTexts[0]).toContain('números, millones');
    });

    it('should return success count', async () => {
      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      expect(body.results.success).toBe(2);
      expect(body.results.errors).toBe(0);
    });

    it('should include processing time', async () => {
      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      expect(body).toHaveProperty('processing_time_ms');
      expect(typeof body.processing_time_ms).toBe('number');
      expect(body.processing_time_ms).toBeGreaterThan(0);
    });

    it('should include item details in response', async () => {
      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      expect(Array.isArray(body.results.items)).toBe(true);
      expect(body.results.items.length).toBe(2);

      const firstItem = body.results.items[0];
      expect(firstItem.id).toBe('MAT-5-C001');
      expect(firstItem.title).toBe('Números hasta el millón');
      expect(firstItem.status).toBe('success');
    });
    it('should reject requests without admin token', async () => {
      const unauthenticatedRequest = new Request(endpoint, { method: 'POST' });
      const response = await handlePopulateVectorize(unauthenticatedRequest, env);
      expect(response.status).toBe(401);
    });
  });

  describe('Error Handling', () => {
    it('should handle database query failures', async () => {
      env.DB.prepare = (query: string) => ({
        all: async () => ({
          success: false,
          results: [],
        }),
      }) as any;

      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      expect(response.status).toBe(500);

      const body = await response.json() as PopulateVectorizeResponse;
      expect(body.code).toBe('DB_ERROR');
      expect(body.message).toContain('Failed to fetch curriculum content');
    });

    it('should handle empty database', async () => {
      env.DB.prepare = (query: string) => ({
        all: async () => ({
          success: true,
          results: [],
        }),
      }) as any;

      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      expect(response.status).toBe(400);

      const body = await response.json() as PopulateVectorizeResponse;
      expect(body.code).toBe('NO_DATA');
    });

    it('should handle AI embedding generation failures', async () => {
      env.AI.run = async () => {
        throw new Error('AI service unavailable');
      };

      const request = makeAuthedRequest();

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      // Should complete but with errors
      expect(body.results.errors).toBe(2);
      expect(body.results.success).toBe(0);
    });

    it('should handle empty embedding responses', async () => {
      env.AI.run = async () => ({
        shape: [1, 0],
        data: [[]],
      }) as any;

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      expect(body.results.errors).toBeGreaterThan(0);
    });

    it('should handle Vectorize insertion failures', async () => {
      env.VECTOR_INDEX.insert = async () => {
        throw new Error('Vectorize unavailable');
      };

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      expect(body.results.errors).toBe(2);
      expect(body.results.success).toBe(0);
    });

    it('should handle malformed learning objectives JSON', async () => {
      env.DB.prepare = (query: string) => ({
        all: async () => ({
          success: true,
          results: [
            {
              id: 'TEST-001',
              title: 'Test',
              grade: 5,
              subject: 'Test',
              content_text: 'Test content',
              learning_objectives: 'not-valid-json',
              ministry_standard_ref: 'Test',
              keywords: 'test',
            },
          ],
        }),
      }) as any;

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      const response = await handlePopulateVectorize(request, env);
      const body = await response.json() as PopulateVectorizeResponse;

      // Should still process but with empty OA code
      expect(body.results.success).toBe(1);

      const insertedVectors: any[] = [];
      env.VECTOR_INDEX.insert = async (vectors) => {
        insertedVectors.push(...vectors);
        return {
          ids: vectors.map(v => v.id),
          count: vectors.length,
        } as VectorizeMutation;
      };

      // Re-run to capture inserted vector
      await handlePopulateVectorize(request, env);
      expect(insertedVectors[0].metadata.oa).toBe('');
    });
  });

  describe('Data Validation', () => {
    it('should parse learning objectives correctly', async () => {
      const insertedVectors: any[] = [];

      env.VECTOR_INDEX.insert = async (vectors) => {
        insertedVectors.push(...vectors);
        return {
          ids: vectors.map(v => v.id),
          count: vectors.length,
        } as VectorizeMutation;
      };

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      await handlePopulateVectorize(request, env);

      // Check OA extraction
      expect(insertedVectors[0].metadata.oa).toBe('MAT-5-OA01');
      expect(insertedVectors[1].metadata.oa).toBe('MAT-5-OA02');
    });

    it('should use first learning objective as OA code', async () => {
      env.DB.prepare = (query: string) => ({
        all: async () => ({
          success: true,
          results: [
            {
              id: 'TEST-001',
              title: 'Test',
              grade: 5,
              subject: 'Test',
              content_text: 'Test',
              learning_objectives: '["OA-01", "OA-02", "OA-03"]',
              ministry_standard_ref: 'Test',
              keywords: 'test',
            },
          ],
        }),
      }) as any;

      const insertedVectors: any[] = [];
      env.VECTOR_INDEX.insert = async (vectors) => {
        insertedVectors.push(...vectors);
        return {
          ids: vectors.map(v => v.id),
          count: vectors.length,
        } as VectorizeMutation;
      };

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      await handlePopulateVectorize(request, env);

      // Should use first OA
      expect(insertedVectors[0].metadata.oa).toBe('OA-01');
    });
  });

  describe('Performance', () => {
    it('should add delay between items to avoid rate limiting', async () => {
      const startTime = Date.now();

      const request = new Request('http://test.com/admin/populate-vectorize', {
        method: 'POST',
      });

      await handlePopulateVectorize(request, env);

      const duration = Date.now() - startTime;

      // With 2 items and 100ms delay each, should take at least 100ms
      expect(duration).toBeGreaterThan(100);
    });
  });
});
