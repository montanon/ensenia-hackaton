/**
 * Request and Response schemas for API endpoints
 * These match the Python backend expectations
 */

// ============================================================================
// SEARCH ENDPOINT
// ============================================================================

export interface SearchRequest {
  query: string;
  grade: number;
  subject: string;
  limit?: number;
}

export interface SearchResponse {
  query: string;
  grade: number;
  subject: string;
  total_found: number;
  content_ids: string[];
  metadata: SearchResultMetadata[];
  cached: boolean;
  search_time_ms: number;
}

export interface SearchResultMetadata {
  id: string;
  score: number;
  title: string;
  oa: string;
}

// ============================================================================
// FETCH ENDPOINT
// ============================================================================

export interface FetchRequest {
  content_ids: string[];
}

export interface FetchResponse {
  contents: CurriculumContent[];
  fetch_time_ms: number;
}

export interface CurriculumContent {
  id: string;
  title: string;
  grade: number;
  subject: string;
  content_text: string;
  learning_objectives: string[];
  ministry_standard_ref: string;
  ministry_approved: boolean;
  keywords: string;
  difficulty_level: string;
}

// ============================================================================
// GENERATE ENDPOINT
// ============================================================================

export interface GenerateRequest {
  context: string;
  query: string;
  grade: number;
  subject: string;
  oa_codes: string[];
  style?: "explanation" | "summary" | "example";
}

export interface GenerateResponse {
  generated_text: string;
  oa_codes: string[];
  model_used: string;
  generation_time_ms: number;
}

// ============================================================================
// VALIDATE ENDPOINT
// ============================================================================

export interface ValidateRequest {
  content: string;
  grade: number;
  subject: string;
  expected_oa: string[];
}

export interface ValidateResponse {
  is_valid: boolean;
  score: number;
  validation_details: ValidationDetails;
  validation_time_ms: number;
}

export interface ValidationDetails {
  oa_alignment_score: number;
  grade_appropriate_score: number;
  chilean_terminology_score: number;
  learning_coverage_score: number;
  issues: string[];
  recommendations: string[];
}

// ============================================================================
// ERROR RESPONSE
// ============================================================================

export interface ErrorResponse {
  error: string;
  code: string;
  message: string;
  details?: any;
}

// ============================================================================
// DATABASE MODELS
// ============================================================================

export interface DbCurriculumContent {
  id: string;
  title: string;
  grade: number;
  subject: string;
  content_text: string;
  learning_objectives: string; // JSON string
  ministry_standard_ref: string;
  ministry_approved: number;
  keywords: string;
  difficulty_level: string;
  created_at: string;
  updated_at: string;
}

export interface DbMinistryStandard {
  oa_id: string;
  grade: number;
  subject: string;
  oa_code: string;
  description: string;
  skills: string; // JSON string
  assessment_criteria: string;
  keywords: string;
  official_document_ref: string;
  effective_date: string;
  created_at: string;
}
