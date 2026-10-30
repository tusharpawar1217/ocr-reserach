# CIV Board OCR System

A powerful Streamlit application for extracting, correcting, and translating text from CIV board and document images using multiple OCR engines with automatic language detection.

## 🚀 Live Demo

**Deploy on Hugging Face Spaces (FREE):** https://huggingface.co/spaces

## ✨ Features

- **3 Working OCR Engines**: Tesseract, EasyOCR, Surya OCR (state-of-the-art)
- **Automatic Language Detection**: Intelligent detection of Hindi, English, and Indian languages
- **Interactive Cropping**: Select specific text regions using streamlit-cropper
- **Advanced Preprocessing**: Grayscale → Denoise → CLAHE → Adaptive Threshold
- **Multi-Language Translation**: 4 translation backends with automatic fallback
- **Database Storage**: SQLite database for saving extraction records
- **Custom Dark Theme**: Charcoal (#171717), Forest Green (#06110C), Crimson Red (#A31C18)
- **Extended Format Support**: JPG, PNG, HEIC, SVG, TIFF, WebP

## 🎯 Quick Start

### Option 1: Deploy to Hugging Face Spaces (RECOMMENDED - FREE)

**Why Hugging Face?**
- ✅ **16GB RAM FREE** (vs Streamlit Cloud's 1GB)
- ✅ **All OCR engines work** (Tesseract + EasyOCR + Surya)
- ✅ **Persistent connection** (no sleeping)
- ✅ **Simple deployment** (5 minutes setup)

**Deployment Steps:**

1. **Create Hugging Face Account** (free)
   - Visit: https://huggingface.co/join
   - Sign up with email or GitHub

2. **Create New Space**
   - Go to: https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose:
     - **SDK**: Streamlit
     - **Hardware**: CPU basic (FREE)
     - **Visibility**: Public

3. **Connect GitHub Repository**
   - In Space settings, select "Connect GitHub"
   - Repository: `tusharpawar1217/ocr-reserach`
   - Branch: `main`
   
   OR manually upload files:
   - `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `runtime.txt`
   - All `.py` modules (db.py, config.py, ocr_engines.py, etc.)
   - `.streamlit/config.toml`

4. **Verify Files**
   - Ensure `runtime.txt` contains: `python-3.11.9`
   - Ensure `packages.txt` contains: `libgl1`, `tesseract-ocr`, `tesseract-ocr-hin`, `tesseract-ocr-eng`

5. **Deploy!**
   - Hugging Face will automatically build and deploy
   - Wait 5-10 minutes for first deployment
   - Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`

**Working OCR Engines on HF Spaces:**
- ✅ Tesseract (100+ languages, fast)
- ✅ EasyOCR (80+ languages, good accuracy)
- ✅ Surya OCR (90+ languages, 85.9% accuracy, best quality)

---

### Option 2: Run Locally

```bash
# Clone repository
git clone https://github.com/tusharpawar1217/ocr-reserach.git
cd ocr-reserach

# Create virtual environment
python -m venv ocr_env
source ocr_env/bin/activate  # Linux/Mac
# OR
ocr_env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

App opens at: `http://localhost:8501`

---

## 📋 System Requirements

### For Hugging Face Spaces (Recommended)
- **RAM**: 16GB (provided FREE by HF)
- **Python**: 3.11.9 (specified in runtime.txt)
- **Storage**: 50GB (provided FREE by HF)

### For Local Development
- **Python**: 3.11 or 3.12
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for dependencies
- **Tesseract**: System binary required

---

## 🔧 Configuration

### Files Included

```
ocr-reserach/
├── app.py                    # Main Streamlit app
├── app_secure.py            # Version with authentication
├── requirements.txt         # Python dependencies
├── packages.txt            # System dependencies (Tesseract)
├── runtime.txt            # Python version (3.11.9)
├── config.py              # Configuration
├── db.py                  # Database operations
├── ocr_engines.py         # OCR engine implementations
├── translation.py         # Translation with 4 backends
├── preprocessing.py       # Image preprocessing
├── auth.py               # Authentication (for app_secure.py)
├── manage_users.py       # User management
├── .streamlit/
│   └── config.toml       # Custom dark theme
└── README.md             # This file
```

### Environment Variables (Optional)

For Hugging Face Spaces, add in Settings → Variables:
- `STREAMLIT_SHARING_MODE=true` (disables local-only features)

---

## 🎨 Custom Theme

The application uses a custom dark theme:
- **Background**: Charcoal Black (#171717)
- **Sidebar**: Forest Green (#06110C)
- **Accents**: Crimson Red (#A31C18)
- **Text**: White (#FFFFFF)

Theme is configured in `.streamlit/config.toml`

---

## 🌐 Translation

**4 Translation Backends** (automatic fallback):
1. **Offline Dictionary** - Instant, no rate limits
2. **GoogleTrans** (googletrans 4.0.0rc1) - Primary cloud service
3. **TranslatePy** - Multi-service fallback (Google/Bing/Yandex)
4. **Argos Translate** - Offline neural translation

**Supported Languages:**
English, Hindi, Marathi, Bengali, Gujarati, Tamil, Telugu, Kannada, Malayalam, Punjabi, and 15+ more

---

## 📊 OCR Engines Comparison

| Engine | Languages | Accuracy | Speed | RAM Usage | Best For |
|--------|-----------|----------|-------|-----------|----------|
| **Tesseract** | 100+ | Good | Fast | Low (100MB) | Clean documents |
| **EasyOCR** | 80+ | Better | Medium | Medium (1GB) | Natural scenes |
| **Surya OCR** | 90+ | Best (85.9%) | Slow | High (2-4GB) | Complex layouts |

*Note: PaddleOCR requires Python 3.10 (commented out in requirements.txt)*

---

## 🔐 Authentication (Optional)

Use `app_secure.py` for password-protected deployment:

**Default Credentials:**
- Username: `admin`
- Password: `ocr@2024`

**Change Password:**
```bash
python manage_users.py
```

---

## 🐛 Troubleshooting

### On Hugging Face Spaces

**1. Build Fails**
- Check `requirements.txt` syntax
- Verify `runtime.txt` has: `python-3.11.9`
- Ensure `packages.txt` has: `libgl1` (not libgl1-mesa-glx)

**2. Tesseract Not Found**
- Add to `packages.txt`: `tesseract-ocr`, `tesseract-ocr-hin`, `tesseract-ocr-eng`
- Rebuild space

**3. Out of Memory**
- Surya OCR needs 2-4GB RAM
- HF Spaces FREE tier provides 16GB (sufficient)
- If still issues, disable Surya in `ocr_engines.py`

**4. Translation Fails**
- Network issue: Check HF Space logs
- Rate limited: googletrans/translatepy will auto-fallback
- Offline dictionary always works

### Local Development

**1. Tesseract Not Found**
- Install: `sudo apt install tesseract-ocr tesseract-ocr-hin` (Linux)
- Or download from: https://github.com/UB-Mannheim/tesseract/wiki (Windows)

**2. EasyOCR Installation Fails**
- Use Python 3.11 (not 3.12)
- Install in clean virtual environment

**3. Hindi Text Garbled**
- Install Hindi language pack: `tesseract-ocr-hin`
- Use Auto-Detect language option

---

## 📖 Usage Workflow

1. **Upload Image** → JPG/PNG/HEIC/SVG
2. **Crop Region** → Select text area with interactive tool
3. **Auto-Detect Language** → System detects Hindi/English/other
4. **Choose OCR Engine** → Tesseract (fast) / EasyOCR (balanced) / Surya (best)
5. **Extract Text** → OCR processes with detected language
6. **Correct Text** → Manual editing or auto-correct
7. **Translate** → Optional translation to 15+ languages
8. **Save Record** → Store in SQLite database

---

## 🚦 Deployment Status

- **Streamlit Cloud**: Limited (1GB RAM, only Tesseract + EasyOCR work)
- **Hugging Face Spaces**: ✅ RECOMMENDED (16GB RAM, all engines work)
- **Local**: ✅ Full features

---

## 📞 Support

**Issues?**
1. Check troubleshooting section
2. Review Hugging Face build logs
3. Open GitHub issue: https://github.com/tusharpawar1217/ocr-reserach/issues

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🎯 Next Steps

1. **Deploy to Hugging Face** (5 minutes)
2. **Test all OCR engines** (Tesseract, EasyOCR, Surya)
3. **Try translation** (4 backends with auto-fallback)
4. **Save records** (SQLite database)
5. **Customize theme** (edit .streamlit/config.toml)

**Ready to deploy?** Go to https://huggingface.co/spaces and click "Create new Space"!
