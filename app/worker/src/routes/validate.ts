/**
 * Validate endpoint - Curriculum compliance validation
 */

import { Env, AiTextGenerationResponse } from '../types/env';
import {
  ValidateRequest,
  ValidateResponse,
  ValidationDetails,
} from '../types/schemas';
import { jsonResponse, errorResponse, parseJsonBody } from '../utils/responses';

/**
 * Handle curriculum validation requests
 *
 * Flow:
 * 1. Validate request
 * 2. Fetch ministry standards from D1
 * 3. Use AI to analyze curriculum alignment
 * 4. Calculate validation scores
 * 5. Return validation results
 */
export async function handleValidate(
  request: Request,
  env: Env
): Promise<Response> {
  const startTime = Date.now();

  try {
    // Parse and validate request
    const body = await parseJsonBody<ValidateRequest>(request);

    if (!body.content || body.content.length < 10) {
      return errorResponse(
        400,
        'INVALID_CONTENT',
        'Content must be at least 10 characters'
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

    const expectedOA = body.expected_oa || [];

    // Fetch ministry standards from D1 for the expected OAs
    let ministryStandards: any[] = [];
    if (expectedOA.length > 0) {
      const placeholders = expectedOA.map(() => '?').join(',');
      const query = `
        SELECT oa_code, description, keywords
        FROM ministry_standards
        WHERE oa_code IN (${placeholders})
          AND grade = ?
          AND subject = ?
      `;
      const params = [...expectedOA, body.grade, body.subject];
      const results = await env.DB.prepare(query).bind(...params).all();

      if (results.success) {
        ministryStandards = results.results;
      }
    }

    // Use AI to analyze curriculum alignment
    const validationPrompt = buildValidationPrompt(
      body.content,
      body.grade,
      body.subject,
      expectedOA,
      ministryStandards
    );

    const aiResponse = (await env.AI.run(env.GENERATION_MODEL, {
      prompt: validationPrompt,
      max_tokens: 300,
      temperature: 0.3,
    })) as AiTextGenerationResponse;

    // Parse AI response and calculate scores
    const validationDetails = parseValidationResponse(
      aiResponse.response,
      expectedOA
    );

    // Calculate overall score (weighted average)
    const overallScore =
      validationDetails.oa_alignment_score * 0.4 +
      validationDetails.grade_appropriate_score * 0.3 +
      validationDetails.chilean_terminology_score * 0.2 +
      validationDetails.learning_coverage_score * 0.1;

    // Validation passes if score >= 70/100
    const isValid = overallScore >= 70;

    // Prepare response
    const response: ValidateResponse = {
      is_valid: isValid,
      score: Math.round(overallScore),
      validation_details: validationDetails,
      validation_time_ms: Date.now() - startTime,
    };

    return jsonResponse(response);
  } catch (error: any) {
    console.error('Validation error:', error);
    return errorResponse(
      500,
      'VALIDATION_FAILED',
      error.message || 'Validation operation failed'
    );
  }
}

/**
 * Build validation prompt for AI analysis
 */
function buildValidationPrompt(
  content: string,
  grade: number,
  subject: string,
  expectedOA: string[],
  ministryStandards: any[]
): string {
  const gradeText = grade === 5 ? '5° Básico' : `${grade}° Básico`;
  const standardsText =
    ministryStandards.length > 0
      ? ministryStandards
          .map((s) => `- ${s.oa_code}: ${s.description}`)
          .join('\n')
      : 'No se especificaron OAs.';

  return `Eres un validador de currículum educativo chileno. Analiza el siguiente contenido y califica cada aspecto del 0 al 100.

**Contenido a Validar:**
${content}

**Requisitos:**
- Nivel: ${gradeText}
- Asignatura: ${subject}
- Objetivos de Aprendizaje esperados:
${standardsText}

**Criterios de Evaluación:**
Califica cada criterio del 0 al 100:

1. **Alineación con OAs (0-100)**: ¿El contenido cubre los Objetivos de Aprendizaje especificados?
2. **Apropiado para el nivel (0-100)**: ¿El contenido es apropiado para ${gradeText}?
3. **Terminología chilena (0-100)**: ¿Usa terminología y español chileno correcto?
4. **Cobertura de aprendizaje (0-100)**: ¿Cubre adecuadamente los conceptos necesarios?

**Formato de Respuesta:**
Responde EXACTAMENTE en este formato:
OA_SCORE: [número]
GRADE_SCORE: [número]
CHILEAN_SCORE: [número]
COVERAGE_SCORE: [número]
ISSUES: [lista separada por comas o "ninguno"]
RECOMMENDATIONS: [lista separada por comas o "ninguno"]

**Tu Evaluación:**`;
}

/**
 * Parse AI validation response into structured data
 */
function parseValidationResponse(
  aiResponse: string,
  expectedOA: string[]
): ValidationDetails {
  // Default scores (neutral)
  let oaScore = 50;
  let gradeScore = 50;
  let chileanScore = 50;
  let coverageScore = 50;
  const issues: string[] = [];
  const recommendations: string[] = [];

  try {
    // Parse scores from AI response
    const oaMatch = aiResponse.match(/OA_SCORE:\s*(\d+)/i);
    const gradeMatch = aiResponse.match(/GRADE_SCORE:\s*(\d+)/i);
    const chileanMatch = aiResponse.match(/CHILEAN_SCORE:\s*(\d+)/i);
    const coverageMatch = aiResponse.match(/COVERAGE_SCORE:\s*(\d+)/i);

    if (oaMatch) oaScore = Math.min(100, Math.max(0, parseInt(oaMatch[1])));
    if (gradeMatch) gradeScore = Math.min(100, Math.max(0, parseInt(gradeMatch[1])));
    if (chileanMatch) chileanScore = Math.min(100, Math.max(0, parseInt(chileanMatch[1])));
    if (coverageMatch) coverageScore = Math.min(100, Math.max(0, parseInt(coverageMatch[1])));

    // Parse issues
    const issuesMatch = aiResponse.match(/ISSUES:\s*(.+?)(?=\n[A-Z_]+:|$)/is);
    if (issuesMatch && issuesMatch[1].toLowerCase().trim() !== 'ninguno') {
      const issuesList = issuesMatch[1]
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      issues.push(...issuesList);
    }

    // Parse recommendations
    const recsMatch = aiResponse.match(/RECOMMENDATIONS:\s*(.+?)(?=\n[A-Z_]+:|$)/is);
    if (recsMatch && recsMatch[1].toLowerCase().trim() !== 'ninguno') {
      const recsList = recsMatch[1]
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      recommendations.push(...recsList);
    }
  } catch (error) {
    console.error('Error parsing validation response:', error);
    // Return default neutral scores if parsing fails
  }

  return {
    oa_alignment_score: oaScore,
    grade_appropriate_score: gradeScore,
    chilean_terminology_score: chileanScore,
    learning_coverage_score: coverageScore,
    issues: issues.length > 0 ? issues : ['No se identificaron problemas'],
    recommendations:
      recommendations.length > 0
        ? recommendations
        : ['El contenido cumple con los estándares'],
  };
}
