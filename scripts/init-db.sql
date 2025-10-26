-- Initialize databases for Ensenia
-- This script runs automatically when PostgreSQL container starts for the first time

-- Create development database
CREATE DATABASE ensenia OWNER postgres;

-- Create test database
CREATE DATABASE test OWNER postgres;

-- Create test user
CREATE USER test WITH PASSWORD 'test';
ALTER USER test CREATEDB;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ensenia TO postgres;
GRANT ALL PRIVILEGES ON DATABASE test TO test;
GRANT ALL PRIVILEGES ON DATABASE test TO postgres;

-- Connect to test database and grant schema privileges
\c test
GRANT ALL ON SCHEMA public TO test;
GRANT ALL ON SCHEMA public TO postgres;

-- Connect to ensenia database and grant schema privileges
\c ensenia
GRANT ALL ON SCHEMA public TO postgres;
