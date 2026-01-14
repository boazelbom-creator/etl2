"""
Unit tests for ConfigManager module.
Tests configuration loading and validation.
"""

import sys
sys.path.insert(0, '.')

import os
import json
import tempfile
from src.config_manager import ConfigManager


def test_config_loading_from_file():
    """Test loading configuration from JSON file."""
    print("\n" + "="*80)
    print("TEST 1: Loading Configuration from File")
    print("="*80)

    # Create a temporary config file
    config_data = {
        "database": {
            "host": "test-host.com",
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass",
            "port": 5432
        },
        "processing": {
            "chunk_size": 500,
            "batch_commit_size": 2000
        },
        "aws": {
            "region": "us-west-2"
        },
        "admin_list": ["admin@test.com"]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        # Load config
        config_manager = ConfigManager(config_file=temp_config_file)

        # Test database config
        db_config = config_manager.get_database_config()
        assert db_config['host'] == 'test-host.com', "Host mismatch"
        assert db_config['database'] == 'test_db', "Database name mismatch"
        assert db_config['port'] == 5432, "Port mismatch"

        # Test processing config
        assert config_manager.get_chunk_size() == 500, "Chunk size mismatch"
        assert config_manager.get_batch_commit_size() == 2000, "Batch commit size mismatch"

        # Test AWS config
        assert config_manager.get_aws_region() == 'us-west-2', "AWS region mismatch"

        # Test admin list
        admin_list = config_manager.get_admin_list()
        assert len(admin_list) == 1, "Admin list length mismatch"
        assert admin_list[0] == 'admin@test.com', "Admin email mismatch"

        print("\n✓ Configuration loaded successfully from file!")
        print(f"  Database Host: {db_config['host']}")
        print(f"  Database Name: {db_config['database']}")
        print(f"  Chunk Size: {config_manager.get_chunk_size()}")
        print(f"  Batch Commit Size: {config_manager.get_batch_commit_size()}")
        print(f"  AWS Region: {config_manager.get_aws_region()}")
        print(f"  Admin List: {admin_list}")

    finally:
        # Clean up
        os.unlink(temp_config_file)

    return True


def test_config_validation_success():
    """Test successful configuration validation."""
    print("\n" + "="*80)
    print("TEST 2: Configuration Validation (Valid Config)")
    print("="*80)

    config_data = {
        "database": {
            "host": "valid-host.com",
            "database": "valid_db",
            "username": "valid_user",
            "password": "valid_pass",
            "port": 5432
        },
        "processing": {
            "chunk_size": 700
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        config_manager = ConfigManager(config_file=temp_config_file)

        # Should not raise exception
        config_manager.validate()

        print("\n✓ Configuration validation passed!")
        print("  All required fields are present")

    finally:
        os.unlink(temp_config_file)

    return True


def test_config_validation_missing_database():
    """Test validation failure when database config is missing."""
    print("\n" + "="*80)
    print("TEST 3: Configuration Validation (Missing Database)")
    print("="*80)

    config_data = {
        "processing": {
            "chunk_size": 700
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        config_manager = ConfigManager(config_file=temp_config_file)

        # Should raise ValueError
        try:
            config_manager.validate()
            print("\n✗ Validation should have failed!")
            return False
        except ValueError as e:
            print(f"\n✓ Validation correctly failed: {e}")
            return True

    finally:
        os.unlink(temp_config_file)


def test_config_validation_missing_fields():
    """Test validation failure when required database fields are missing."""
    print("\n" + "="*80)
    print("TEST 4: Configuration Validation (Missing Database Fields)")
    print("="*80)

    config_data = {
        "database": {
            "host": "test-host.com",
            # Missing: database, username, password, port
        },
        "processing": {
            "chunk_size": 700
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        config_manager = ConfigManager(config_file=temp_config_file)

        # Should raise ValueError
        try:
            config_manager.validate()
            print("\n✗ Validation should have failed!")
            return False
        except ValueError as e:
            print(f"\n✓ Validation correctly failed: {e}")
            assert "database" in str(e).lower() or "username" in str(e).lower(), "Error message should mention missing field"
            return True

    finally:
        os.unlink(temp_config_file)


def test_config_env_override():
    """Test that environment variables override config file values."""
    print("\n" + "="*80)
    print("TEST 5: Environment Variable Override")
    print("="*80)

    # Create config file with default values
    config_data = {
        "database": {
            "host": "file-host.com",
            "database": "file_db",
            "username": "file_user",
            "password": "file_pass",
            "port": 5432
        },
        "processing": {
            "chunk_size": 300
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        # Set environment variables
        os.environ['DB_HOST'] = 'env-host.com'
        os.environ['DB_NAME'] = 'env_db'
        os.environ['DB_USER'] = 'env_user'
        os.environ['DB_PASSWORD'] = 'env_pass'
        os.environ['DB_PORT'] = '3306'
        os.environ['CHUNK_SIZE'] = '999'

        config_manager = ConfigManager(config_file=temp_config_file)

        # Test that env vars override file values
        db_config = config_manager.get_database_config()
        assert db_config['host'] == 'env-host.com', "Env var should override file"
        assert db_config['database'] == 'env_db', "Env var should override file"
        assert db_config['port'] == 3306, "Env var should override file"
        assert config_manager.get_chunk_size() == 999, "Env var should override file"

        print("\n✓ Environment variables correctly override config file!")
        print(f"  File Host: 'file-host.com' → Env Host: '{db_config['host']}'")
        print(f"  File Database: 'file_db' → Env Database: '{db_config['database']}'")
        print(f"  File Port: 5432 → Env Port: {db_config['port']}")
        print(f"  File Chunk Size: 300 → Env Chunk Size: {config_manager.get_chunk_size()}")

    finally:
        # Clean up
        os.unlink(temp_config_file)
        del os.environ['DB_HOST']
        del os.environ['DB_NAME']
        del os.environ['DB_USER']
        del os.environ['DB_PASSWORD']
        del os.environ['DB_PORT']
        del os.environ['CHUNK_SIZE']

    return True


def test_config_defaults():
    """Test default values when optional fields are missing."""
    print("\n" + "="*80)
    print("TEST 6: Default Values")
    print("="*80)

    config_data = {
        "database": {
            "host": "test-host.com",
            "database": "test_db",
            "username": "test_user",
            "password": "test_pass",
            "port": 5432
        },
        "processing": {
            "chunk_size": 700
            # Missing batch_commit_size
        }
        # Missing aws section
        # Missing admin_list
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name

    try:
        config_manager = ConfigManager(config_file=temp_config_file)

        # Test default values
        assert config_manager.get_batch_commit_size() == 1000, "Default batch size should be 1000"
        assert config_manager.get_aws_region() == 'us-east-1', "Default region should be us-east-1"
        assert config_manager.get_admin_list() == [], "Default admin list should be empty"

        print("\n✓ Default values working correctly!")
        print(f"  Default Batch Commit Size: {config_manager.get_batch_commit_size()}")
        print(f"  Default AWS Region: {config_manager.get_aws_region()}")
        print(f"  Default Admin List: {config_manager.get_admin_list()}")

    finally:
        os.unlink(temp_config_file)

    return True


def run_all_tests():
    """Run all configuration tests."""
    print("\n" + "="*80)
    print("RUNNING CONFIGURATION MANAGER UNIT TESTS")
    print("="*80)

    tests = [
        ("Load Config from File", test_config_loading_from_file),
        ("Valid Config Validation", test_config_validation_success),
        ("Missing Database Config", test_config_validation_missing_database),
        ("Missing Database Fields", test_config_validation_missing_fields),
        ("Environment Variable Override", test_config_env_override),
        ("Default Values", test_config_defaults),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test_name}")
            print(f"  Exception: {e}")
            import traceback
            traceback.print_exc()
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
