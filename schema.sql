-- ============================================================================
-- PostgreSQL Schema for Facebook JSON ETL
-- ============================================================================
-- This file contains the database schema required for the Lambda function.
-- Run these statements in your PostgreSQL database before deploying the Lambda.
-- ============================================================================

-- Drop tables if they exist (for clean setup)
-- WARNING: This will delete all existing data
-- DROP TABLE IF EXISTS comments CASCADE;
-- DROP TABLE IF EXISTS posts CASCADE;

-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
    post_id VARCHAR(255) PRIMARY KEY,
    timestamp TIMESTAMP,
    author VARCHAR(255),
    title TEXT,
    post_texts TEXT,
    text_length INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(255) PRIMARY KEY,
    post_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP,
    author VARCHAR(255),
    comment_texts TEXT,
    comment_priority integer,
    text_length INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post
        FOREIGN KEY (post_id)
        REFERENCES posts(post_id)
        ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_timestamp ON comments(timestamp);
CREATE INDEX IF NOT EXISTS idx_comments_author ON comments(author);

-- ============================================================================
-- Example UPSERT Queries (used by the Lambda function)
-- ============================================================================

-- Posts UPSERT (Insert or Update on conflict)
-- INSERT INTO posts (post_id, timestamp, title, post_texts, text_length)
-- VALUES ('post_001', '2024-11-18 09:42:13', 'Test Post', 'This is a test', 14)
-- ON CONFLICT (post_id)
-- DO UPDATE SET
--     timestamp = EXCLUDED.timestamp,
--     title = EXCLUDED.title,
--     post_texts = EXCLUDED.post_texts,
--     text_length = EXCLUDED.text_length,
--     updated_at = CURRENT_TIMESTAMP;

-- Comments UPSERT (Insert or Update on conflict)
-- INSERT INTO comments (comment_id, post_id, timestamp, author, comment_texts, text_length)
-- VALUES ('comment_001', 'post_001', '2024-11-18 10:05:47', 'John Doe', 'Great post!', 11)
-- ON CONFLICT (comment_id)
-- DO UPDATE SET
--     post_id = EXCLUDED.post_id,
--     timestamp = EXCLUDED.timestamp,
--     author = EXCLUDED.author,
--     comment_texts = EXCLUDED.comment_texts,
--     text_length = EXCLUDED.text_length,
--     updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check table structure
-- \d posts
-- \d comments

-- Count records
-- SELECT COUNT(*) FROM posts;
-- SELECT COUNT(*) FROM comments;

-- Sample data query
-- SELECT * FROM posts ORDER BY timestamp DESC LIMIT 10;
-- SELECT * FROM comments ORDER BY timestamp DESC LIMIT 10;

-- Check posts with their comment counts
-- SELECT p.post_id, p.title, COUNT(c.comment_id) as comment_count
-- FROM posts p
-- LEFT JOIN comments c ON p.post_id = c.post_id
-- GROUP BY p.post_id, p.title
-- ORDER BY comment_count DESC;

-- ============================================================================
-- Facebook Chunks Table for RAG
-- ============================================================================

-- Create facebook_chunks table
CREATE TABLE IF NOT EXISTS facebook_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    post_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP,
    full_chunk TEXT NOT NULL,
    engagement_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chunk_post
        FOREIGN KEY (post_id)
        REFERENCES posts(post_id)
        ON DELETE CASCADE
);

-- Create indexes for facebook_chunks table
CREATE INDEX IF NOT EXISTS idx_chunks_post_id ON facebook_chunks(post_id);
CREATE INDEX IF NOT EXISTS idx_chunks_timestamp ON facebook_chunks(timestamp);
CREATE INDEX IF NOT EXISTS idx_chunks_engagement_score ON facebook_chunks(engagement_score);
CREATE INDEX IF NOT EXISTS idx_chunks_created_at ON facebook_chunks(created_at);

-- ============================================================================
-- Verification Queries for facebook_chunks
-- ============================================================================

-- Check table structure
-- \d facebook_chunks

-- Count chunks
-- SELECT COUNT(*) FROM facebook_chunks;

-- Sample data query
-- SELECT chunk_id, post_id, timestamp, engagement_score,
--        LEFT(full_chunk, 100) as chunk_preview
-- FROM facebook_chunks
-- ORDER BY created_at DESC LIMIT 10;

-- Check chunks by engagement score
-- SELECT chunk_id, post_id, engagement_score,
--        LENGTH(full_chunk) as chunk_length
-- FROM facebook_chunks
-- ORDER BY engagement_score DESC
-- LIMIT 20;
