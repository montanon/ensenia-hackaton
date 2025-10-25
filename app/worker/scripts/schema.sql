-- Ensenia Database Schema for D1
-- Chilean Education Curriculum Content Management

-- ============================================================================
-- CURRICULUM CONTENT TABLE
-- Stores educational content aligned with Chilean Ministry standards
-- ============================================================================

CREATE TABLE IF NOT EXISTS curriculum_content (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 12),
  subject TEXT NOT NULL,
  content_text TEXT NOT NULL,
  learning_objectives TEXT NOT NULL, -- JSON array of OA IDs
  ministry_standard_ref TEXT NOT NULL,
  ministry_approved INTEGER DEFAULT 1,
  keywords TEXT,
  difficulty_level TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_curriculum_grade_subject
  ON curriculum_content(grade, subject);

CREATE INDEX IF NOT EXISTS idx_curriculum_ministry_ref
  ON curriculum_content(ministry_standard_ref);

CREATE INDEX IF NOT EXISTS idx_curriculum_created
  ON curriculum_content(created_at);

-- ============================================================================
-- MINISTRY STANDARDS TABLE
-- Stores official Chilean Ministry of Education learning objectives (OAs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ministry_standards (
  oa_id TEXT PRIMARY KEY,
  grade INTEGER NOT NULL,
  subject TEXT NOT NULL,
  oa_code TEXT NOT NULL,
  description TEXT NOT NULL,
  skills TEXT, -- JSON array of skills
  assessment_criteria TEXT,
  keywords TEXT,
  official_document_ref TEXT,
  effective_date TEXT DEFAULT '2024-01-01',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ministry_grade_subject
  ON ministry_standards(grade, subject);

CREATE INDEX IF NOT EXISTS idx_ministry_oa_code
  ON ministry_standards(oa_code);

-- ============================================================================
-- METADATA TABLE
-- Stores metadata about the database
-- ============================================================================

CREATE TABLE IF NOT EXISTS db_metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial metadata
INSERT OR REPLACE INTO db_metadata (key, value) VALUES
  ('schema_version', '1.0.0'),
  ('last_updated', CURRENT_TIMESTAMP),
  ('ministry_curriculum_version', '2024');
