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

    if (!body.context || body.context.length < 10) {
      return errorResponse(
        400,
        'INVALID_CONTEXT',
        'Context must be at least 10 characters'
      );
    }

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

    const style = body.style || 'explanation';
    const oaCodes = body.oa_codes || [];

    // Build Chilean-context prompt
    const prompt = buildChileanPrompt(
      body.context,
      body.query,
      body.grade,
      body.subject,
      oaCodes,
      style
    );

    // Generate text using Workers AI
    const aiResponse = (await env.AI.run(env.GENERATION_MODEL, {
      prompt,
      max_tokens: 500,
      temperature: 0.7,
    })) as AiTextGenerationResponse;

    if (!aiResponse.response) {
      return errorResponse(
        500,
        'GENERATION_FAILED',
        'AI model did not return a response'
      );
    }

    // Prepare response
    const response: GenerateResponse = {
      generated_text: aiResponse.response,
      oa_codes: oaCodes,
      model_used: env.GENERATION_MODEL,
      generation_time_ms: Date.now() - startTime,
    };

    return jsonResponse(response);
  } catch (error: any) {
    console.error('Generation error:', error);
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
