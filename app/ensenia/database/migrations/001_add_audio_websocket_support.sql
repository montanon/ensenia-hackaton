-- Migration: Add audio and WebSocket support to sessions and messages
-- Created: 2025-10-25
-- Purpose: Enable real-time text/audio mode switching in chat sessions

-- Add WebSocket and audio mode fields to sessions table
ALTER TABLE sessions
    ADD COLUMN current_mode VARCHAR(10) NOT NULL DEFAULT 'text',
    ADD COLUMN ws_connection_id VARCHAR(100);

COMMENT ON COLUMN sessions.current_mode IS 'Current output mode preference: text or audio';
COMMENT ON COLUMN sessions.ws_connection_id IS 'WebSocket connection identifier for active connections';

-- Add audio support fields to messages table
ALTER TABLE messages
    ADD COLUMN output_mode VARCHAR(10) NOT NULL DEFAULT 'text',
    ADD COLUMN audio_id VARCHAR(100),
    ADD COLUMN audio_url VARCHAR(500),
    ADD COLUMN audio_available BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN audio_duration FLOAT;

-- Create index on audio_id for faster lookups
CREATE INDEX idx_messages_audio_id ON messages(audio_id) WHERE audio_id IS NOT NULL;

COMMENT ON COLUMN messages.output_mode IS 'How this message was delivered: text or audio';
COMMENT ON COLUMN messages.audio_id IS 'Reference to cached audio file (SHA-256 hash)';
COMMENT ON COLUMN messages.audio_url IS 'CDN or static URL for audio playback';
COMMENT ON COLUMN messages.audio_available IS 'Whether TTS audio has been generated';
COMMENT ON COLUMN messages.audio_duration IS 'Audio length in seconds';

-- Add constraints for valid mode values
ALTER TABLE sessions
    ADD CONSTRAINT check_current_mode CHECK (current_mode IN ('text', 'audio'));

ALTER TABLE messages
    ADD CONSTRAINT check_output_mode CHECK (output_mode IN ('text', 'audio'));

-- Ensure audio_available is false when audio_id is NULL
ALTER TABLE messages
    ADD CONSTRAINT check_audio_consistency CHECK (
        (audio_id IS NULL AND audio_available = false) OR
        (audio_id IS NOT NULL)
    );
