"""
Database migration script to add missing columns
Run this if you get "table has no column" errors
"""

import sqlite3
import os

databases = ['civ_ocr.db', 'civ_ocr_v2.db', 'civ_board_ocr.db']

for db_file in databases:
    if not os.path.exists(db_file):
        continue
    
    print(f"\n📦 Migrating: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check if ocr_corrections table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='ocr_corrections'
    """)
    
    if cursor.fetchone():
        # Check columns
        cursor.execute("PRAGMA table_info(ocr_corrections)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing column
        if 'corrected_by_engine' not in columns:
            print(f"  Adding corrected_by_engine column...")
            cursor.execute("""
                ALTER TABLE ocr_corrections 
                ADD COLUMN corrected_by_engine TEXT
            """)
            print(f"  ✅ Added corrected_by_engine")
        else:
            print(f"  ✓ corrected_by_engine already exists")
        
        conn.commit()
    else:
        print(f"  ⚠️  ocr_corrections table doesn't exist (will be created on first run)")
    
    conn.close()
    print(f"✅ {db_file} migrated")

print("\n✅ All databases migrated!")
print("\nNow restart your Streamlit app:")
print("  1. Press Ctrl+C to stop")
print("  2. Run: streamlit run app.py")
