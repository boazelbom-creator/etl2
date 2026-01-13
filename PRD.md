# Product Requirements Document (PRD)
## Facebook Posts to RAG Chunks ETL Pipeline

**Version:** 1.0
**Date:** 2026-01-13
**Status:** Draft

---

## 1. Executive Summary

This document outlines the requirements for an AWS Lambda-based ETL pipeline that transforms social media posts and their associated comments from a PostgreSQL database into structured text chunks optimized for Retrieval Augmented Generation (RAG) systems.

## 2. Project Overview

### 2.1 Purpose
Process Facebook/social media posts and comments stored in PostgreSQL, creating concatenated text chunks that combine post metadata, content, and prioritized comments into a format suitable for RAG document retrieval systems.

### 2.2 Goals
- Automate the transformation of raw social media data into RAG-ready chunks
- Maintain traceability between source posts and generated chunks
- Optimize chunk content based on comment priority and engagement
- Support configurable chunk sizes for different RAG model requirements

---

## 3. Functional Requirements

### 3.1 Data Reading & Processing

#### FR-1: Sequential Post Processing
- **Description:** Read all posts from the `posts` table sequentially
- **Priority:** P0
- **Acceptance Criteria:**
  - All posts in the database are processed
  - Processing order is consistent and deterministic
  - No posts are skipped or duplicated

#### FR-2: Comment Retrieval
- **Description:** For each post, retrieve all related comments ordered by:
  1. `comment_priority` (ascending)
  2. `text_length` (ascending)
- **Priority:** P0
- **Acceptance Criteria:**
  - Comments are fetched with correct JOIN to posts
  - Ordering is applied correctly in SQL query
  - All comments for a post are retrieved

### 3.2 Chunk Generation

#### FR-3: Metadata Section
- **Description:** Generate metadata header for each chunk
- **Format:** `metadata: [Post_id: {post_id} | Timestamp: {timestamp} | Author: {author_prefix}]`
- **Priority:** P0
- **Acceptance Criteria:**
  - Author field is truncated to first 5 characters only
  - All metadata fields are present
  - Timestamp format is consistent

#### FR-4: Title Section
- **Description:** Include post title
- **Format:** `Title: {title}`
- **Priority:** P0

#### FR-5: Question Section
- **Description:** Include post content
- **Format:** `Question (priority 1): {post_texts}`
- **Priority:** P0

#### FR-6: Important Answer Section
- **Description:** Include only the FIRST comment for the post
- **Format:** `Important answer (priority 2): {comment_texts}`
- **Priority:** P0
- **Acceptance Criteria:**
  - Only the first comment (by priority and length ordering) is included
  - If no comments exist, this section should handle gracefully

#### FR-7: Other Comments Section
- **Description:** Concatenate all remaining comments (second, third, etc.)
- **Format:** `Other comments (priority 3): {comment_texts_concatenated}`
- **Priority:** P0
- **Acceptance Criteria:**
  - All comments except the first are included
  - Comments are concatenated in the correct order
  - If only one or zero comments exist, section handles gracefully

#### FR-8: Section Delimiters
- **Description:** Use standard RAG delimiters between sections and comments
- **Priority:** P0
- **Suggested Delimiter:** `\n\n---\n\n` or `\n\n###\n\n`
- **Acceptance Criteria:**
  - Consistent delimiter used throughout
  - Delimiter is compatible with common RAG frameworks

#### FR-9: Chunk Truncation
- **Description:** Truncate the concatenated string to `chunk_size` words (configured)
- **Priority:** P0
- **Acceptance Criteria:**
  - Truncation is word-based, not character-based
  - Configuration parameter controls the size
  - Truncation doesn't break mid-word

### 3.3 Data Insertion

#### FR-10: Chunk Table Insert
- **Description:** Insert each generated chunk into `facebook_chunks` table
- **Fields:**
  - `chunk_id`: Sequential unique identifier
  - `post_id`: Reference to source post
  - `timestamp`: Copy from post timestamp
  - `full_chunk`: The generated concatenated text
  - `engagement_score`: Total count of comments for the post
- **Priority:** P0
- **Acceptance Criteria:**
  - All fields populated correctly
  - chunk_id is unique and sequential
  - engagement_score accurately reflects comment count

#### FR-11: Batch Commits
- **Description:** Perform database commits every 1,000 inserts
- **Priority:** P0
- **Acceptance Criteria:**
  - Commits occur at 1,000 insert intervals
  - Final commit occurs for remaining records < 1,000
  - Transaction integrity is maintained

### 3.4 Schema Management

#### FR-12: Chunks Table Schema
- **Description:** Add `facebook_chunks` table definition to schema.sql
- **Priority:** P0
- **Required Fields:**
  - chunk_id (Primary Key, auto-incrementing or sequence-based)
  - post_id (Foreign Key to posts.post_id)
  - timestamp (TIMESTAMP)
  - full_chunk (TEXT)
  - engagement_score (INTEGER)
  - created_at (TIMESTAMP, default CURRENT_TIMESTAMP)

#### FR-13: Indexes
- **Description:** Create appropriate indexes for query performance
- **Priority:** P1
- **Suggested Indexes:**
  - Primary key on chunk_id
  - Index on post_id (for lookups)
  - Index on timestamp (for time-based queries)
  - Index on engagement_score (for ranking queries)

---

## 4. Non-Functional Requirements

### 4.1 Technology Stack

#### NFR-1: Programming Language
- **Requirement:** Python 3.12
- **Priority:** P0
- **Rationale:** AWS Lambda support, rich ecosystem for data processing, modern Python features

#### NFR-2: Virtual Environment
- **Requirement:** Use Python virtual environment for dependency management
- **Priority:** P0
- **Rationale:** Isolate dependencies, ensure reproducible builds

#### NFR-3: Cloud Platform
- **Requirement:** Deploy as AWS Lambda function
- **Priority:** P0

### 4.2 Configuration Management

#### NFR-4: Configuration File
- **Format:** JSON or YAML
- **Required Parameters:**
  - `postgres_url`: Database connection URL
  - `db_username`: Database username
  - `db_password`: Database password
  - `db_name`: Database name
  - `db_host`: Database host
  - `db_port`: Database port
  - `chunk_size`: Number of words per chunk (integer)
  - `admin_list`: List of administrator emails/IDs
  - `aws_region`: AWS region for deployment
- **Priority:** P0

### 4.3 Performance

#### NFR-5: Batch Processing
- **Requirement:** Process posts in batches to optimize memory usage
- **Priority:** P1

#### NFR-6: Lambda Timeout
- **Requirement:** Handle Lambda timeout limits appropriately
- **Priority:** P1
- **Consideration:** May need to process in chunks or use Step Functions for large datasets

### 4.4 Reliability

#### NFR-7: Error Handling
- **Requirement:** Implement comprehensive error handling
- **Priority:** P1
- **Coverage:**
  - Database connection failures
  - Query execution errors
  - Data validation errors
  - Transaction rollback on failures

#### NFR-8: Logging
- **Requirement:** Implement structured logging
- **Priority:** P1
- **Content:**
  - Processing progress (number of posts processed)
  - Error messages with context
  - Performance metrics
  - Transaction commit points

### 4.5 Maintainability

#### NFR-9: Code Structure
- **Requirement:** Modular, well-documented code
- **Priority:** P1
- **Standards:**
  - Follow PEP 8 style guide
  - Include docstrings for functions
  - Use type hints where applicable

---

## 5. Data Model

### 5.1 Source Tables

#### Posts Table
```sql
post_id VARCHAR(255) PRIMARY KEY
timestamp TIMESTAMP
author VARCHAR(255)
title TEXT
post_texts TEXT
text_length INTEGER
created_at TIMESTAMP
updated_at TIMESTAMP
```

#### Comments Table
```sql
comment_id VARCHAR(255) PRIMARY KEY
post_id VARCHAR(255) FOREIGN KEY
timestamp TIMESTAMP
author VARCHAR(255)
comment_texts TEXT
comment_priority INTEGER
text_length INTEGER
created_at TIMESTAMP
updated_at TIMESTAMP
```

### 5.2 Target Table

#### Facebook Chunks Table
```sql
chunk_id INTEGER/BIGINT PRIMARY KEY
post_id VARCHAR(255) FOREIGN KEY
timestamp TIMESTAMP
full_chunk TEXT
engagement_score INTEGER
created_at TIMESTAMP
```

---

## 6. Process Flow

### 6.1 High-Level Flow
1. Lambda function triggered (scheduled, manual, or event-based)
2. Load configuration
3. Establish PostgreSQL connection
4. Query all posts
5. For each post:
   - Retrieve ordered comments
   - Generate chunk string with all components
   - Truncate to chunk_size words
   - Insert into facebook_chunks table
   - Commit every 1,000 inserts
6. Final commit for remaining records
7. Close database connection
8. Return processing summary

### 6.2 Chunk Generation Algorithm
```
FOR each post IN posts:
    comments = SELECT comments WHERE post_id = post.post_id
               ORDER BY comment_priority, text_length

    chunk = concatenate(
        "metadata: [Post_id: " + post.post_id +
        " | Timestamp: " + post.timestamp +
        " | Author: " + post.author[:5] + "]",
        DELIMITER,
        "Title: " + post.title,
        DELIMITER,
        "Question (priority 1): " + post.post_texts,
        DELIMITER,
        "Important answer (priority 2): " + comments[0].comment_texts IF comments.length > 0,
        DELIMITER,
        "Other comments (priority 3): " + concatenate(comments[1:].comment_texts, DELIMITER),
    )

    chunk = truncate_to_words(chunk, chunk_size)
    engagement_score = comments.length

    INSERT INTO facebook_chunks (chunk_id, post_id, timestamp, full_chunk, engagement_score)

    IF insert_count % 1000 == 0:
        COMMIT
END FOR

COMMIT  -- final commit
```

---

## 7. Success Criteria

### 7.1 Functional Success
- All posts from source database are processed
- Each post generates exactly one chunk
- Chunks contain all required components in correct format
- Data integrity maintained (post_id references, engagement scores)

### 7.2 Performance Success
- Processing completes within Lambda timeout limits
- Memory usage stays within Lambda allocation
- Database commits occur at specified intervals

### 7.3 Quality Success
- Zero data loss during processing
- Chunks are properly formatted and readable
- All truncations occur at word boundaries

---

## 8. Out of Scope

### 8.1 Current Phase Exclusions
- Real-time processing (batch only)
- Incremental updates (full reprocessing each run)
- Multi-language support or translation
- Sentiment analysis or content classification
- Duplicate detection or deduplication
- RAG model integration or vector embeddings
- User authentication or authorization
- Web UI or API endpoints
- Monitoring dashboard

### 8.2 Future Considerations
- Incremental processing (only new posts)
- Change data capture (CDC) for real-time updates
- Multi-region deployment
- Data archival strategies
- A/B testing different chunk formats

---

## 9. Dependencies

### 9.1 Infrastructure
- AWS Lambda service
- PostgreSQL database (existing, populated)
- AWS CloudWatch (logging)

### 9.2 Python Libraries
- `psycopg2-binary` (PostgreSQL adapter)
  - **CRITICAL**: Must use `psycopg2-binary`, NOT `psycopg2`
  - The regular `psycopg2` package has C extensions that fail on AWS Lambda
  - `psycopg2-binary` is a pre-compiled standalone binary that works on Lambda without compilation
- `boto3` (AWS SDK, if using Secrets Manager)
- Standard library: `json`, `logging`, `os`

---

## 10. Security Considerations

### 10.1 Data Access
- Lambda execution role with minimal required permissions
- VPC configuration for database access (if required)

### 10.2 Data Privacy
- No PII exposure in logs
- Secure handling of author information
- Admin list access control

---

## 11. Testing Requirements

### 11.1 Unit Tests
- Chunk generation logic
- Text truncation to word boundaries
- Metadata formatting
- Comment ordering and selection

### 11.2 Integration Tests
- Database connection and queries
- Full ETL pipeline with test data
- Batch commit functionality
- Error handling and rollback

### 11.3 Test Data
- Posts with varying numbers of comments (0, 1, many)
- Comments with different priorities and lengths
- Edge cases (null values, empty strings, very long texts)

---

## 12. Deployment

### 12.1 Deployment Package
- Lambda deployment package (.zip) with dependencies
- Configuration file template
- schema.sql updates for DBA
- requirements.txt file with `psycopg2-binary` specified

### 12.2 Deployment Steps
1. Update PostgreSQL schema (add author to posts, create facebook_chunks table)
2. Create/update configuration file
3. Create requirements.txt with `psycopg2-binary` (NOT `psycopg2`)
4. Package Lambda function with dependencies using `pip install -r requirements.txt -t package/`
5. Deploy to AWS Lambda
6. Configure Lambda execution role and permissions
7. Set up CloudWatch logging
8. Configure trigger (if scheduled)

### 12.3 Critical Deployment Notes
- **Python Version**: Use Python 3.12 runtime for Lambda
- **PostgreSQL Library**: Always use `psycopg2-binary` in requirements.txt
- The regular `psycopg2` package will fail on Lambda due to C extension compilation issues
- Use deployment script similar to etl1 project for consistent packaging

---

## 13. Monitoring & Observability

### 13.1 Metrics
- Number of posts processed
- Number of chunks created
- Processing duration
- Database query performance
- Error count and types

### 13.2 Alerts
- Lambda execution failures
- Database connection failures
- Processing time exceeding threshold

---

## 14. Documentation Deliverables

1. This PRD document
2. schema.sql with all table definitions
3. README with setup instructions
4. Configuration file template with examples
5. Code documentation (inline and docstrings)

---

## 15. Timeline & Milestones

**Note:** Implementation timeline to be determined based on resource availability.

### Suggested Milestones:
1. Schema updates and database preparation
2. Core ETL logic implementation
3. Configuration and AWS integration
4. Testing and validation
5. Deployment and verification

---

## 16. Assumptions

1. Posts and comments tables are already populated with data
2. Database is accessible from AWS Lambda environment
3. PostgreSQL version is compatible with psycopg2-binary
4. Comment priority values are standardized (lower = higher priority)
5. AWS account has necessary permissions for Lambda deployment
6. chunk_size configuration is reasonable (e.g., 100-500 words)
7. Deployment follows best practices from etl1 project (using psycopg2-binary)
8. Python 3.12 runtime is available and configured for AWS Lambda

---

## 17. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Lambda timeout on large datasets | High | Medium | Implement pagination or Step Functions |
| Database connection limits | Medium | Low | Use connection pooling, batch processing |
| Memory limits exceeded | High | Low | Process in smaller batches, optimize queries |
| Malformed data causing errors | Medium | Medium | Robust error handling, data validation |
| Configuration errors | Medium | Medium | Schema validation, clear documentation |

---

## 18. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Technical Lead | | | |
| DBA | | | |

---

**Document History:**
- v1.0 (2026-01-13): Initial PRD creation
