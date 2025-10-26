/**
 * Fetch endpoint - Retrieve curriculum content from D1 database
 */

import { Env } from '../types/env';
import {
  FetchRequest,
  FetchResponse,
  CurriculumContent,
  DbCurriculumContent,
} from '../types/schemas';
import { jsonResponse, errorResponse, parseJsonBody } from '../utils/responses';

/**
 * Handle content fetch requests
 *
 * Flow:
 * 1. Validate request
 * 2. Query D1 database for content by IDs
 * 3. Transform database records to API format
 * 4. Return content array
 */
export async function handleFetch(
  request: Request,
  env: Env
): Promise<Response> {
  const startTime = Date.now();

  try {
    // Parse and validate request
    const body = await parseJsonBody<FetchRequest>(request);
    console.log('[Worker] RAG Fetch requested for content IDs:', body.content_ids?.slice(0, 5).join(', ') + (body.content_ids?.length > 5 ? '...' : ''));

    if (!body.content_ids || body.content_ids.length === 0) {
      console.warn('[Worker] Fetch request with no content IDs');
      return errorResponse(
        400,
        'INVALID_REQUEST',
        'content_ids array is required and cannot be empty'
      );
    }

    // Limit to 50 IDs max per request
    const contentIds = body.content_ids.slice(0, 50);
    console.log('[Worker] Fetching', contentIds.length, 'content documents from database');

    // Build SQL query with placeholders
    const placeholders = contentIds.map(() => '?').join(',');
    const query = `
      SELECT
        id,
        title,
        grade,
        subject,
        content_text,
        learning_objectives,
        ministry_standard_ref,
        ministry_approved,
        keywords,
        difficulty_level
      FROM curriculum_content
      WHERE id IN (${placeholders})
      ORDER BY
        CASE id
          ${contentIds.map((_, i) => `WHEN ? THEN ${i}`).join(' ')}
        END
    `;

    // Execute query with parameters (once for WHERE IN, once for ORDER BY)
    const params = [...contentIds, ...contentIds];
    const dbStartTime = Date.now();
    const results = await env.DB.prepare(query).bind(...params).all();
    console.log('[Worker] Database query completed in', Date.now() - dbStartTime, 'ms');

    if (!results.success) {
      console.error('[Worker] Database query failed');
      return errorResponse(500, 'DB_QUERY_FAILED', 'Database query failed');
    }

    console.log('[Worker] Retrieved', results.results.length, 'documents from database');

    // Transform database records to API format
    const contents: CurriculumContent[] = results.results.map((row: any) => {
      const dbContent = row as DbCurriculumContent;
      return {
        id: dbContent.id,
        title: dbContent.title,
        grade: dbContent.grade,
        subject: dbContent.subject,
        content_text: dbContent.content_text,
        learning_objectives: JSON.parse(dbContent.learning_objectives || '[]'),
        ministry_standard_ref: dbContent.ministry_standard_ref,
        ministry_approved: dbContent.ministry_approved === 1,
        keywords: dbContent.keywords || '',
        difficulty_level: dbContent.difficulty_level || 'medium',
      };
    });

    console.log('[Worker] RAG context documents:');
    contents.forEach((c, i) => {
      console.log(`  ${i + 1}. "${c.title}" (Grade: ${c.grade}, Subject: ${c.subject}, Length: ${c.content_text.length} chars)`);
    });

    // Prepare response
    const response: FetchResponse = {
      contents,
      fetch_time_ms: Date.now() - startTime,
    };

    console.log('[Worker] Fetch completed in', Date.now() - startTime, 'ms');
    return jsonResponse(response);
  } catch (error: any) {
    console.error('[Worker] Fetch error:', error);
    return errorResponse(
      500,
      'FETCH_FAILED',
      error.message || 'Content fetch operation failed'
    );
  }
}
