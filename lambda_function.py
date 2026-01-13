"""
AWS Lambda function for Facebook Posts to RAG Chunks ETL.

This Lambda function reads Facebook posts and comments from PostgreSQL,
generates RAG-ready text chunks, and loads them into the facebook_chunks table.
"""

from src.config_manager import ConfigManager
from src.database_reader import DatabaseReader
from src.chunk_generator import ChunkGenerator
from src.database_writer import DatabaseWriter
from src.logger import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Main Lambda handler function.

    Args:
        event (dict): Lambda event object
        context (object): Lambda context object

    Returns:
        dict: Response with status code and processing summary
    """
    logger.info("=" * 80)
    logger.info("Lambda function execution started: Facebook Chunks ETL")
    logger.info("=" * 80)

    db_reader = None
    db_writer = None

    try:
        # 1. Load Configuration
        logger.info("Step 1: Loading configuration...")
        config_manager = ConfigManager()
        config_manager.validate()

        db_config = config_manager.get_database_config()
        chunk_size = config_manager.get_chunk_size()
        batch_commit_size = config_manager.get_batch_commit_size()

        logger.info(f"Configuration: chunk_size={chunk_size}, batch_commit_size={batch_commit_size}")

        # 2. Initialize Database Reader
        logger.info("Step 2: Connecting to database (reader)...")
        db_reader = DatabaseReader(db_config)
        db_reader.connect()

        # Verify tables exist
        if not db_reader.verify_tables_exist():
            error_msg = "Required database tables do not exist"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': {'error': error_msg}
            }

        # 3. Read All Posts
        logger.info("Step 3: Reading all posts from database...")
        posts = db_reader.get_all_posts()

        if not posts:
            logger.warning("No posts found in database")
            db_reader.disconnect()
            return {
                'statusCode': 200,
                'body': {
                    'message': 'No posts to process',
                    'posts_processed': 0,
                    'chunks_created': 0
                }
            }

        logger.info(f"Found {len(posts)} posts to process")

        # 4. Initialize Chunk Generator
        logger.info("Step 4: Initializing chunk generator...")
        chunk_generator = ChunkGenerator(chunk_size=chunk_size)

        # 5. Process Posts and Generate Chunks
        logger.info("Step 5: Processing posts and generating chunks...")
        chunks_to_insert = []

        for i, post in enumerate(posts, 1):
            post_id = post.get('post_id')

            # Get comments for this post
            comments = db_reader.get_comments_for_post(post_id)

            # Generate chunk
            chunk = chunk_generator.generate_chunk(post, comments)
            chunks_to_insert.append(chunk)

            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(posts)} posts...")

        logger.info(f"Generated {len(chunks_to_insert)} chunks")

        # Close reader connection
        db_reader.disconnect()
        db_reader = None

        # 6. Initialize Database Writer
        logger.info("Step 6: Connecting to database (writer)...")
        db_writer = DatabaseWriter(db_config, batch_commit_size=batch_commit_size)
        db_writer.connect()

        # Verify chunks table exists
        if not db_writer.verify_table_exists():
            error_msg = "facebook_chunks table does not exist"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': {'error': error_msg}
            }

        # 7. Insert Chunks
        logger.info("Step 7: Inserting chunks into database...")
        insert_stats = db_writer.insert_chunks_batch(chunks_to_insert)

        # 8. Disconnect Writer
        logger.info("Step 8: Closing database connection...")
        db_writer.disconnect()
        db_writer = None

        # 9. Prepare Response
        response = {
            'statusCode': 200,
            'body': {
                'message': 'ETL process completed successfully',
                'posts_processed': len(posts),
                'chunks_created': insert_stats['success'],
                'chunks_failed': insert_stats['failed'],
                'total_chunks': insert_stats['total']
            }
        }

        logger.info("=" * 80)
        logger.info("Lambda function execution completed successfully")
        logger.info(f"Posts processed: {len(posts)}")
        logger.info(f"Chunks created: {insert_stats['success']}/{insert_stats['total']}")
        logger.info("=" * 80)

        return response

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"Lambda function execution failed: {str(e)}")
        logger.error("=" * 80)

        # Clean up connections
        if db_reader:
            try:
                db_reader.disconnect()
            except:
                pass

        if db_writer:
            try:
                db_writer.disconnect()
            except:
                pass

        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'ETL process failed'
            }
        }


# For local testing
if __name__ == "__main__":
    # Mock event and context for local testing
    test_event = {}
    test_context = {}

    result = lambda_handler(test_event, test_context)
    print("\nLambda Response:")
    print(result)
