"""
Database writer for inserting chunks into PostgreSQL.
"""

import psycopg2
from src.logger import get_logger

logger = get_logger(__name__)


class DatabaseWriter:
    """
    Handles writing chunks to PostgreSQL database with batch commits.
    """

    def __init__(self, db_config, batch_commit_size=1000):
        """
        Initialize DatabaseWriter with database configuration.

        Args:
            db_config (dict): Database configuration containing host, database, username, password, port
            batch_commit_size (int): Number of inserts before committing (default: 1000)
        """
        self.db_config = db_config
        self.batch_commit_size = batch_commit_size
        self.connection = None
        self.cursor = None
        self.insert_count = 0
        self.total_inserted = 0
        self.total_failed = 0
        logger.info(f"DatabaseWriter initialized with batch_commit_size={batch_commit_size}")

    def connect(self):
        """
        Establish connection to PostgreSQL database.

        Raises:
            psycopg2.Error: If connection fails
        """
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get("host"),
                database=self.db_config.get("database"),
                user=self.db_config.get("username"),
                password=self.db_config.get("password"),
                port=self.db_config.get("port", 5432)
            )
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to database: {self.db_config.get('database')}")

        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        # Final commit for any remaining records
        if self.insert_count > 0:
            self._commit()

        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")

    def insert_chunk(self, chunk):
        """
        Insert a single chunk into the facebook_chunks table.
        Commits automatically every batch_commit_size inserts.

        Args:
            chunk (dict): Chunk dictionary with post_id, timestamp, full_chunk, engagement_score

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            insert_query = """
                INSERT INTO facebook_chunks (post_id, timestamp, full_chunk, engagement_score)
                VALUES (%s, %s, %s, %s);
            """

            self.cursor.execute(
                insert_query,
                (
                    chunk.get('post_id'),
                    chunk.get('timestamp'),
                    chunk.get('full_chunk'),
                    chunk.get('engagement_score')
                )
            )

            self.insert_count += 1

            # Commit every batch_commit_size inserts
            if self.insert_count >= self.batch_commit_size:
                self._commit()

            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to insert chunk for post {chunk.get('post_id')}: {e}")
            self.connection.rollback()
            self.total_failed += 1
            return False

    def insert_chunks_batch(self, chunks):
        """
        Insert multiple chunks.

        Args:
            chunks (list): List of chunk dictionaries

        Returns:
            dict: Statistics about the insertion (total, success, failed)
        """
        success_count = 0
        failed_count = 0

        logger.info(f"Inserting {len(chunks)} chunks into database")

        for chunk in chunks:
            if self.insert_chunk(chunk):
                success_count += 1
            else:
                failed_count += 1

        # Ensure any remaining records are committed
        if self.insert_count > 0:
            self._commit()

        stats = {
            'total': len(chunks),
            'success': success_count,
            'failed': failed_count
        }

        logger.info(f"Chunk insertion complete: {stats}")
        return stats

    def _commit(self):
        """
        Commit current transaction and reset insert counter.
        """
        try:
            self.connection.commit()
            self.total_inserted += self.insert_count
            logger.info(f"Committed {self.insert_count} records (total: {self.total_inserted})")
            self.insert_count = 0

        except psycopg2.Error as e:
            logger.error(f"Failed to commit transaction: {e}")
            self.connection.rollback()
            raise

    def get_statistics(self):
        """
        Get insertion statistics.

        Returns:
            dict: Statistics with total_inserted and total_failed counts
        """
        return {
            'total_inserted': self.total_inserted,
            'total_failed': self.total_failed
        }

    def verify_table_exists(self):
        """
        Verify that facebook_chunks table exists in the database.

        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'facebook_chunks'
                );
            """)
            exists = self.cursor.fetchone()[0]

            if exists:
                logger.info("Verified: facebook_chunks table exists")
                return True
            else:
                logger.error("facebook_chunks table does not exist in database")
                return False

        except psycopg2.Error as e:
            logger.error(f"Failed to verify table: {e}")
            return False
