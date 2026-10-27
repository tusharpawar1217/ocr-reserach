"""
Configuration settings for CIV Board OCR Application
"""

import pytesseract

# Tesseract OCR binary path (Windows)
TESSERACT_PATH = r"C:\Users\pawar\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Database settings
DATABASE_NAME = "civ_board_ocr.db"

# OCR settings
TESSERACT_CONFIG = {
    'oem': 3,  # OCR Engine Mode
    'psm': 6,  # Page Segmentation Mode
    'languages': 'hin+eng+mar'  # Hindi, English, Marathi
}

# Image processing settings
IMAGE_PROCESSING = {
    'min_resolution': (600, 400),
    'max_file_size_mb': 10,
    'supported_formats': ['png', 'jpg', 'jpeg'],
    'preprocessing': {
        'denoise': True,
        'adaptive_threshold': True,
        'resize_small_images': True,
        'target_size': 800
    }
}

# Language detection settings
LANGUAGE_DETECTION = {
    'devanagari_threshold': 0.3,  # Minimum ratio for Hindi/Marathi detection
    'latin_threshold': 0.5,       # Minimum ratio for English detection
    'mixed_threshold': 0.1        # Threshold for mixed language detection
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'tesseract_min': 0,
    'easyocr_min': 0.1,
    'good_quality': 70,
    'excellent_quality': 90
}

# Translation settings
TRANSLATION = {
    'supported_languages': {
        'Hindi': 'hi',
        'English': 'en',
        'Marathi': 'mr',
        'Telugu': 'te',
        'Tamil': 'ta',
        'Gujarati': 'gu',
        'Bengali': 'bn'
    },
    'max_text_length': 5000
}

# UI settings
UI_CONFIG = {
    'page_title': "CIV Board OCR System",
    'page_icon': "📋",
    'layout': "wide",
    'sidebar_width': 300,
    'max_upload_size_mb': 10
}

# Batch processing settings
BATCH_PROCESSING = {
    'max_files': 50,
    'progress_update_interval': 1,
    'auto_save': True
}