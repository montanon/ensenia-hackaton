-- Migration: Create curriculum and ministry standards tables
-- Created: 2025-10-25
-- Purpose: Enable RAG with Chilean Ministry of Education content

-- Create ministry_standards table
CREATE TABLE ministry_standards (
    oa_id VARCHAR(50) PRIMARY KEY,
    grade INTEGER NOT NULL,
    subject VARCHAR(255) NOT NULL,
    oa_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    skills JSONB NOT NULL,
    keywords TEXT NOT NULL,
    official_document_ref VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for ministry_standards
CREATE INDEX idx_ministry_grade_subject ON ministry_standards(grade, subject);
CREATE INDEX idx_ministry_oa_code ON ministry_standards(oa_code);

COMMENT ON TABLE ministry_standards IS 'Chilean Ministry of Education learning objectives (OAs)';
COMMENT ON COLUMN ministry_standards.oa_id IS 'Unique identifier for learning objective (e.g., MAT-5-OA01)';
COMMENT ON COLUMN ministry_standards.grade IS 'Grade level (1-12)';
COMMENT ON COLUMN ministry_standards.subject IS 'Subject name (e.g., Matemática, Lenguaje)';
COMMENT ON COLUMN ministry_standards.oa_code IS 'Official OA code (e.g., OA 01)';
COMMENT ON COLUMN ministry_standards.description IS 'Learning objective description';
COMMENT ON COLUMN ministry_standards.skills IS 'Array of skills covered';
COMMENT ON COLUMN ministry_standards.keywords IS 'Search keywords for content matching';
COMMENT ON COLUMN ministry_standards.official_document_ref IS 'Reference to official ministry document';

-- Create curriculum_content table
CREATE TABLE curriculum_content (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    grade INTEGER NOT NULL,
    subject VARCHAR(255) NOT NULL,
    content_text TEXT NOT NULL,
    learning_objectives JSONB NOT NULL,
    ministry_standard_ref VARCHAR(255) NOT NULL,
    ministry_approved INTEGER NOT NULL DEFAULT 0,
    keywords TEXT NOT NULL,
    difficulty_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    chunk_index INTEGER DEFAULT 0,
    source_file VARCHAR(500),
    embedding_generated BOOLEAN NOT NULL DEFAULT false
);

-- Create indexes for curriculum_content
CREATE INDEX idx_curriculum_grade_subject ON curriculum_content(grade, subject);
CREATE INDEX idx_curriculum_difficulty ON curriculum_content(difficulty_level);
CREATE INDEX idx_curriculum_embedding ON curriculum_content(embedding_generated);
CREATE INDEX idx_curriculum_keywords ON curriculum_content USING gin(to_tsvector('spanish', keywords));

COMMENT ON TABLE curriculum_content IS 'Educational content chunks aligned with ministry standards';
COMMENT ON COLUMN curriculum_content.id IS 'Unique identifier for content chunk';
COMMENT ON COLUMN curriculum_content.title IS 'Content title';
COMMENT ON COLUMN curriculum_content.grade IS 'Grade level (1-12)';
COMMENT ON COLUMN curriculum_content.subject IS 'Subject name';
COMMENT ON COLUMN curriculum_content.content_text IS 'Educational content text';
COMMENT ON COLUMN curriculum_content.learning_objectives IS 'Array of OA IDs this content addresses';
COMMENT ON COLUMN curriculum_content.ministry_standard_ref IS 'Reference to ministry standard document';
COMMENT ON COLUMN curriculum_content.ministry_approved IS '0=pending, 1=approved by ministry standards';
COMMENT ON COLUMN curriculum_content.keywords IS 'Search keywords';
COMMENT ON COLUMN curriculum_content.difficulty_level IS 'Content difficulty: easy, medium, hard';
COMMENT ON COLUMN curriculum_content.chunk_index IS 'Index of chunk if split from larger document';
COMMENT ON COLUMN curriculum_content.source_file IS 'Source PDF or document file path';
COMMENT ON COLUMN curriculum_content.embedding_generated IS 'Whether vector embedding has been generated';
