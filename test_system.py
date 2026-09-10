#!/usr/bin/env python3
"""Test script to verify Sqlantra System V2 core functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database():
    """Test database initialization and basic operations."""
    print("Testing database...")
    try:
        import sqlantra_database_v2 as db
        db.init_database()
        print("✓ Database initialized successfully")
        
        # Test getting tables
        import sqlite3
        conn = sqlite3.connect('/tmp/sqlantra_v2_demo.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✓ Found {len(tables)} tables in database")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_modules():
    """Test that all modules can be imported."""
    print("\nTesting module imports...")
    try:
        import sqlantra_database_v2
        print("✓ sqlantra_database_v2 imported")
        
        import text_to_sql
        print("✓ text_to_sql imported")
        
        import context_memory
        print("✓ context_memory imported")
        
        import hitl_workflow
        print("✓ hitl_workflow imported")
        
        return True
    except Exception as e:
        print(f"✗ Module import failed: {e}")
        return False

def test_text_to_sql():
    """Test text-to-SQL conversion."""
    print("\nTesting text-to-SQL...")
    try:
        import text_to_sql
        # Test with a simple query
        result = text_to_sql.text_to_sql("Show all completed orders")
        print(f"✓ Text-to-SQL conversion works: {result[:50]}...")
        return True
    except Exception as e:
        print(f"✗ Text-to-SQL test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Sqlantra System V2 Core Functionality Test")
    print("=" * 40)
    
    tests = [
        test_database,
        test_modules,
        test_text_to_sql
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All core functionality tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())