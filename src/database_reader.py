"""
Database reader for fetching posts and comments from PostgreSQL.
"""

import psycopg2
from src.logger import get_logger

logger = get_logger(__name__)


class DatabaseReader:
    """
    Handles reading posts and comments from PostgreSQL database.
    """

    def __init__(self, db_config):
        """
        Initialize DatabaseReader with database configuration.

        Args:
            db_config (dict): Database configuration containing host, database, username, password, port
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        logger.info("DatabaseReader initialized")

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
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")

    def get_all_posts(self):
        """
        Retrieve all posts from the database.

        Returns:
            list: List of post dictionaries with all fields
        """
        try:
            query = """
                SELECT post_id, timestamp, author, title, post_texts, text_length
                FROM posts
                ORDER BY post_id;
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            posts = []
            for row in rows:
                post = {
                    'post_id': row[0],
                    'timestamp': row[1],
                    'author': row[2],
                    'title': row[3],
                    'post_texts': row[4],
                    'text_length': row[5]
                }
                posts.append(post)

            logger.info(f"Retrieved {len(posts)} posts from database")
            return posts

        except psycopg2.Error as e:
            logger.error(f"Failed to fetch posts: {e}")
            raise

    def get_comments_for_post(self, post_id):
        """
        Retrieve all comments for a specific post, ordered by priority and text length.

        Args:
            post_id (str): The post ID to fetch comments for

        Returns:
            list: List of comment dictionaries ordered by comment_priority, then text_length
        """
        try:
            query = """
                SELECT comment_id, post_id, timestamp, author, comment_texts,
                       comment_priority, text_length
                FROM comments
                WHERE post_id = %s
                ORDER BY comment_priority ASC, text_length ASC;
            """
            self.cursor.execute(query, (post_id,))
            rows = self.cursor.fetchall()

            comments = []
            for row in rows:
                comment = {
                    'comment_id': row[0],
                    'post_id': row[1],
                    'timestamp': row[2],
                    'author': row[3],
                    'comment_texts': row[4],
                    'comment_priority': row[5],
                    'text_length': row[6]
                }
                comments.append(comment)

            return comments

        except psycopg2.Error as e:
            logger.error(f"Failed to fetch comments for post {post_id}: {e}")
            raise

    def verify_tables_exist(self):
        """
        Verify that required tables (posts, comments, facebook_chunks) exist in the database.

        Returns:
            bool: True if all tables exist, False otherwise
        """
        try:
            required_tables = ['posts', 'comments', 'facebook_chunks']

            for table_name in required_tables:
                self.cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, (table_name,))
                exists = self.cursor.fetchone()[0]

                if not exists:
                    logger.error(f"Required table '{table_name}' does not exist in database")
                    return False

            logger.info("Verified: all required tables exist")
            return True

        except psycopg2.Error as e:
            logger.error(f"Failed to verify tables: {e}")
            return False
