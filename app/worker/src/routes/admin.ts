/**
 * Admin endpoint - Populate Vectorize Index
 * WARNING: This should be protected in production!
 */

import { Env, AiEmbeddingResponse } from '../types/env';
import { jsonResponse, errorResponse } from '../utils/responses';

interface CurriculumRow {
  id: string;
  title: string;
  grade: number;
  subject: string;
  content_text: string;
  learning_objectives: string;
  ministry_standard_ref: string;
  keywords: string;
}

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

/**
 * Populate Vectorize index with curriculum embeddings
 */
export async function handlePopulateVectorize(
  request: Request,
  env: Env
): Promise<Response> {
  const startTime = Date.now();

  try {
    if (!isAuthorized(request, env)) {
      return errorResponse(401, 'UNAUTHORIZED', 'Acceso no autorizado al endpoint admin');
    }

    // Step 1: Fetch all curriculum content
    const query = `
      SELECT
        id,
        title,
        grade,
        subject,
        content_text,
        learning_objectives,
        ministry_standard_ref,
        keywords
      FROM curriculum_content
      ORDER BY grade, subject, id
    `;

    const result = await env.DB.prepare(query).all();

    if (!result.success) {
      return errorResponse(500, 'DB_ERROR', 'Failed to fetch curriculum content');
    }

    const contents = result.results as unknown as CurriculumRow[];

    if (contents.length === 0) {
      return errorResponse(400, 'NO_DATA', 'No curriculum content found in database');
    }

    // Step 2: Process each content item
    const results: PopulateResults = {
      total: contents.length,
      success: 0,
      errors: 0,
      items: [],
    };

    for (const content of contents) {
      try {
        // Create searchable text
        const searchableText = `${content.title}\n\n${content.content_text}\n\nPalabras clave: ${content.keywords}`;

        // Generate embedding
        const embeddingResponse = (await env.AI.run(env.EMBEDDING_MODEL, {
          text: searchableText,
        })) as AiEmbeddingResponse;

        const embedding = embeddingResponse.data[0];

        if (!embedding || embedding.length === 0) {
          results.errors++;
          results.items.push({
            id: content.id,
            status: 'error',
            message: 'Failed to generate embedding',
          });
          continue;
        }

        // Parse learning objectives
        let learningObjectives: string[] = [];
        try {
          learningObjectives = JSON.parse(content.learning_objectives);
        } catch {
          learningObjectives = [];
        }

        // Extract OA code
        const oaCode = learningObjectives.length > 0 ? learningObjectives[0] : '';

        // Insert into Vectorize
        await env.VECTOR_INDEX.insert([
          {
            id: content.id,
            values: embedding,
            metadata: {
              title: content.title,
              grade: content.grade,
              subject: content.subject,
              oa: oaCode,
              ministry_ref: content.ministry_standard_ref,
              keywords: content.keywords,
            },
          },
        ]);

        results.success++;
        results.items.push({
          id: content.id,
          title: content.title,
          status: 'success',
        });

        // Small delay to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 100));
      } catch (error) {
        results.errors++;
        results.items.push({
          id: content.id,
          status: 'error',
          message: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    // Return results
    return jsonResponse({
      message: 'Vectorize population complete',
      results,
      processing_time_ms: Date.now() - startTime,
    });
  } catch (error) {
    console.error('Populate vectorize error:', error);
    return errorResponse(
      500,
      'POPULATE_FAILED',
      error instanceof Error ? error.message : 'Failed to populate Vectorize'
    );
  }
}

function isAuthorized(request: Request, env: Env): boolean {
  const token = env.ADMIN_API_TOKEN;
  if (!token) {
    return false;
  }

  const headerToken =
    request.headers.get('x-admin-token') ||
    request.headers.get('authorization') ||
    '';

  if (headerToken.startsWith('Bearer ')) {
    return headerToken.slice(7) === token;
  }

  return headerToken === token;
}
