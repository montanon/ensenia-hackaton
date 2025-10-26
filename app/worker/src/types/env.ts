/**
 * Environment bindings for Cloudflare Worker
 * These are injected by Cloudflare Workers runtime based on wrangler.toml
 */

export interface Env {
  // Workers AI binding
  AI: Ai;

  // D1 Database binding
  DB: D1Database;

  // Vectorize binding
  VECTOR_INDEX: VectorizeIndex;

  // KV Cache binding
  SEARCH_CACHE: KVNamespace;

  // Environment variables
  ENVIRONMENT: string;
  EMBEDDING_MODEL: keyof AiModels;
  GENERATION_MODEL: keyof AiModels;
  VECTOR_DIMENSION: string;
  CACHE_TTL_HOT: string;
  CACHE_TTL_WARM: string;
  CACHE_TTL_COLD: string;
  DEBUG?: string;
  ADMIN_API_TOKEN?: string;
}

/**
 * Vectorize Index interface
 */
export interface VectorizeIndex {
  query(
    vector: number[],
    options?: VectorizeQueryOptions
  ): Promise<VectorizeMatches>;

  insert(vectors: VectorizeVector[]): Promise<VectorizeMutation>;

  upsert(vectors: VectorizeVector[]): Promise<VectorizeMutation>;

  getByIds(ids: string[]): Promise<VectorizeVector[]>;

  deleteByIds(ids: string[]): Promise<VectorizeMutation>;
}

export interface VectorizeQueryOptions {
  topK?: number;
  filter?: Record<string, any>;
  returnValues?: boolean;
  returnMetadata?: boolean;
}

export interface VectorizeMatches {
  count: number;
  matches: VectorizeMatch[];
}

export interface VectorizeMatch {
  id: string;
  score: number;
  values?: number[];
  metadata?: Record<string, any>;
}

export interface VectorizeVector {
  id: string;
  values: number[];
  metadata?: Record<string, any>;
}

export interface VectorizeMutation {
  ids: string[];
  count: number;
}

/**
 * Workers AI Response Types
 */
export interface AiEmbeddingResponse {
  shape: number[];
  data: number[][];
}

export interface AiTextGenerationResponse {
  response: string;
}
