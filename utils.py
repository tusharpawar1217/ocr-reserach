"""
Utility functions for CIV Board OCR Application
"""

import cv2
import numpy as np
import re
import sqlite3
import pandas as pd
from datetime import datetime
import os
from config import *

class ImageUtils:
    @staticmethod
    def validate_image(uploaded_file):
        """Validate uploaded image file"""
        if uploaded_file is None:
            return False, "No file uploaded"
        
        # Check file size
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > IMAGE_PROCESSING['max_file_size_mb']:
            return False, f"File size too large: {file_size_mb:.1f}MB (max: {IMAGE_PROCESSING['max_file_size_mb']}MB)"
        
        # Check file format
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in IMAGE_PROCESSING['supported_formats']:
            return False, f"Unsupported format: {file_extension}"
        
        return True, "Valid image"
    
    @staticmethod
    def enhance_image_quality(image):
        """Apply advanced image enhancement techniques"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Bilateral filtering for noise reduction while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Morphological operations to clean up
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(filtered, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    @staticmethod
    def detect_text_regions(image):
        """Detect potential text regions in the image"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours that might contain text
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            area = cv2.contourArea(contour)
            
            # Filter based on size and aspect ratio
            if area > 100 and 0.1 < aspect_ratio < 10:
                text_regions.append((x, y, w, h))
        
        return text_regions

class TextUtils:
    @staticmethod
    def clean_extracted_text(text):
        """Clean and format extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that are likely OCR errors
        text = re.sub(r'[^\u0900-\u097F\u0020-\u007E\u00A0-\u00FF]', '', text)
        
        # Clean up common OCR mistakes
        replacements = {
            '।।': '।',
            ',,': ',',
            '..': '.',
            '  ': ' '
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    @staticmethod
    def extract_key_information(text):
        """Extract key information like IDs, dates, etc."""
        info = {}
        
        # Extract work ID patterns
        work_id_pattern = r'[A-Z]{2}/\d+'
        work_ids = re.findall(work_id_pattern, text)
        info['work_ids'] = work_ids
        
        # Extract date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}-\d{1,2}-\d{1,2}'
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        info['dates'] = dates
        
        # Extract amounts (currency)
        amount_pattern = r'₹?\s*\d+[,\d]*\.?\d*'
        amounts = re.findall(amount_pattern, text)
        info['amounts'] = amounts
        
        return info
    
    @staticmethod
    def calculate_text_quality_score(text, confidence):
        """Calculate overall text quality score"""
        if not text:
            return 0
        
        score = confidence * 0.6  # Base confidence contributes 60%
        
        # Length factor (reasonable length gets bonus)
        length_score = min(len(text) / 100, 1) * 20
        score += length_score
        
        # Character diversity (mixed scripts get bonus for CIV boards)
        devanagari_chars = len(re.findall(r'[\u0900-\u097F]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        digit_chars = len(re.findall(r'[0-9]', text))
        
        if devanagari_chars > 0 and latin_chars > 0:
            score += 10  # Bonus for multilingual content
        
        if digit_chars > 0:
            score += 5   # Bonus for having numbers (common in CIV boards)
        
        return min(score, 100)

class DatabaseUtils:
    @staticmethod
    def get_database_stats():
        """Get database statistics"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            
            # Total records
            total_records = pd.read_sql_query("SELECT COUNT(*) as count FROM civ_extractions", conn).iloc[0]['count']
            
            # Language distribution
            lang_dist = pd.read_sql_query("""
                SELECT detected_language, COUNT(*) as count 
                FROM civ_extractions 
                GROUP BY detected_language
            """, conn)
            
            # Average confidence by engine
            avg_conf = pd.read_sql_query("""
                SELECT ocr_engine, AVG(confidence_score) as avg_confidence 
                FROM civ_extractions 
                GROUP BY ocr_engine
            """, conn)
            
            # Recent activity (last 7 days)
            recent_activity = pd.read_sql_query("""
                SELECT DATE(processing_date) as date, COUNT(*) as count
                FROM civ_extractions 
                WHERE processing_date >= datetime('now', '-7 days')
                GROUP BY DATE(processing_date)
                ORDER BY date
            """, conn)
            
            conn.close()
            
            return {
                'total_records': total_records,
                'language_distribution': lang_dist,
                'average_confidence': avg_conf,
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def update_record(record_id, field, new_value):
        """Update a specific field in a record"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            # Validate field name to prevent SQL injection
            allowed_fields = ['corrected_text', 'translated_text', 'target_language']
            if field not in allowed_fields:
                return False, "Invalid field name"
            
            query = f"UPDATE civ_extractions SET {field} = ? WHERE id = ?"
            cursor.execute(query, (new_value, record_id))
            
            conn.commit()
            conn.close()
            
            return True, "Record updated successfully"
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def delete_record(record_id):
        """Delete a record from database"""
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM civ_extractions WHERE id = ?", (record_id,))
            
            conn.commit()
            conn.close()
            
            return True, "Record deleted successfully"
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def export_to_excel(df, filename=None):
        """Export dataframe to Excel file"""
        if filename is None:
            filename = f"civ_board_exports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main data
                df.to_excel(writer, sheet_name='OCR_Results', index=False)
                
                # Summary statistics
                stats = DatabaseUtils.get_database_stats()
                if 'error' not in stats:
                    stats['language_distribution'].to_excel(writer, sheet_name='Language_Stats', index=False)
                    stats['average_confidence'].to_excel(writer, sheet_name='Confidence_Stats', index=False)
            
            return True, filename
            
        except Exception as e:
            return False, str(e)

class ValidationUtils:
    @staticmethod
    def validate_civ_board_content(text):
        """Validate if text looks like it's from a CIV board"""
        if not text:
            return False, "Empty text"
        
        # Common CIV board indicators
        civ_indicators = [
            r'ग्रा\.?\s*पं\.?',  # Gram Panchayat abbreviation
            r'work\s*id',
            r'कार्य',
            r'विकास',
            r'प्रधान',
            r'\d{4}-\d{2}',  # Financial year pattern
            r'₹\s*\d+',      # Currency
        ]
        
        matches = 0
        for pattern in civ_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        confidence = (matches / len(civ_indicators)) * 100
        
        if confidence >= 30:
            return True, f"Likely CIV board content (confidence: {confidence:.1f}%)"
        else:
            return False, f"May not be CIV board content (confidence: {confidence:.1f}%)"
    
    @staticmethod
    def suggest_corrections(original_text, detected_language):
        """Suggest common corrections based on typical OCR errors"""
        suggestions = []
        
        if detected_language in ["Hindi", "Mixed"]:
            # Common Devanagari OCR corrections
            corrections = {
                'गा. प.': 'ग्रा. पं.',
                'विपणन': 'विकास',
                '२०२३': '2023',
                '२०२४': '2024',
            }
            
            for wrong, correct in corrections.items():
                if wrong in original_text:
                    suggestions.append(f"Consider changing '{wrong}' to '{correct}'")
        
        return suggestions