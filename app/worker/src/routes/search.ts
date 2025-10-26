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
    let body: SearchRequest;
    try {
      body = await parseJsonBody<SearchRequest>(request);
    } catch (parseError) {
      console.error('[Worker] Failed to parse request body:', parseError);
      console.error('[Worker] Request content-type:', request.headers.get('content-type'));
      return errorResponse(
        400,
        'PARSE_ERROR',
        'Failed to parse request JSON body'
      );
    }

    // Validate required fields exist
    if (!body) {
      console.error('[Worker] Request body is null or undefined');
      return errorResponse(400, 'EMPTY_BODY', 'Request body is required');
    }

    console.log('[Worker] RAG Search initiated:', {
      query: body.query,
      grade: body.grade,
      subject: body.subject,
    });

    if (!body.query || typeof body.query !== 'string' || body.query.length < 3) {
      console.warn('[Worker] Invalid query - must be string with 3+ chars:', body.query);
      return errorResponse(
        400,
        'INVALID_QUERY',
        'Query must be at least 3 characters'
      );
    }

    if (!body.grade || typeof body.grade !== 'number' || body.grade < 1 || body.grade > 12) {
      console.warn('[Worker] Invalid grade:', body.grade, 'type:', typeof body.grade);
      return errorResponse(
        400,
        'INVALID_GRADE',
        'Grade must be a number between 1 and 12'
      );
    }

    if (!body.subject || typeof body.subject !== 'string') {
      console.warn('[Worker] Missing or invalid subject:', body.subject);
      return errorResponse(400, 'INVALID_SUBJECT', 'Subject is required and must be a string');
    }

    const limit = Math.min(body.limit || 10, 50);

    // Check cache (hot cache - 1 hour TTL)
    const cacheKey = `search:${body.query}:${body.grade}:${body.subject}:${limit}`;
    console.log('[Worker] Checking cache with key:', cacheKey);
    const cached = await env.SEARCH_CACHE.get(cacheKey);

    if (cached) {
      console.log('[Worker] Cache HIT for search');
      const cachedData = JSON.parse(cached);

      // Ensure cached data has required fields (for backwards compatibility)
      if (!cachedData.total_found) {
        console.warn('[Worker] Cached data missing total_found, regenerating...');
        // Fall through to regenerate if cache is invalid
      } else {
        return jsonResponse({
          ...cachedData,
          cached: true,
        });
      }
    }

    console.log('[Worker] Cache MISS - generating embedding for query:', body.query);

    // Generate embedding for the query using Workers AI
    const embeddingStartTime = Date.now();
    const embeddingResponse = (await env.AI.run(env.EMBEDDING_MODEL, {
      text: body.query,
    })) as AiEmbeddingResponse;

    console.log('[Worker] Embedding generated in', Date.now() - embeddingStartTime, 'ms');

    const queryVector = embeddingResponse.data[0];

    if (!queryVector || queryVector.length === 0) {
      console.error('[Worker] Failed to generate embedding');
      return errorResponse(
        500,
        'EMBEDDING_FAILED',
        'Failed to generate query embedding'
      );
    }

    console.log('[Worker] Query vector dimension:', queryVector.length);

    // Search Vectorize index with metadata filtering
    console.log('[Worker] Searching Vectorize index with filters:', {
      grade: body.grade,
      subject: body.subject,
      topK: limit,
    });

    const vectorSearchStartTime = Date.now();

    // Check if VECTOR_INDEX is available (it's not available in local dev mode without experimental flag)
    let vectorResults;
    if (!env.VECTOR_INDEX) {
      console.warn('[Worker] VECTOR_INDEX not available - using mock results for development');
      // In development mode, return mock results
      if (env.ENVIRONMENT === 'development') {
        vectorResults = {
          count: 2,
          matches: [
            {
              id: 'mock-1',
              score: 0.95,
              metadata: {
                title: `Contenido sobre ${body.query} - Grado ${body.grade}`,
                subject: body.subject,
                grade: body.grade,
                content: `Este es contenido de ejemplo sobre ${body.query} para desarrollo local. En producción, esto vendría de Vectorize.`,
              },
            },
            {
              id: 'mock-2',
              score: 0.87,
              metadata: {
                title: `Introducción a ${body.query}`,
                subject: body.subject,
                grade: body.grade,
                content: `Contenido educativo adicional sobre ${body.query} alineado con los estándares curriculares chilenos.`,
              },
            },
          ],
        };
        console.log('[Worker] Using mock search results for development mode');
      } else {
        return errorResponse(
          503,
          'VECTORIZE_UNAVAILABLE',
          'Vector search service is not available in this environment'
        );
      }
    } else {
      vectorResults = await env.VECTOR_INDEX.query(queryVector, {
        topK: limit,
        filter: {
          grade: body.grade,
          subject: body.subject,
        },
        returnMetadata: true,
      });
    }

    console.log('[Worker] Vectorize search completed in', Date.now() - vectorSearchStartTime, 'ms');
    console.log('[Worker] Found', vectorResults.matches.length, 'matching documents');

    // Format response metadata
    const metadata: SearchResultMetadata[] = vectorResults.matches.map(
      (match) => ({
        id: match.id,
        score: match.score,
        title: (match.metadata?.title as string) || '',
        oa: (match.metadata?.oa as string) || '',
      })
    );

    console.log('[Worker] Search results metadata:');
    metadata.forEach((m) => {
      console.log(`  - ${m.title} (Score: ${m.score.toFixed(4)}, OA: ${m.oa})`);
    });

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
    console.log('[Worker] Caching search results with TTL:', cacheTTL);
    await env.SEARCH_CACHE.put(cacheKey, JSON.stringify(response), {
      expirationTtl: cacheTTL,
    });

    console.log('[Worker] Search completed in', Date.now() - startTime, 'ms');
    return jsonResponse(response);
  } catch (error: any) {
    console.error('[Worker] Search error:', error);
    return errorResponse(
      500,
      'SEARCH_FAILED',
      error.message || 'Search operation failed'
    );
  }
}
