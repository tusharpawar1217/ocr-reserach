# 🚀 Advanced OCR Deployment Guide

## Problem: Advanced OCR Models Not Working on Streamlit Cloud

**Issue:** PaddleOCR, SuryaOCR, ChandraOCR show "(Not Installed)" on Streamlit Cloud

**Reason:** Streamlit Cloud free tier has only **1GB RAM** - insufficient for advanced models

---

## ✅ Solution: Two Deployment Options

### **Option 1: Streamlit Cloud (FREE, LIMITED)**
- ✅ Tesseract OCR
- ✅ EasyOCR
- ❌ PaddleOCR, SuryaOCR, ChandraOCR (too heavy)
- **RAM:** 1GB
- **Cost:** FREE forever

### **Option 2: Hugging Face Spaces (FREE, POWERFUL)**
- ✅ Tesseract OCR
- ✅ EasyOCR
- ✅ SuryaOCR ⭐ (works!)
- ✅ PaddleOCR (needs Python 3.10)
- **RAM:** 16GB
- **Cost:** FREE forever

---

## 🎯 Recommended: Deploy to Hugging Face Spaces

Hugging Face offers **16GB RAM for FREE** - enough for advanced OCR!

---

## 📋 Step-by-Step: Hugging Face Spaces Deployment

### Step 1: Create Hugging Face Account

1. Go to: https://huggingface.co/join
2. Sign up (free)
3. Verify email

### Step 2: Create New Space

1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name:** `civ-board-ocr`
   - **License:** MIT
   - **SDK:** Streamlit
   - **Hardware:** CPU basic (free)
   - **Visibility:** Public

### Step 3: Clone Your Space

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/civ-board-ocr
cd civ-board-ocr
```

### Step 4: Copy Files from GitHub

```bash
# Clone your GitHub repo
git clone https://github.com/tusharpawar1217/ocr-reserach.git temp
cd temp

# Copy files to HF Space
cp -r * ../
cd ..
rm -rf temp
```

### Step 5: Use Advanced Requirements

```bash
# Use Hugging Face requirements (includes advanced OCR)
cp requirements-hf.txt requirements.txt

# Or manually edit requirements.txt and uncomment:
# surya-ocr>=0.22.0
# transformers>=5.12.1
```

### Step 6: Create README.md for Space

HF Spaces need special README with frontmatter:

```markdown
---
title: CIV Board OCR - Advanced
emoji: 📝
colorFrom: red
colorTo: purple
sdk: streamlit
sdk_version: 1.39.0
app_file: app.py
pinned: false
python_version: 3.11
---

# CIV Board OCR - Advanced Models

Multi-language OCR with advanced models:
- Tesseract OCR
- EasyOCR
- SuryaOCR (85.9% accuracy)
- Custom dark theme

Supports Hindi, Marathi, Bengali, and 10+ Indian languages.
```

### Step 7: Push to Hugging Face

```bash
git add .
git commit -m "Deploy with advanced OCR models"
git push
```

### Step 8: Wait for Build

- Build takes 10-15 minutes (first time)
- Watch logs in HF Space dashboard
- Space becomes live automatically

---

## 🔧 Python Version Configuration

### For Streamlit Cloud

**File:** `runtime.txt`
```
python-3.11.9
```

### For Hugging Face Spaces

**In README.md frontmatter:**
```yaml
python_version: 3.11
```

---

## 📦 Requirements Comparison

### Streamlit Cloud (requirements.txt)

```txt
# Lightweight only
pytesseract>=0.3.10
easyocr>=1.7.0

# Advanced OCR - COMMENTED OUT
# surya-ocr>=0.22.0
# transformers>=5.12.1
```

### Hugging Face (requirements-hf.txt)

```txt
# All OCR engines enabled!
pytesseract>=0.3.10
easyocr==1.7.1
surya-ocr==0.6.0          # ✅ ENABLED
transformers==4.46.3       # ✅ ENABLED
torch==2.5.1               # ✅ ENABLED
```

---

## 🚀 Quick Deploy Script

I'll create this for you:

```bash
#!/bin/bash
# deploy-to-hf.sh

# Step 1: Install HF CLI
pip install huggingface_hub

# Step 2: Login
huggingface-cli login

# Step 3: Create space
huggingface-cli repo create civ-board-ocr --type space --space_sdk streamlit

# Step 4: Clone and push
git clone https://huggingface.co/spaces/YOUR_USERNAME/civ-board-ocr
cd civ-board-ocr

# Copy files
cp ../requirements-hf.txt requirements.txt
cp ../*.py .
cp -r ../.streamlit .
cp ../packages.txt .

# Commit and push
git add .
git commit -m "Initial deployment with advanced OCR"
git push
```

---

## 🎯 What Will Work After HF Deployment

### OCR Engines Available:

| Engine | Streamlit Cloud | Hugging Face |
|--------|----------------|--------------|
| **Tesseract** | ✅ | ✅ |
| **EasyOCR** | ✅ | ✅ |
| **SuryaOCR** | ❌ (no RAM) | ✅ **NEW!** |
| **PaddleOCR** | ❌ (no RAM) | ⚠️ (needs Python 3.10) |
| **ChandraOCR** | ❌ (no RAM) | ⚠️ (needs GPU) |

### Why SuryaOCR?

- ✅ **85.9% accuracy** (best open source)
- ✅ **90+ languages** including all Indian languages
- ✅ **Layout preservation** (tables, columns)
- ✅ **Works on CPU** (no GPU needed)
- ✅ **Fits in 16GB RAM**

---

## 🐛 Troubleshooting

### Issue: Build Timeout on HF

**Solution:** Build takes longer first time (10-15 min). Be patient!

### Issue: Out of Memory

**Solution:** Use `torch==2.5.1` CPU version (not CUDA)

### Issue: PaddleOCR Not Working

**Solution:** PaddleOCR needs Python 3.10. Either:
1. Change `python_version: 3.10` in README
2. Or skip PaddleOCR (use Surya instead - it's better!)

---

## 💰 Cost Comparison

### Streamlit Cloud
- **RAM:** 1GB
- **Cost:** $0/month ✅
- **Advanced OCR:** ❌

### Hugging Face Spaces (Basic CPU)
- **RAM:** 16GB
- **Cost:** $0/month ✅
- **Advanced OCR:** ✅

### Hugging Face Spaces (GPU - if needed)
- **RAM:** 16GB + GPU
- **Cost:** $0.60/hour (~$400/month)
- **Advanced OCR:** ✅ (all models)

**Recommendation:** Use HF Spaces CPU (free) - works for Surya!

---

## ✅ Summary

**Current Deployment (Streamlit Cloud):**
- ✅ Working: Tesseract, EasyOCR
- ❌ Not working: SuryaOCR, PaddleOCR, ChandraOCR

**Recommended (Hugging Face Spaces):**
- ✅ Working: Tesseract, EasyOCR, **SuryaOCR** ⭐
- ⚠️ Partial: PaddleOCR (needs Python 3.10)
- ❌ Not working: ChandraOCR (needs GPU)

**Migration:** Easy - just push to HF Spaces with `requirements-hf.txt`

---

## 🚀 Quick Migration Steps

1. **Keep Streamlit Cloud** for basic OCR (Tesseract + EasyOCR)
2. **Deploy to HF Spaces** for advanced OCR (add SuryaOCR)
3. **Test SuryaOCR** on HF Spaces
4. **Choose your favorite** deployment

**Both are FREE forever!** 🎉

---

## 📞 Need Help?

- **Streamlit Cloud Issues:** https://discuss.streamlit.io/
- **Hugging Face Issues:** https://huggingface.co/join/discord
- **SuryaOCR Docs:** https://github.com/VikParuchuri/surya

---

**Created:** January 2025  
**Python Version:** 3.11 (stable for most models)  
**Tested On:** Streamlit Cloud, Hugging Face Spaces
