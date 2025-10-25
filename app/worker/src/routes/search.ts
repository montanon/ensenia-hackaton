/**
 * Search endpoint - Semantic search using Vectorize and Workers AI
 */

import { Env, AiEmbeddingResponse } from '../types/env';
import {
  SearchRequest,
  SearchResponse,
  SearchResultMetadata,
} from '../types/schemas';
import { jsonResponse, errorResponse, parseJsonBody } from '../utils/responses';

/**
 * Handle semantic search requests
 *
 * Flow:
 * 1. Validate request
 * 2. Check cache
 * 3. Generate embedding for query
 * 4. Search Vectorize index
 * 5. Format and return results
 * 6. Cache results
 */
export async function handleSearch(
  request: Request,
  env: Env
): Promise<Response> {
  const startTime = Date.now();

  try {
    // Parse and validate request
    const body = await parseJsonBody<SearchRequest>(request);

    if (!body.query || body.query.length < 3) {
      return errorResponse(
        400,
        'INVALID_QUERY',
        'Query must be at least 3 characters'
      );
    }

    if (!body.grade || body.grade < 1 || body.grade > 12) {
      return errorResponse(
        400,
        'INVALID_GRADE',
        'Grade must be between 1 and 12'
      );
    }

    if (!body.subject) {
      return errorResponse(400, 'INVALID_SUBJECT', 'Subject is required');
    }

    const limit = Math.min(body.limit || 10, 50);

    // Check cache (hot cache - 1 hour TTL)
    const cacheKey = `search:${body.query}:${body.grade}:${body.subject}:${limit}`;
    const cached = await env.SEARCH_CACHE.get(cacheKey);

    if (cached) {
      const cachedData = JSON.parse(cached);
      return jsonResponse({
        ...cachedData,
        cached: true,
      });
    }

    // Generate embedding for the query using Workers AI
    const embeddingResponse = (await env.AI.run(env.EMBEDDING_MODEL, {
      text: body.query,
    })) as AiEmbeddingResponse;

    const queryVector = embeddingResponse.data[0];

    if (!queryVector || queryVector.length === 0) {
      return errorResponse(
        500,
        'EMBEDDING_FAILED',
        'Failed to generate query embedding'
      );
    }

    // Search Vectorize index with metadata filtering
    const vectorResults = await env.VECTOR_INDEX.query(queryVector, {
      topK: limit,
      filter: {
        grade: body.grade,
        subject: body.subject,
      },
      returnMetadata: true,
    });

    // Format response metadata
    const metadata: SearchResultMetadata[] = vectorResults.matches.map(
      (match) => ({
        id: match.id,
        score: match.score,
        title: (match.metadata?.title as string) || '',
        oa: (match.metadata?.oa as string) || '',
      })
    );

    // Prepare response
    const response: SearchResponse = {
      query: body.query,
      grade: body.grade,
      subject: body.subject,
      total_found: vectorResults.count,
      content_ids: vectorResults.matches.map((m) => m.id),
      metadata,
      cached: false,
      search_time_ms: Date.now() - startTime,
    };

    // Cache results (1 hour TTL for hot cache)
    const cacheTTL = parseInt(env.CACHE_TTL_HOT) || 3600;
    await env.SEARCH_CACHE.put(cacheKey, JSON.stringify(response), {
      expirationTtl: cacheTTL,
    });

    return jsonResponse(response);
  } catch (error: any) {
    console.error('Search error:', error);
    return errorResponse(
      500,
      'SEARCH_FAILED',
      error.message || 'Search operation failed'
    );
  }
}
