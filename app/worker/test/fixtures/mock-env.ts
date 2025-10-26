/**
 * Mock environment for testing
 */

import { Env } from '../../src/types/env';

/**
 * Create a mock environment for testing
 */
export function createMockEnv(overrides?: Partial<Env>): Env {
  return {
    AI: {
      run: async (model: any, input: any) => {
        // Mock AI responses
        if (model.includes('embedding')) {
          return {
            shape: [1, 768],
            data: [[...Array(768)].map(() => Math.random())],
          };
        }
        if (model.includes('llama')) {
          return {
            response: 'Respuesta generada de prueba en español chileno.',
          };
        }
        throw new Error('Unknown AI model');
      },
    } as any,

    DB: {
      prepare: (query: string) => ({
        bind: (...params: any[]) => ({
          all: async () => ({ success: true, results: [] }),
          first: async () => null,
          run: async () => ({ success: true }),
        }),
        all: async () => ({ success: true, results: [] }),
        first: async () => null,
        run: async () => ({ success: true }),
      }),
    } as any,

    VECTOR_INDEX: {
      query: async (vector: number[], options?: any) => ({
        count: 0,
        matches: [],
      }),
      insert: async (vectors: any[]) => ({ ids: [], count: 0 }),
      upsert: async (vectors: any[]) => ({ ids: [], count: 0 }),
      getByIds: async (ids: string[]) => [],
      deleteByIds: async (ids: string[]) => ({ ids: [], count: 0 }),
    } as any,

    SEARCH_CACHE: {
      get: async (key: string) => null,
      put: async (key: string, value: string, options?: any) => undefined,
      delete: async (key: string) => undefined,
      list: async () => ({ keys: [], list_complete: true, cursor: '' }),
    } as any,

    ENVIRONMENT: 'test',
    EMBEDDING_MODEL: '@cf/baai/bge-base-en-v1.5' as any,
    GENERATION_MODEL: '@cf/meta/llama-3.1-8b-instruct' as any,
    VECTOR_DIMENSION: '768',
    CACHE_TTL_HOT: '3600',
    CACHE_TTL_WARM: '86400',
    CACHE_TTL_COLD: '604800',
    DEBUG: 'true',
    ADMIN_API_TOKEN: 'test-admin-token',
    ...overrides,
  };
}

/**
 * Create a mock execution context
 */
export function createMockContext(): ExecutionContext {
  return {
    waitUntil: (promise: Promise<any>) => {},
    passThroughOnException: () => {},
  };
}
