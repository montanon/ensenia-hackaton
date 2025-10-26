/**
 * Generate endpoint - Text generation using Workers AI
 */

import { Env, AiTextGenerationResponse } from '../types/env';
import { GenerateRequest, GenerateResponse } from '../types/schemas';
import { jsonResponse, errorResponse, parseJsonBody } from '../utils/responses';

/**
 * Handle text generation requests
 *
 * Flow:
 * 1. Validate request
 * 2. Build Chilean-context prompt
 * 3. Call Workers AI for text generation
 * 4. Return generated text with metadata
 */
export async function handleGenerate(
  request: Request,
  env: Env
): Promise<Response> {
  const startTime = Date.now();

  try {
    // Parse and validate request
    const body = await parseJsonBody<GenerateRequest>(request);
    console.log('[Worker] RAG Generation initiated:', {
      query: body.query,
      grade: body.grade,
      subject: body.subject,
      style: body.style || 'explanation',
      oa_codes: body.oa_codes || [],
      context_length: body.context?.length || 0,
    });

    if (!body.context || body.context.length < 10) {
      console.warn('[Worker] Invalid context - too short:', body.context?.length);
      return errorResponse(
        400,
        'INVALID_CONTEXT',
        'Context must be at least 10 characters'
      );
    }

    if (!body.query || body.query.length < 3) {
      console.warn('[Worker] Invalid query - too short:', body.query);
      return errorResponse(
        400,
        'INVALID_QUERY',
        'Query must be at least 3 characters'
      );
    }

    if (!body.grade || body.grade < 1 || body.grade > 12) {
      console.warn('[Worker] Invalid grade:', body.grade);
      return errorResponse(
        400,
        'INVALID_GRADE',
        'Grade must be between 1 and 12'
      );
    }

    if (!body.subject) {
      console.warn('[Worker] Missing subject');
      return errorResponse(400, 'INVALID_SUBJECT', 'Subject is required');
    }

    const style = body.style || 'explanation';
    const oaCodes = body.oa_codes || [];

    console.log('[Worker] RAG context received:');
    console.log('  - Context length:', body.context.length, 'characters');
    console.log('  - Student grade:', body.grade, '°');
    console.log('  - Subject:', body.subject);
    console.log('  - Style:', style);
    console.log('  - OA Codes:', oaCodes.join(', ') || 'None');

    // Build Chilean-context prompt
    console.log('[Worker] Building Chilean-context prompt with RAG context');
    const prompt = buildChileanPrompt(
      body.context,
      body.query,
      body.grade,
      body.subject,
      oaCodes,
      style
    );

    console.log('[Worker] Prompt constructed. Length:', prompt.length, 'characters');
    console.log('[Worker] Calling Workers AI with model:', env.GENERATION_MODEL);

    // Generate text using Workers AI
    const aiStartTime = Date.now();
    const aiResponse = (await env.AI.run(env.GENERATION_MODEL, {
      prompt,
      max_tokens: 500,
      temperature: 0.7,
    })) as AiTextGenerationResponse;

    const aiDuration = Date.now() - aiStartTime;
    console.log('[Worker] AI generation completed in', aiDuration, 'ms');

    if (!aiResponse.response) {
      console.error('[Worker] AI model returned empty response');
      return errorResponse(
        500,
        'GENERATION_FAILED',
        'AI model did not return a response'
      );
    }

    console.log('[Worker] Generated response length:', aiResponse.response.length, 'characters');
    console.log('[Worker] Generated text preview:', aiResponse.response.substring(0, 100) + '...');

    // Prepare response
    const response: GenerateResponse = {
      generated_text: aiResponse.response,
      oa_codes: oaCodes,
      model_used: env.GENERATION_MODEL,
      generation_time_ms: Date.now() - startTime,
    };

    console.log('[Worker] Generation completed in', Date.now() - startTime, 'ms');
    return jsonResponse(response);
  } catch (error: any) {
    console.error('[Worker] Generation error:', error);
    return errorResponse(
      500,
      'GENERATION_FAILED',
      error.message || 'Text generation failed'
    );
  }
}

/**
 * Build a Chilean education-context prompt
 */
function buildChileanPrompt(
  context: string,
  query: string,
  grade: number,
  subject: string,
  oaCodes: string[],
  style: string
): string {
  const gradeText = grade === 5 ? '5° Básico' : `${grade}° Básico`;
  const oaText = oaCodes.length > 0 ? `\n- Objetivos de Aprendizaje: ${oaCodes.join(', ')}` : '';

  let styleInstruction = '';
  switch (style) {
    case 'explanation':
      styleInstruction = 'Proporciona una explicación clara y detallada, apropiada para estudiantes.';
      break;
    case 'summary':
      styleInstruction = 'Proporciona un resumen conciso de los conceptos clave.';
      break;
    case 'example':
      styleInstruction = 'Proporciona ejemplos prácticos usando contexto chileno (pesos, nombres chilenos, lugares de Chile).';
      break;
    default:
      styleInstruction = 'Proporciona una respuesta educativa apropiada.';
  }

  return `Eres un asistente educativo para estudiantes chilenos. Responde en español chileno usando terminología del Ministerio de Educación de Chile.

**Contexto del Currículum:**
${context}

**Información del Estudiante:**
- Nivel: ${gradeText}
- Asignatura: ${subject}${oaText}

**Pregunta del Estudiante:**
${query}

**Instrucciones:**
${styleInstruction}

IMPORTANTE:
- Usa español chileno (no español de España ni México)
- Usa ejemplos con contexto chileno (pesos chilenos, nombres chilenos como María, José, Valentina, Matías)
- Usa terminología del Ministerio de Educación
- Mantén el nivel apropiado para ${gradeText}
- Sé claro y conciso

**Respuesta:**`;
}
