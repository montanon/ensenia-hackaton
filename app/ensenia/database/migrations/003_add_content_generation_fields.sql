-- Migration: Add content generation fields to sessions table
-- Description: Adds learning_content and study_guide JSON fields to support
--              structured content generation from research context

BEGIN;

-- Add new JSON columns to sessions table
ALTER TABLE sessions
ADD COLUMN learning_content JSON DEFAULT NULL,
ADD COLUMN study_guide JSON DEFAULT NULL;

-- Create indexes for potential queries
CREATE INDEX idx_sessions_learning_content_exists
  ON sessions USING btree ((learning_content IS NOT NULL));

CREATE INDEX idx_sessions_study_guide_exists
  ON sessions USING btree ((study_guide IS NOT NULL));

COMMIT;
