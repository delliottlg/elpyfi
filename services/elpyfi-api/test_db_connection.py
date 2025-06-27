#!/usr/bin/env python3
"""Test database connection for elPyFi API"""

import asyncio
import asyncpg
import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_connection():
    """Test basic database connection"""
    # Try different connection strings
    connection_strings = [
        "postgresql://d@localhost:5432/elpyfi",
        "postgresql://d@localhost/elpyfi",
        os.getenv("ELPYFI_DATABASE_URL", ""),
    ]
    
    for conn_str in connection_strings:
        if not conn_str:
            continue
            
        print(f"\nTrying connection: {conn_str}")
        try:
            # Test connection
            conn = await asyncpg.connect(conn_str)
            
            # Test query
            result = await conn.fetchval("SELECT COUNT(*) FROM signals")
            print(f"✅ Connection successful! Found {result} signals in database")
            
            # Check tables
            tables = await conn.fetch("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            
            print("\nTables found:")
            for table in tables:
                print(f"  - {table['tablename']}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if not success:
        print("\n⚠️  No successful connection. Check your database configuration.")