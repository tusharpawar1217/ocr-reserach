# CIV Board OCR System

A Streamlit application for extracting, correcting, and translating text from CIV board and document images using multiple OCR engines with automatic language detection.

## ✅ Quick Status
- **Environment**: `ocr_env_312` (Python 3.12) + `paddle_env` (Python 3.10) virtual environments
- **Dependencies**: All core dependencies installed and working
- **Engines Available**: Tesseract ✅, EasyOCR ✅, PaddleOCR ✅, Surya ✅, Chandra ✅
- **Optional GPU Engines**: GOT-OCR2.0, DeepSeek-OCR (setup scripts provided)
- **App Status**: Ready to run - all features working
- **Language Detection**: ✅ Automatic Hindi/English detection after cropping

## 🆕 Latest Features (v2.0)

### Automatic Language Detection
- **Auto-detect after cropping**: System automatically detects Hindi, English, and other Indian languages
- **Uses pytesseract OSD**: Orientation and Script Detection for accurate language identification
- **Fallback detection**: Heuristic-based detection when OSD fails
- **Manual override**: User can change detected language from dropdown if needed
- **Real-time feedback**: Shows "Auto-Detect (detected: Hindi)" in UI

### 7 OCR Engines Integrated
1. **Tesseract** ✅ - Fast and reliable for clean text
2. **EasyOCR** ✅ - Excellent for natural scenes and multilingual text
3. **PaddleOCR** ✅ - Advanced neural OCR with high accuracy (subprocess via Python 3.10)
4. **Surya OCR** ✅ - State-of-the-art multilingual OCR (85.9% accuracy)
5. **Chandra OCR** ✅ - Advanced document OCR with structure preservation
6. **GOT-OCR2.0** ⚡ - Unified end-to-end OCR (GPU required)
7. **DeepSeek-OCR** ⚡ - High-performance OCR with vLLM (GPU required)

### Unicode Support
- **Full UTF-8 encoding**: Proper handling of Hindi Devanagari characters
- **Fixed encoding errors**: No more "charmap codec" errors
- **Cross-platform support**: Works on Windows, Linux, macOS

## Features

- **Multi-Engine OCR**: Support for 7 OCR engines (5 CPU, 2 GPU-based)
- **Automatic Language Detection**: Intelligent detection of Hindi, English, and Indian languages
- **Interactive Cropping**: Select specific text regions using streamlit-cropper
- **Advanced Preprocessing**: Grayscale → Denoise → CLAHE → Adaptive Threshold
- **Text Correction**: Manual correction interface with auto-correct option
- **Multi-Language Translation**: Support for 15+ Indian and international languages
- **Database Storage**: SQLite database for saving extraction records
- **Records Management**: View, search, and manage saved OCR records
- **Extended Format Support**: JPG, PNG, HEIC, SVG, TIFF, WebP, and more

## Pipeline

1. **Upload** → Upload board/document photo (JPG/PNG/HEIC/SVG/TIFF/WebP)
2. **Crop** → Interactive crop to select text region
3. **Auto-Detect Language** → System automatically detects Hindi, English, or other languages
4. **Preprocess** → Apply image enhancement (optional)
5. **OCR** → Extract text using selected engine with detected language
6. **Correct** → Manual text correction with optional auto-correct
7. **Translate** → Optional translation to 15+ target languages
8. **Save** → Store complete record in database

## Quick Start

### 1. Activate Main Environment (Python 3.12)
```bash
# Windows
ocr_env_312\Scripts\activate

# Linux/macOS
source ocr_env_312/bin/activate
```

### 2. Run the Application
```bash
streamlit run app.py
```

The app will open at: `http://localhost:8501`

### 3. Using PaddleOCR (Python 3.10 subprocess)

PaddleOCR runs automatically in a separate Python 3.10 environment via subprocess:
- **Environment**: `paddle_env\Scripts\python.exe`
- **No manual activation needed** - app handles it automatically
- **UTF-8 encoding** - Proper Hindi text support

## Installation (If Starting Fresh)

### Prerequisites
- **Python 3.12** (for main environment - Tesseract, EasyOCR, Surya, Chandra)
- **Python 3.10** (for PaddleOCR - separate environment)
- **Tesseract OCR binary** (system dependency)

### 1. Create Main Virtual Environment (Python 3.12)

```bash
python -m venv ocr_env_312
```

### 2. Activate Main Environment

**Windows:**
```bash
ocr_env_312\Scripts\activate
```

**Linux/macOS:**
```bash
source ocr_env_312/bin/activate
```

### 3. Install Main Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create PaddleOCR Environment (Python 3.10)

**Windows:**
```bash
# Download Python 3.10 from python.org if not installed
python3.10 -m venv paddle_env
paddle_env\Scripts\activate
pip install paddlepaddle paddleocr
deactivate
```

**Linux/macOS:**
```bash
python3.10 -m venv paddle_env
source paddle_env/bin/activate
pip install paddlepaddle paddleocr
deactivate
```

### 5. Install Tesseract OCR Binary

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH during installation
- Install Hindi language pack: `tesseract-ocr-hin`

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-hin tesseract-ocr-eng tesseract-ocr-mar
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For Hindi and other languages
```

### 6. Optional: Install GPU OCR Engines

**GOT-OCR2.0** (requires CUDA GPU):
```bash
python setup_got_ocr.py
```

**DeepSeek-OCR** (requires CUDA GPU with 16GB+ VRAM):
```bash
python setup_deepseek_ocr.py
```

See `GOT_OCR_SETUP.md` and `OCR_ENGINES_SUMMARY.md` for detailed instructions.

## Usage

### Navigation

- **New Extraction**: Complete OCR pipeline for new images
- **View Records**: Browse and manage saved OCR records

### OCR Engines

1. **Tesseract**: Fast and reliable for clean text, supports 100+ languages
2. **EasyOCR**: Excellent for natural scenes and multilingual text, GPU-accelerated
3. **PaddleOCR**: Advanced neural OCR with high accuracy, runs in Python 3.10 subprocess
4. **Surya OCR**: State-of-the-art multilingual OCR (85.9% olmOCR benchmark)
5. **Chandra OCR**: Advanced document OCR with structure preservation (77.8% accuracy)
6. **GOT-OCR2.0**: Unified end-to-end OCR with layout preservation (GPU only)
7. **DeepSeek-OCR**: High-performance OCR with vLLM support (GPU only, 16GB+ VRAM)

### Automatic Language Detection

The system uses **pytesseract OSD (Orientation and Script Detection)** to automatically identify:
- **Primary detection**: Devanagari → Hindi, Latin → English, Bengali → Bengali, etc.
- **Fallback detection**: Heuristic analysis of non-ASCII character ratio
- **Default fallback**: Hindi (most common for Indian CIV boards)
- **Manual override**: User can change detected language from dropdown

**Supported languages for detection:**
- Hindi, English, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Punjabi, Oriya/Odia, Marathi, Assamese, Nepali, Urdu, Sanskrit

### Supported Languages

**OCR Support:**
- English, Hindi, Marathi, Bengali, Gujarati, Tamil, Telugu, Kannada, Malayalam, Oriya, Punjabi, Assamese, Nepali, Urdu, Sanskrit (engine-dependent)

**Translation Support:**
- All major Indian languages + international languages via deep-translator and argostranslate

## Configuration

### Database

The application uses SQLite by default (`civ_ocr.db`). The database structure supports easy migration to PostgreSQL later.

### File Storage

- **Uploads**: Original images saved to `uploads/` directory
- **Crops**: Cropped regions saved with timestamps
- **Database**: All metadata and text content stored in SQLite

## API Keys

### Translation

The application uses Google Translate via `deep-translator`. No API key required for basic usage, but rate limits may apply for heavy use.

For production use, consider:
1. Google Translate API with authentication
2. Azure Translator Text API
3. Local translation models

## Troubleshooting

### Common Issues

1. **Unicode/Encoding Errors for Hindi Text**
   - ✅ **FIXED**: All subprocess calls use UTF-8 encoding
   - ✅ **FIXED**: PaddleOCR subprocess forces UTF-8 with `io.TextIOWrapper`
   - No more "charmap codec can't encode character" errors

2. **PaddleOCR Installation Issues**
   - Create separate Python 3.10 environment: `python3.10 -m venv paddle_env`
   - PaddleOCR requires Python 3.8-3.11 (not compatible with 3.12+)
   - App automatically runs PaddleOCR in subprocess

3. **Language Detection Not Working**
   - Ensure Tesseract is installed with language packs
   - Install Hindi language data: `tesseract-ocr-hin`
   - Click "Detect Language" button manually if auto-detect fails
   - System defaults to Hindi for CIV boards if detection fails

4. **PaddleOCR Garbled Output**
   - ✅ **FIXED**: System now auto-detects correct language
   - ✅ **FIXED**: Default fallback changed from English to Hindi
   - If still issues, manually select correct language from dropdown

5. **Streamlit API Errors**
   - ✅ **FIXED**: Updated `use_column_width` → `use_container_width`
   - ✅ **FIXED**: Updated `st.experimental_rerun` → `st.rerun`

6. **Tesseract not found**
   - Ensure Tesseract is installed and in PATH
   - Windows: Add `C:\Program Files\Tesseract-OCR` to PATH
   - Restart terminal after installation

7. **EasyOCR/PaddleOCR installation fails**
   - Try installing in clean virtual environment
   - Check Python version compatibility (3.8-3.12)
   - For PaddleOCR, use separate Python 3.10 environment

8. **streamlit-cropper not working**
   - Ensure you're using compatible Streamlit version
   - Try: `pip install streamlit-cropper --force-reinstall`

9. **Low OCR accuracy**
   - Try auto-language detection (default)
   - Manually select correct language if auto-detect fails
   - Use binary threshold for low-quality images
   - Test different OCR engines (Surya, Chandra for complex layouts)

10. **GPU Engines Not Working**
    - GOT-OCR2.0 and DeepSeek-OCR require CUDA GPU
    - Check GPU availability: `nvidia-smi`
    - Ensure CUDA 11.8+ is installed
    - Use setup scripts: `python setup_got_ocr.py` or `python setup_deepseek_ocr.py`

### Performance Tips

1. **Image Quality**: Use high-resolution, well-lit images
2. **Cropping**: Crop tightly around text regions for better accuracy
3. **Preprocessing**: Enable for poor-quality images, disable for clean images
4. **Language Selection**: Use Auto-Detect for intelligent language selection
5. **Engine Selection**: 
   - Tesseract: Clean documents, fast processing
   - EasyOCR: Natural scenes, mixed languages, GPU acceleration
   - PaddleOCR: Complex layouts, high accuracy needed, Hindi text
   - Surya OCR: Multilingual documents, complex layouts, state-of-the-art accuracy
   - Chandra OCR: Document structure preservation, tables, forms
   - GOT-OCR2.0: End-to-end unified OCR, layout preservation (GPU)
   - DeepSeek-OCR: Highest performance, batch processing (GPU, 16GB+ VRAM)

## File Structure

```
civ-board-ocr/
├── app.py                         # Main Streamlit application with auto-detection
├── db.py                          # Database operations
├── preprocessing.py               # Image preprocessing functions
├── ocr_engines.py                # OCR engine implementations (7 engines)
├── translation.py                # Translation functions
├── config.py                     # Configuration settings
├── evaluation_metrics.py         # OCR quality metrics
├── advanced_ocr_pipeline.py      # Advanced OCR processing
├── advanced_color_preprocessing.py # Color-based preprocessing
├── setup_got_ocr.py              # GOT-OCR2.0 installation helper
├── setup_deepseek_ocr.py         # DeepSeek-OCR installation helper
├── GOT_OCR_SETUP.md              # GOT-OCR2.0 setup guide
├── OCR_ENGINES_SUMMARY.md        # Comprehensive OCR engines comparison
├── requirements.txt              # Python dependencies (main environment)
├── README.md                     # This file
├── ocr_env_312/                  # Virtual environment (Python 3.12)
├── paddle_env/                   # PaddleOCR environment (Python 3.10)
├── uploads/                      # Uploaded images storage
└── civ_board_ocr.db             # SQLite database (created on first run)
```

## Database Schema

```sql
CREATE TABLE ocr_records (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id TEXT NOT NULL,                -- Short unique ID (8 chars)
    civ_board_language TEXT,              -- Detected/selected language
    original_image_path TEXT NOT NULL,
    crop_box TEXT NOT NULL,               -- JSON: crop coordinates
    cropped_image_path TEXT NOT NULL,
    engine_used TEXT NOT NULL,            -- tesseract | easyocr | paddleocr | suryaocr | chandraocr | gotocr | deepseekocr
    eocr_pred TEXT,                       -- Raw OCR output (line-by-line)
    ocr_confidence REAL,                  -- Average confidence score
    correction_mode TEXT,                 -- as_is | manual_edit | auto_corrected | reset_to_original
    eocr_corrected TEXT,                  -- Corrected text
    target_language TEXT,                 -- Translation target language
    translated_text TEXT,                 -- Translated text
    created_at TEXT DEFAULT (datetime('now'))
);
```

### Schema Changes (v2.0)
- Added `image_id` - Short unique identifier for each image
- Added `civ_board_language` - Detected or selected language
- Added `correction_mode` - Tracks how text was corrected
- Renamed `raw_extracted_text` → `eocr_pred` (OCR prediction)
- Renamed `corrected_text` → `eocr_corrected` (corrected output)

## Development

### Testing

Run the test suite to verify everything works:
```bash
python test_app.py
```

### Adding New OCR Engines

1. Add engine initialization to `ocr_engines.py`
2. Implement analysis function following existing pattern
3. Update `run_ocr_engine()` function
4. Add engine to availability check

### Adding New Translation Services

1. Add service to `translation.py`
2. Update language mappings
3. Implement translation function
4. Add to UI selection options

## Recent Updates

### v2.0 - Automatic Language Detection & 7 OCR Engines (Current)
- ✅ **Automatic language detection** after image cropping using pytesseract OSD
- ✅ **7 OCR engines integrated**: Tesseract, EasyOCR, PaddleOCR, Surya, Chandra, GOT-OCR2.0, DeepSeek-OCR
- ✅ **Unicode encoding fixed**: Full UTF-8 support for Hindi Devanagari text
- ✅ **PaddleOCR subprocess**: Runs in separate Python 3.10 environment
- ✅ **Language UI improvements**: Shows "Auto-Detect (detected: Hindi)" with manual override
- ✅ **Detection workflow**: Auto-detect → OCR with correct language → Display results
- ✅ **Fallback detection**: Heuristic-based detection when OSD fails
- ✅ **Default to Hindi**: Smart fallback for Indian CIV boards
- ✅ **GPU engine support**: Optional GOT-OCR2.0 and DeepSeek-OCR with setup scripts
- ✅ **Comprehensive documentation**: Added OCR_ENGINES_SUMMARY.md and GOT_OCR_SETUP.md

### v1.1 - Streamlit Compatibility Fix
- ✅ Fixed `use_column_width` → `use_container_width` 
- ✅ Fixed `st.experimental_rerun` → `st.rerun`
- ✅ Added comprehensive test suite
- ✅ Verified compatibility with Streamlit 1.61.1

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Run `python test_app.py` to verify setup
3. Open an issue on GitHub
4. Provide detailed error messages and system information
