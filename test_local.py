"""
Local testing script for the Facebook Chunks ETL Lambda function.

This script allows you to test the Lambda function locally before deploying to AWS.
"""

import sys
from lambda_function import lambda_handler


def main():
    """
    Run the Lambda function locally with mock event and context.
    """
    print("=" * 80)
    print("Local Testing: Facebook Chunks ETL Lambda Function")
    print("=" * 80)
    print()

    # Check if config file exists
    import os
    if not os.path.exists('config/config.json'):
        print("ERROR: config/config.json not found!")
        print("Please create config/config.json with your database credentials.")
        print()
        print("Example config.json:")
        print("""
{
  "database": {
    "host": "your-postgres-host",
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
  "admin_list": []
}
        """)
        return 1

    # Mock Lambda event and context
    test_event = {}

    class MockContext:
        """Mock Lambda context object."""
        def __init__(self):
            self.function_name = "facebook-chunks-etl-local"
            self.memory_limit_in_mb = 1024
            self.invoked_function_arn = "arn:aws:lambda:local:000000000000:function:test"
            self.aws_request_id = "local-test-request-id"

    test_context = MockContext()

    print("Starting Lambda function execution...")
    print()

    try:
        # Execute the Lambda function
        result = lambda_handler(test_event, test_context)

        print()
        print("=" * 80)
        print("Lambda Execution Result:")
        print("=" * 80)
        print(f"Status Code: {result.get('statusCode')}")
        print()
        print("Response Body:")
        for key, value in result.get('body', {}).items():
            print(f"  {key}: {value}")
        print()

        if result.get('statusCode') == 200:
            print("✓ Lambda function executed successfully!")
            return 0
        else:
            print("✗ Lambda function execution failed!")
            return 1

    except KeyboardInterrupt:
        print()
        print("Execution interrupted by user")
        return 130

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR: Lambda execution failed")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
