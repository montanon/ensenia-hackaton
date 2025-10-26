/**
 * Test fixtures for curriculum data
 */

export const mockCurriculumContent = {
  id: 'test-mat-5-001',
  title: 'Test: Fracciones Básicas',
  grade: 5,
  subject: 'Matemática',
  content_text: 'Contenido de prueba sobre fracciones para 5° Básico.',
  learning_objectives: '["oa-mat-5-03"]',
  ministry_standard_ref: 'OA-MAT-5-03',
  ministry_approved: 1,
  keywords: 'fracciones, test, prueba',
  difficulty_level: 'basic',
  created_at: '2024-01-01T00:00:00.000Z',
  updated_at: '2024-01-01T00:00:00.000Z',
};

export const mockMinistryStandard = {
  oa_id: 'test-oa-mat-5-03',
  grade: 5,
  subject: 'Matemática',
  oa_code: 'OA-MAT-5-03',
  description: 'Estándar de prueba para fracciones',
  skills: '["comprensión", "aplicación"]',
  assessment_criteria: 'Criterios de evaluación de prueba',
  keywords: 'fracciones, test',
  official_document_ref: 'Bases Curriculares Test',
  effective_date: '2024-01-01',
  created_at: '2024-01-01T00:00:00.000Z',
};

export const validSearchRequest = {
  query: '¿Qué son las fracciones?',
  grade: 5,
  subject: 'Matemática',
  limit: 10,
};

export const validFetchRequest = {
  content_ids: ['curr-mat-5-001', 'curr-mat-5-002'],
};

export const validGenerateRequest = {
  context: 'Las fracciones representan partes de un todo. El numerador indica cuántas partes.',
  query: '¿Cómo sumo fracciones con el mismo denominador?',
  grade: 5,
  subject: 'Matemática',
  oa_codes: ['OA-MAT-5-04'],
  style: 'explanation' as const,
};

export const validValidateRequest = {
  content: 'Las fracciones son números que representan partes de un entero. Por ejemplo, 1/2 significa una de dos partes iguales.',
  grade: 5,
  subject: 'Matemática',
  expected_oa: ['OA-MAT-5-03'],
};

// Invalid requests for testing error handling
export const invalidSearchRequests = {
  shortQuery: { query: 'ab', grade: 5, subject: 'Matemática' },
  invalidGrade: { query: 'test query', grade: 13, subject: 'Matemática' },
  lowGrade: { query: 'test query', grade: 0, subject: 'Matemática' },
  missingSubject: { query: 'test query', grade: 5, subject: '' },
};

export const invalidFetchRequests = {
  emptyArray: { content_ids: [] },
  missingField: {},
};

export const invalidGenerateRequests = {
  shortContext: { context: 'short', query: 'test query', grade: 5, subject: 'Matemática' },
  shortQuery: { context: 'Valid context here', query: 'ab', grade: 5, subject: 'Matemática' },
  invalidGrade: { context: 'Valid context here', query: 'test query', grade: 15, subject: 'Matemática' },
};

export const invalidValidateRequests = {
  shortContent: { content: 'short', grade: 5, subject: 'Matemática' },
  invalidGrade: { content: 'Valid content here', grade: 0, subject: 'Matemática' },
};
