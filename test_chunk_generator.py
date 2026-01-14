"""
Unit tests for ChunkGenerator module.
Tests the chunk generation logic without requiring a database connection.
"""

import sys
sys.path.insert(0, '.')

from src.chunk_generator import ChunkGenerator
from datetime import datetime


def test_basic_chunk_generation():
    """Test basic chunk generation with post and comments."""
    print("\n" + "="*80)
    print("TEST 1: Basic Chunk Generation")
    print("="*80)

    # Create a test post
    post = {
        'post_id': 'POST_001',
        'timestamp': datetime(2026, 1, 13, 10, 30, 0),
        'author': 'JohnDoe123',
        'title': 'Test Post Title',
        'post_texts': 'This is the main post content asking a question.'
    }

    # Create test comments (ordered by priority and length)
    comments = [
        {
            'comment_id': 'COMMENT_001',
            'comment_texts': 'This is the most important comment with priority 1.',
            'comment_priority': 1,
            'text_length': 53
        },
        {
            'comment_id': 'COMMENT_002',
            'comment_texts': 'This is a secondary comment.',
            'comment_priority': 2,
            'text_length': 28
        },
        {
            'comment_id': 'COMMENT_003',
            'comment_texts': 'Another secondary comment here.',
            'comment_priority': 2,
            'text_length': 31
        }
    ]

    # Generate chunk
    chunk_generator = ChunkGenerator(chunk_size=700)
    chunk = chunk_generator.generate_chunk(post, comments)

    # Verify results
    assert chunk['post_id'] == 'POST_001', "Post ID mismatch"
    assert chunk['engagement_score'] == 3, f"Expected engagement score 3, got {chunk['engagement_score']}"
    assert 'metadata:' in chunk['full_chunk'], "Missing metadata section"
    assert 'Title: Test Post Title' in chunk['full_chunk'], "Missing title section"
    assert 'Question (priority 1):' in chunk['full_chunk'], "Missing question section"
    assert 'Important answer (priority 2):' in chunk['full_chunk'], "Missing important answer section"
    assert 'Other comments (priority 3):' in chunk['full_chunk'], "Missing other comments section"
    assert 'JohnD' in chunk['full_chunk'], "Author prefix not truncated correctly"

    print("\n✓ Chunk generated successfully!")
    print(f"  Post ID: {chunk['post_id']}")
    print(f"  Engagement Score: {chunk['engagement_score']}")
    print(f"  Chunk Length: {len(chunk['full_chunk'])} characters")
    print(f"  Word Count: {len(chunk['full_chunk'].split())} words")

    print("\n--- Generated Chunk ---")
    print(chunk['full_chunk'])
    print("--- End of Chunk ---\n")

    return True


def test_chunk_with_no_comments():
    """Test chunk generation when post has no comments."""
    print("\n" + "="*80)
    print("TEST 2: Chunk Generation with No Comments")
    print("="*80)

    post = {
        'post_id': 'POST_002',
        'timestamp': datetime(2026, 1, 13, 11, 0, 0),
        'author': 'Alice',
        'title': 'Post Without Comments',
        'post_texts': 'This post has no comments yet.'
    }

    comments = []

    chunk_generator = ChunkGenerator(chunk_size=700)
    chunk = chunk_generator.generate_chunk(post, comments)

    assert chunk['post_id'] == 'POST_002', "Post ID mismatch"
    assert chunk['engagement_score'] == 0, f"Expected engagement score 0, got {chunk['engagement_score']}"
    assert 'Important answer' not in chunk['full_chunk'], "Should not have important answer section"
    assert 'Other comments' not in chunk['full_chunk'], "Should not have other comments section"

    print("\n✓ Chunk generated successfully!")
    print(f"  Post ID: {chunk['post_id']}")
    print(f"  Engagement Score: {chunk['engagement_score']}")
    print(f"  Chunk Length: {len(chunk['full_chunk'])} characters")

    print("\n--- Generated Chunk ---")
    print(chunk['full_chunk'])
    print("--- End of Chunk ---\n")

    return True


def test_chunk_with_one_comment():
    """Test chunk generation when post has only one comment."""
    print("\n" + "="*80)
    print("TEST 3: Chunk Generation with One Comment")
    print("="*80)

    post = {
        'post_id': 'POST_003',
        'timestamp': datetime(2026, 1, 13, 12, 0, 0),
        'author': 'BobSmith',
        'title': 'Post With One Comment',
        'post_texts': 'Question with single answer.'
    }

    comments = [
        {
            'comment_id': 'COMMENT_004',
            'comment_texts': 'The only comment on this post.',
            'comment_priority': 1,
            'text_length': 31
        }
    ]

    chunk_generator = ChunkGenerator(chunk_size=700)
    chunk = chunk_generator.generate_chunk(post, comments)

    assert chunk['post_id'] == 'POST_003', "Post ID mismatch"
    assert chunk['engagement_score'] == 1, f"Expected engagement score 1, got {chunk['engagement_score']}"
    assert 'Important answer (priority 2):' in chunk['full_chunk'], "Should have important answer section"
    assert 'Other comments (priority 3):' not in chunk['full_chunk'], "Should not have other comments section"

    print("\n✓ Chunk generated successfully!")
    print(f"  Post ID: {chunk['post_id']}")
    print(f"  Engagement Score: {chunk['engagement_score']}")

    print("\n--- Generated Chunk ---")
    print(chunk['full_chunk'])
    print("--- End of Chunk ---\n")

    return True


def test_chunk_truncation():
    """Test that chunks are truncated to specified word count."""
    print("\n" + "="*80)
    print("TEST 4: Chunk Truncation")
    print("="*80)

    # Create a post with very long text
    long_text = " ".join([f"Word{i}" for i in range(500)])

    post = {
        'post_id': 'POST_004',
        'timestamp': datetime(2026, 1, 13, 13, 0, 0),
        'author': 'TestUser',
        'title': 'Long Post',
        'post_texts': long_text
    }

    comments = [
        {
            'comment_id': 'COMMENT_005',
            'comment_texts': " ".join([f"Comment{i}" for i in range(300)]),
            'comment_priority': 1,
            'text_length': 300
        }
    ]

    # Set a small chunk size
    chunk_size = 50
    chunk_generator = ChunkGenerator(chunk_size=chunk_size)
    chunk = chunk_generator.generate_chunk(post, comments)

    word_count = len(chunk['full_chunk'].split())

    print(f"\n✓ Chunk truncation working!")
    print(f"  Configured chunk size: {chunk_size} words")
    print(f"  Actual word count: {word_count} words")
    print(f"  Character count: {len(chunk['full_chunk'])} characters")

    assert word_count <= chunk_size, f"Chunk should be truncated to {chunk_size} words, but has {word_count} words"

    print("\n--- Truncated Chunk (first 500 chars) ---")
    print(chunk['full_chunk'][:500] + "...")
    print("--- End of Preview ---\n")

    return True


def test_author_prefix():
    """Test that author name is correctly truncated to 5 characters."""
    print("\n" + "="*80)
    print("TEST 5: Author Prefix Truncation")
    print("="*80)

    post = {
        'post_id': 'POST_005',
        'timestamp': datetime(2026, 1, 13, 14, 0, 0),
        'author': 'VeryLongAuthorName123456789',
        'title': 'Test Author Truncation',
        'post_texts': 'Testing author prefix.'
    }

    chunk_generator = ChunkGenerator(chunk_size=700)
    chunk = chunk_generator.generate_chunk(post, [])

    assert 'Author: VeryL]' in chunk['full_chunk'], "Author should be truncated to first 5 characters"
    assert 'VeryLongAuthorName' not in chunk['full_chunk'], "Full author name should not appear"

    print("\n✓ Author prefix correctly truncated!")
    print("  Original author: 'VeryLongAuthorName123456789'")
    print("  Truncated prefix: 'VeryL'")

    print("\n--- Metadata Section ---")
    # Extract just the metadata line
    lines = chunk['full_chunk'].split('\n')
    print(lines[0])
    print("--- End of Metadata ---\n")

    return True


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*80)
    print("RUNNING CHUNK GENERATOR UNIT TESTS")
    print("="*80)

    tests = [
        ("Basic Chunk Generation", test_basic_chunk_generation),
        ("No Comments", test_chunk_with_no_comments),
        ("One Comment", test_chunk_with_one_comment),
        ("Chunk Truncation", test_chunk_truncation),
        ("Author Prefix", test_author_prefix),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test_name}")
            print(f"  Exception: {e}")
            failed += 1

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
