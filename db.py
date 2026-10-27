"""
Database layer for OCR records
SQLite with two-table design: attempts vs. corrections
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import os

# Database file path
DB_PATH = "civ_ocr.db"

def compute_image_hash(image_bytes: bytes) -> str:
    """
    Compute stable hash from image bytes
    Returns 12-character hex hash
    """
    return hashlib.sha256(image_bytes).hexdigest()[:12]

def init_db():
    """Initialize the database with two tables: ocr_attempts and ocr_corrections"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we need to migrate from old schema
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='ocr_records'
    """)
    old_table_exists = cursor.fetchone() is not None
    
    # Check for new tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='ocr_attempts'
    """)
    attempts_exists = cursor.fetchone() is not None
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='ocr_corrections'
    """)
    corrections_exists = cursor.fetchone() is not None
    
    # Create new schema
    if not attempts_exists:
        cursor.execute("""
            CREATE TABLE ocr_attempts (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id TEXT NOT NULL,
                civ_board_language TEXT,
                original_image_path TEXT NOT NULL,
                crop_box TEXT NOT NULL,
                cropped_image_path TEXT NOT NULL,
                engine_used TEXT NOT NULL,
                eocr_pred TEXT,
                ocr_confidence REAL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(image_id, engine_used)
            )
        """)
        print(f"✅ Created table: ocr_attempts")
    
    if not corrections_exists:
        cursor.execute("""
            CREATE TABLE ocr_corrections (
                image_id TEXT PRIMARY KEY,
                correction_mode TEXT,
                eocr_corrected TEXT NOT NULL,
                corrected_by_engine TEXT,
                target_language TEXT,
                translated_text TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        print(f"✅ Created table: ocr_corrections")
    else:
        # Check if corrected_by_engine column exists
        cursor.execute("PRAGMA table_info(ocr_corrections)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'corrected_by_engine' not in columns:
            print("📦 Adding missing column: corrected_by_engine")
            cursor.execute("""
                ALTER TABLE ocr_corrections 
                ADD COLUMN corrected_by_engine TEXT
            """)
            print("✅ Added corrected_by_engine column")
    
    # Migrate old data if exists
    if old_table_exists and (not attempts_exists or not corrections_exists):
        print("📦 Migrating data from old schema...")
        # Just drop old table for clean slate (dev data)
        # In production, you'd migrate the data
        cursor.execute("DROP TABLE IF EXISTS ocr_records")
        print("🗑️ Dropped old ocr_records table (clean start)")
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

def save_ocr_attempt(
    image_id: str,
    civ_board_language: str,
    original_image_path: str,
    crop_box: Dict,
    cropped_image_path: str,
    engine_used: str,
    eocr_pred: str,
    ocr_confidence: float
) -> int:
    """
    Save or update an OCR attempt
    Uses UPSERT to handle re-running same engine on same image
    Returns the row_id
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    crop_box_json = json.dumps(crop_box)
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO ocr_attempts (
            image_id, civ_board_language, original_image_path, crop_box, 
            cropped_image_path, engine_used, eocr_pred, ocr_confidence, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(image_id, engine_used) DO UPDATE SET
            eocr_pred = excluded.eocr_pred,
            ocr_confidence = excluded.ocr_confidence,
            created_at = excluded.created_at
    """, (
        image_id, civ_board_language, original_image_path, crop_box_json,
        cropped_image_path, engine_used, eocr_pred, ocr_confidence, created_at
    ))
    
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return row_id

def get_ocr_attempt(image_id: str, engine_used: str) -> Optional[Dict]:
    """Get a specific OCR attempt by image_id and engine"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM ocr_attempts 
        WHERE image_id = ? AND engine_used = ?
    """, (image_id, engine_used))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        record = dict(row)
        if record['crop_box']:
            record['crop_box'] = json.loads(record['crop_box'])
        return record
    
    return None

def get_all_attempts_for_image(image_id: str) -> List[Dict]:
    """Get all OCR attempts for a specific image"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM ocr_attempts 
        WHERE image_id = ?
        ORDER BY created_at DESC
    """, (image_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    records = []
    for row in rows:
        record = dict(row)
        if record['crop_box']:
            record['crop_box'] = json.loads(record['crop_box'])
        records.append(record)
    
    return records

def save_correction(
    image_id: str,
    correction_mode: str,
    eocr_corrected: str,
    corrected_by_engine: str,
    target_language: str = None,
    translated_text: str = None
) -> None:
    """
    Save or update correction for an image
    Always uses UPSERT - one correction per image
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO ocr_corrections
            (image_id, correction_mode, eocr_corrected, corrected_by_engine,
             target_language, translated_text, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(image_id) DO UPDATE SET
            correction_mode = excluded.correction_mode,
            eocr_corrected = excluded.eocr_corrected,
            corrected_by_engine = excluded.corrected_by_engine,
            target_language = excluded.target_language,
            translated_text = excluded.translated_text,
            updated_at = excluded.updated_at
    """, (image_id, correction_mode, eocr_corrected, corrected_by_engine,
          target_language, translated_text, updated_at))
    
    conn.commit()
    conn.close()

def get_correction(image_id: str) -> Optional[Dict]:
    """Get correction for a specific image"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM ocr_corrections 
        WHERE image_id = ?
    """, (image_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def get_all_images() -> List[Dict]:
    """
    Get all images with their attempts and corrections
    Returns list of image records with attempts and correction nested
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all unique images
    cursor.execute("""
        SELECT DISTINCT image_id, original_image_path, cropped_image_path, 
                        civ_board_language, crop_box, created_at
        FROM ocr_attempts
        ORDER BY created_at DESC
    """)
    
    images = []
    for row in cursor.fetchall():
        image_data = dict(row)
        image_id = image_data['image_id']
        
        if image_data['crop_box']:
            image_data['crop_box'] = json.loads(image_data['crop_box'])
        
        # Get all attempts for this image
        cursor.execute("""
            SELECT engine_used, eocr_pred, ocr_confidence, created_at
            FROM ocr_attempts
            WHERE image_id = ?
            ORDER BY created_at DESC
        """, (image_id,))
        
        image_data['attempts'] = [dict(r) for r in cursor.fetchall()]
        
        # Get correction if exists
        cursor.execute("""
            SELECT * FROM ocr_corrections
            WHERE image_id = ?
        """, (image_id,))
        
        correction_row = cursor.fetchone()
        image_data['correction'] = dict(correction_row) if correction_row else None
        
        images.append(image_data)
    
    conn.close()
    return images

def delete_image(image_id: str) -> bool:
    """Delete an image and all its attempts and correction"""
    # Get file paths before deletion
    attempts = get_all_attempts_for_image(image_id)
    if not attempts:
        return False
    
    # Delete files (only once per unique path)
    file_paths = set()
    for attempt in attempts:
        file_paths.add(attempt.get('original_image_path'))
        file_paths.add(attempt.get('cropped_image_path'))
    
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Deleted file: {file_path}")
            except Exception as e:
                print(f"⚠️ Could not delete file {file_path}: {e}")
    
    # Delete database records
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ocr_attempts WHERE image_id = ?", (image_id,))
    cursor.execute("DELETE FROM ocr_corrections WHERE image_id = ?", (image_id,))
    conn.commit()
    conn.close()
    
    print(f"✅ Image {image_id} and all related records deleted")
    return True

def get_stats() -> Dict:
    """Get database statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total unique images
    cursor.execute("SELECT COUNT(DISTINCT image_id) FROM ocr_attempts")
    total_images = cursor.fetchone()[0]
    
    # Total attempts
    cursor.execute("SELECT COUNT(*) FROM ocr_attempts")
    total_attempts = cursor.fetchone()[0]
    
    # Total corrections
    cursor.execute("SELECT COUNT(*) FROM ocr_corrections")
    total_corrections = cursor.fetchone()[0]
    
    # Attempts by engine
    cursor.execute("""
        SELECT engine_used, COUNT(*) 
        FROM ocr_attempts 
        GROUP BY engine_used
    """)
    engine_stats = dict(cursor.fetchall())
    
    # Average confidence by engine
    cursor.execute("""
        SELECT engine_used, AVG(ocr_confidence) 
        FROM ocr_attempts 
        WHERE ocr_confidence IS NOT NULL
        GROUP BY engine_used
    """)
    confidence_stats = {engine: round(conf, 3) for engine, conf in cursor.fetchall()}
    
    conn.close()
    
    return {
        'total_images': total_images,
        'total_attempts': total_attempts,
        'total_corrections': total_corrections,
        'engine_usage': engine_stats,
        'avg_confidence_by_engine': confidence_stats
    }

# Backward compatibility functions (deprecated but functional during migration)
def save_record(
    image_id: str,
    civ_board_language: str,
    original_image_path: str,
    crop_box: Dict,
    cropped_image_path: str,
    engine_used: str,
    eocr_pred: str,
    ocr_confidence: float,
    correction_mode: str,
    eocr_corrected: str,
    target_language: str = None,
    translated_text: str = None
) -> int:
    """
    Backward compatibility wrapper - splits into attempt + correction
    This allows old code to work while migrating to new schema
    """
    # Save OCR attempt
    save_ocr_attempt(
        image_id=image_id,
        civ_board_language=civ_board_language,
        original_image_path=original_image_path,
        crop_box=crop_box,
        cropped_image_path=cropped_image_path,
        engine_used=engine_used,
        eocr_pred=eocr_pred,
        ocr_confidence=ocr_confidence
    )
    
    # Save correction
    save_correction(
        image_id=image_id,
        correction_mode=correction_mode,
        eocr_corrected=eocr_corrected,
        corrected_by_engine=engine_used,
        target_language=target_language,
        translated_text=translated_text
    )
    
    # Return a pseudo-ID (not really used in new schema)
    return hash(image_id) % 1000000

def get_all_records():
    """Backward compatibility: Use get_all_images() instead"""
    return get_all_images()

def get_record_by_id(record_id: int):
    """Backward compatibility: Records no longer have single row_id"""
    # Try to find by pseudo-matching
    images = get_all_images()
    if record_id < len(images):
        img = images[record_id]
        # Flatten for old format
        return {
            'row_id': record_id,
            'image_id': img['image_id'],
            'civ_board_language': img.get('civ_board_language'),
            'original_image_path': img.get('original_image_path'),
            'cropped_image_path': img.get('cropped_image_path'),
            'crop_box': img.get('crop_box'),
            'engine_used': img['attempts'][0]['engine_used'] if img['attempts'] else '',
            'eocr_pred': img['attempts'][0]['eocr_pred'] if img['attempts'] else '',
            'ocr_confidence': img['attempts'][0]['ocr_confidence'] if img['attempts'] else 0,
            'correction_mode': img['correction']['correction_mode'] if img['correction'] else '',
            'eocr_corrected': img['correction']['eocr_corrected'] if img['correction'] else '',
            'target_language': img['correction']['target_language'] if img['correction'] else '',
            'translated_text': img['correction']['translated_text'] if img['correction'] else '',
            'created_at': img.get('created_at')
        }
    return None

def delete_record(record_id: int):
    """Backward compatibility: Use delete_image() instead"""
    # Get image by index
    images = get_all_images()
    if record_id < len(images):
        image_id = images[record_id]['image_id']
        return delete_image(image_id)
    return False

# Initialize database on module import
if __name__ == "__main__":
    init_db()
    print("✅ Database test completed")