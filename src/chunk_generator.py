"""
Chunk generator for creating RAG-ready text chunks from posts and comments.
"""

from src.logger import get_logger

logger = get_logger(__name__)


class ChunkGenerator:
    """
    Generates formatted text chunks from posts and comments for RAG systems.
    """

    # RAG-style delimiter between sections
    DELIMITER = "\n\n---\n\n"

    def __init__(self, chunk_size=300):
        """
        Initialize ChunkGenerator.

        Args:
            chunk_size (int): Maximum number of words per chunk
        """
        self.chunk_size = chunk_size
        logger.info(f"ChunkGenerator initialized with chunk_size={chunk_size}")

    def generate_chunk(self, post, comments):
        """
        Generate a formatted chunk from a post and its comments.

        Args:
            post (dict): Post dictionary with fields: post_id, timestamp, author, title, post_texts
            comments (list): List of comment dictionaries ordered by priority and text_length

        Returns:
            dict: Dictionary containing:
                - post_id: ID of the source post
                - timestamp: Timestamp of the post
                - full_chunk: The generated text chunk
                - engagement_score: Total number of comments
        """
        # Build the chunk components
        components = []

        # 1. Metadata section
        author_prefix = (post.get('author', '')[:5]) if post.get('author') else ''
        metadata = (
            f"metadata: [Post_id: {post.get('post_id', '')} | "
            f"Timestamp: {post.get('timestamp', '')} | "
            f"Author: {author_prefix}]"
        )
        components.append(metadata)

        # 2. Title section
        if post.get('title'):
            title_section = f"Title: {post.get('title')}"
            components.append(title_section)

        # 3. Question section (post content)
        if post.get('post_texts'):
            question_section = f"Question (priority 1): {post.get('post_texts')}"
            components.append(question_section)

        # 4. Important answer section (first comment only)
        if comments and len(comments) > 0:
            first_comment = comments[0].get('comment_texts', '')
            if first_comment:
                important_answer = f"Important answer (priority 2): {first_comment}"
                components.append(important_answer)

        # 5. Other comments section (remaining comments)
        if comments and len(comments) > 1:
            other_comments_texts = []
            for comment in comments[1:]:
                comment_text = comment.get('comment_texts', '')
                if comment_text:
                    other_comments_texts.append(comment_text)

            if other_comments_texts:
                # Concatenate other comments with delimiter
                other_comments_concat = self.DELIMITER.join(other_comments_texts)
                other_comments_section = f"Other comments (priority 3): {other_comments_concat}"
                components.append(other_comments_section)

        # Concatenate all components with delimiter
        full_text = self.DELIMITER.join(components)

        # Truncate to chunk_size words
        truncated_chunk = self._truncate_to_words(full_text, self.chunk_size)

        # Calculate engagement score (total number of comments)
        engagement_score = len(comments)

        result = {
            'post_id': post.get('post_id'),
            'timestamp': post.get('timestamp'),
            'full_chunk': truncated_chunk,
            'engagement_score': engagement_score
        }

        return result

    def _truncate_to_words(self, text, max_words):
        """
        Truncate text to a maximum number of words.

        Args:
            text (str): Text to truncate
            max_words (int): Maximum number of words

        Returns:
            str: Truncated text
        """
        if not text:
            return ""

        words = text.split()

        if len(words) <= max_words:
            return text

        # Take only the first max_words words
        truncated_words = words[:max_words]
        truncated_text = ' '.join(truncated_words)

        logger.debug(f"Truncated text from {len(words)} words to {max_words} words")

        return truncated_text

    def generate_chunks_batch(self, posts_with_comments):
        """
        Generate chunks for multiple posts.

        Args:
            posts_with_comments (list): List of tuples (post, comments)

        Returns:
            list: List of chunk dictionaries
        """
        chunks = []

        for post, comments in posts_with_comments:
            try:
                chunk = self.generate_chunk(post, comments)
                chunks.append(chunk)
            except Exception as e:
                logger.error(f"Failed to generate chunk for post {post.get('post_id')}: {e}")
                continue

        logger.info(f"Generated {len(chunks)} chunks from {len(posts_with_comments)} posts")
        return chunks
