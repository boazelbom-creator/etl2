# Facebook Posts to RAG Chunks ETL Lambda Function

AWS Lambda function that transforms Facebook posts and comments from PostgreSQL into RAG-ready text chunks for retrieval augmented generation systems.

## Features

- **Sequential Post Processing**: Processes all posts from PostgreSQL sequentially
- **Smart Comment Ordering**: Retrieves comments ordered by priority and text length
- **RAG-Optimized Format**: Creates structured chunks with metadata, titles, questions, and answers
- **Configurable Chunk Size**: Truncates text to specified word count (default: 700 words)
- **Batch Commits**: Commits every 1,000 inserts for optimal performance
- **Engagement Tracking**: Calculates engagement score based on comment count
- **Comprehensive Logging**: Detailed CloudWatch logs for monitoring and debugging

## Project Structure

```
etl2/
├── lambda_function.py          # Main Lambda handler
├── requirements.txt            # Python dependencies (psycopg2-binary)
├── schema.sql                  # PostgreSQL schema with facebook_chunks table
├── PRD.md                      # Product requirements document
├── deploy.py                   # Cross-platform deployment script
├── config/
│   └── config.json            # Configuration template
├── security/                   # Placeholder for credentials (not in git)
└── src/
    ├── __init__.py
    ├── config_manager.py      # Configuration loading and validation
    ├── database_reader.py     # PostgreSQL reader for posts and comments
    ├── chunk_generator.py     # RAG chunk generation logic
    ├── database_writer.py     # PostgreSQL writer for chunks
    └── logger.py              # Centralized logging
```

## Prerequisites

1. **Python 3.12** with virtual environment
2. **PostgreSQL Database** with:
   - `posts` table (with author column)
   - `comments` table
   - `facebook_chunks` table (created by schema.sql)
3. **AWS Account** with:
   - Lambda service access
   - VPC configuration (if database is in VPC)
   - Appropriate IAM role permissions

## Setup Instructions

### 1. Database Setup

Run the schema creation script on your PostgreSQL database:

```bash
psql -h your-host -U your-username -d your-database -f schema.sql
```

This creates:
- `posts` table (with author column added)
- `comments` table with foreign key to posts
- `facebook_chunks` table for storing generated chunks
- Indexes for performance optimization

### 2. Local Development Setup

Create and activate virtual environment:

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**Important**: The project uses `psycopg2-binary` specifically for AWS Lambda compatibility. The regular `psycopg2` package will fail on Lambda due to C extension compilation issues.

### 3. Configuration

Edit `config/config.json` with your settings:

```json
{
  "database": {
    "host": "your-postgres-host.amazonaws.com",
    "database": "your-database-name",
    "username": "your-username",
    "password": "your-password",
    "port": 5432
  },
  "processing": {
    "chunk_size": 700,
    "batch_commit_size": 1000
  },
  "aws": {
    "region": "us-east-1"
  },
  "admin_list": [
    "admin1@example.com",
    "admin2@example.com"
  ]
}
```

**Security Note**: For production, use AWS environment variables or Secrets Manager instead of storing credentials in config files.

### 4. Local Testing

Run the Lambda function locally:

```bash
python lambda_function.py
```

Or use the test script:

```bash
python test_local.py
```

### 5. Deployment to AWS Lambda

Use the deployment script:

```bash
python deploy.py
```

This will:
1. Clean previous builds
2. Create a `package` directory
3. Install dependencies to the package
4. Copy source code
5. Create `lambda-deployment.zip`

Then:
1. Upload `lambda-deployment.zip` to AWS Lambda
2. Set handler to: `lambda_function.lambda_handler`
3. Set runtime to: **Python 3.12**
4. Configure environment variables (see below)
5. Set memory to 1024 MB
6. Set timeout to 10 minutes (600 seconds)
7. Configure VPC access if database is in VPC

### 6. Lambda Environment Variables

Configure these environment variables in Lambda (they override config.json):

```
DB_HOST=your-postgres-host.amazonaws.com
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password
DB_PORT=5432
CHUNK_SIZE=700
BATCH_COMMIT_SIZE=1000
AWS_REGION=us-east-1
```

## Chunk Format

Each generated chunk follows this structure:

```
metadata: [Post_id: {post_id} | Timestamp: {timestamp} | Author: {first_5_chars}]

---

Title: {post_title}

---

Question (priority 1): {post_text}

---

Important answer (priority 2): {first_comment_text}

---

Other comments (priority 3): {remaining_comments_concatenated}
```

- Sections are separated by `\n\n---\n\n` delimiters (RAG-friendly)
- Text is truncated to `chunk_size` words (word boundaries preserved)
- Author is truncated to first 5 characters only

## Processing Logic

1. **Read Posts**: Fetch all posts from PostgreSQL sequentially
2. **Get Comments**: For each post, retrieve comments ordered by:
   - `comment_priority` (ascending)
   - `text_length` (ascending)
3. **Generate Chunk**: Create formatted text with all sections
4. **Truncate**: Limit to `chunk_size` words
5. **Calculate Engagement**: Count total comments for the post
6. **Insert**: Write chunk to `facebook_chunks` table
7. **Batch Commit**: Commit every 1,000 inserts

## Database Tables

### Input Tables

**posts**
```sql
post_id VARCHAR(255) PRIMARY KEY
timestamp TIMESTAMP
author VARCHAR(255)
title TEXT
post_texts TEXT
text_length INTEGER
```

**comments**
```sql
comment_id VARCHAR(255) PRIMARY KEY
post_id VARCHAR(255) FOREIGN KEY
timestamp TIMESTAMP
author VARCHAR(255)
comment_texts TEXT
comment_priority INTEGER
text_length INTEGER
```

### Output Table

**facebook_chunks**
```sql
chunk_id BIGSERIAL PRIMARY KEY
post_id VARCHAR(255) FOREIGN KEY
timestamp TIMESTAMP
full_chunk TEXT
engagement_score INTEGER
created_at TIMESTAMP
```

## Performance Considerations

- **Batch Commits**: Every 1,000 inserts to balance performance and reliability
- **Sequential Processing**: Ensures consistent and deterministic results
- **Connection Management**: Separate reader/writer connections to avoid conflicts
- **Memory Optimization**: Processes one post at a time to minimize memory usage

## Monitoring

Monitor the Lambda function using CloudWatch:

- **Logs**: Detailed processing logs with step-by-step progress
- **Metrics**: Posts processed, chunks created, success/failure counts
- **Errors**: Comprehensive error messages with context

## Troubleshooting

### Common Issues

1. **psycopg2 Import Error**
   - Ensure you're using `psycopg2-binary` in requirements.txt
   - Do NOT use regular `psycopg2` (it will fail on Lambda)

2. **Database Connection Timeout**
   - Verify Lambda is in the correct VPC/subnet
   - Check security group allows PostgreSQL access (port 5432)
   - Increase Lambda timeout if needed

3. **Memory Errors**
   - Increase Lambda memory allocation
   - Consider processing in smaller batches

4. **Table Not Found**
   - Verify schema.sql was executed successfully
   - Check that facebook_chunks table exists

## Testing

The project includes comprehensive testing capabilities:

1. **Local Testing**: Run `python lambda_function.py` with local config
2. **Unit Tests**: Test individual modules (chunk_generator, database_writer, etc.)
3. **Integration Tests**: Test full ETL pipeline with test database

## Security Best Practices

1. **Credentials**: Never commit credentials to git
2. **Environment Variables**: Use Lambda environment variables for production
3. **AWS Secrets Manager**: Consider using for sensitive data
4. **IAM Roles**: Use minimal required permissions
5. **VPC**: Deploy Lambda in VPC if database is private

## License

Proprietary - Internal use only

## Support

For issues or questions, contact the development team or refer to the PRD.md document.

---

**Version**: 1.0
**Python**: 3.12
**Last Updated**: 2026-01-13
