#!/usr/bin/env python3
"""
Test script to verify database fallback behavior when columns are missing.
"""

import os
import sys
import logging
from db_writer import DatabaseWriter, SchemaMismatchError, initialize_db_writer, get_db_writer
from events import SignalEvent
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fallback_behavior():
    """Test database operations with missing columns"""
    print("\n" + "="*80)
    print("Testing Database Fallback Behavior")
    print("="*80 + "\n")
    
    # Initialize database writer (will fail schema validation but continue)
    print("Test 1: Initializing database writer with schema mismatch...")
    try:
        db_url = os.environ.get('CORE_DATABASE_URL', 'postgresql://d@localhost/elpyfi')
        db_writer = initialize_db_writer(db_url)
        print("✓ Database writer initialized (with warnings)")
    except SchemaMismatchError:
        print("✗ Schema mismatch prevented initialization")
        # In the improved version, this should not happen - we continue with degraded mode
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return
    
    # Test 2: Try to write a position
    print("\nTest 2: Writing position (should handle missing order_id column)...")
    try:
        position_id = db_writer.write_position_opened(
            symbol="TEST",
            quantity=100.0,
            entry_price=50.0,
            strategy="test_strategy",
            order_id="TEST_ORDER_123"
        )
        if position_id:
            print(f"✓ Position written successfully with ID: {position_id}")
        else:
            print("✗ Position write failed but was handled gracefully")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 3: Try to write a signal
    print("\nTest 3: Writing signal (should handle missing columns)...")
    try:
        signal = SignalEvent(
            strategy="test_strategy",
            symbol="TEST",
            action="BUY",
            confidence=0.85,
            estimated_profit=100.0,
            timestamp=datetime.now()
        )
        signal.metadata = {"reason": "test signal"}
        
        signal_id = db_writer.write_signal(signal)
        if signal_id:
            print(f"✓ Signal written successfully with ID: {signal_id}")
        else:
            print("✗ Signal write failed but was handled gracefully")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "="*80)
    print("Fallback behavior test complete!")
    print("="*80)

if __name__ == "__main__":
    test_fallback_behavior()