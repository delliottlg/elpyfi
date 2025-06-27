#!/usr/bin/env python3
"""
Test script to verify database schema mismatch error handling improvements.
This script simulates various schema mismatch scenarios.
"""

import os
import sys
import logging
from db_writer import DatabaseWriter, SchemaMismatchError, initialize_db_writer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_schema_mismatch_detection():
    """Test schema mismatch detection and error messages"""
    print("\n" + "="*80)
    print("Testing Database Schema Mismatch Error Handling")
    print("="*80 + "\n")
    
    # Test 1: Try to initialize with potentially mismatched schema
    print("Test 1: Initializing database writer...")
    try:
        db_url = os.environ.get('CORE_DATABASE_URL', 'postgresql://d@localhost/elpyfi')
        db_writer = initialize_db_writer(db_url)
        print("✓ Database initialized successfully - schema is valid!")
        
        # Test write operations
        print("\nTest 2: Testing write operations...")
        try:
            position_id = db_writer.write_position_opened(
                symbol="TEST",
                quantity=100.0,
                entry_price=50.0,
                strategy="test_strategy",
                order_id="TEST_ORDER_123"
            )
            if position_id:
                print(f"✓ Successfully wrote position with ID: {position_id}")
            else:
                print("✗ Write operation failed but was handled gracefully")
        except Exception as e:
            print(f"✗ Unexpected error during write: {e}")
            
    except SchemaMismatchError as e:
        print(f"✗ Schema mismatch detected: {e}")
        print("\nDetailed error information:")
        if e.missing_tables:
            print(f"  - Missing tables: {e.missing_tables}")
        if e.schema_issues:
            print("  - Missing columns:")
            for table, cols in e.schema_issues.items():
                print(f"    * {table}: {', '.join(cols)}")
        
        # Show fix SQL
        fix_sql = e.get_fix_sql()
        if fix_sql:
            print("\nGenerated fix SQL:")
            print("-" * 80)
            print(fix_sql)
            print("-" * 80)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "="*80)
    print("Test complete!")
    print("="*80)

def test_schema_error_fix_sql():
    """Test the SQL generation for fixing schema issues"""
    print("\nTest 3: Testing schema fix SQL generation...")
    
    # Create a mock SchemaMismatchError
    error = SchemaMismatchError(
        "Test error",
        missing_columns=['order_id', 'closed_at'],
        missing_tables=['signals'],
        schema_issues={
            'positions': ['order_id', 'closed_at'],
            'signals': ['metadata', 'expected_profit']
        }
    )
    
    fix_sql = error.get_fix_sql()
    print("Generated fix SQL for mock error:")
    print("-" * 80)
    print(fix_sql)
    print("-" * 80)

if __name__ == "__main__":
    test_schema_mismatch_detection()
    test_schema_error_fix_sql()