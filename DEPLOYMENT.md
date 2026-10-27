# 🚀 Free Deployment Guide - CIV Board OCR

## 📋 Overview

This guide shows how to deploy the CIV Board OCR application for **FREE** using popular cloud platforms.

---

## 🎯 Best Free Platforms

### 1. **Streamlit Cloud** (Recommended ⭐)
- **Free Tier**: 1 GB RAM, 1 CPU
- **Best For**: Streamlit apps (easiest)
- **Limitations**: May struggle with heavy OCR models

### 2. **Hugging Face Spaces**
- **Free Tier**: 16 GB RAM, 2 CPUs
- **Best For**: Larger models, better performance
- **Limitations**: Slightly more setup

### 3. **Railway**
- **Free Tier**: 500 hours/month, $5 credit
- **Best For**: Full control
- **Limitations**: Credit runs out eventually

---

## 🌟 Option 1: Streamlit Cloud (EASIEST)

### Prerequisites
- GitHub account
- Your code pushed to GitHub repository

### Step-by-Step Deployment

#### Step 1: Prepare Your Repository

Make sure you have these files in your GitHub repo:
```
Ocr-Challenges/
├── app.py                    # Main application
├── requirements.txt          # Python dependencies
├── packages.txt              # System dependencies (Tesseract)
├── .streamlit/
│   └── config.toml          # Streamlit config
└── README.md
```

#### Step 2: Push to GitHub

```bash
# If not already done
git add .
git commit -m "Prepare for deployment"
git push origin main
```

#### Step 3: Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io/
2. **Sign in** with your GitHub account
3. Click **"New app"**
4. Fill in the form:
   - **Repository**: `YourUsername/Ocr-Challenges`
   - **Branch**: `main` (or `paper`)
   - **Main file path**: `app.py`
5. Click **"Deploy!"**

#### Step 4: Wait for Deployment (5-10 minutes)

Watch the logs for any errors. Common issues:
- **Memory errors**: Comment out heavy models in `requirements.txt`
- **Module not found**: Check `requirements.txt` spelling

#### Step 5: Access Your App

You'll get a URL like: `https://your-app-name.streamlit.app`

### Streamlit Cloud Configuration

If you need to adjust settings, create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
```

---

## 🤗 Option 2: Hugging Face Spaces (More RAM)

### Step-by-Step Deployment

#### Step 1: Create a Hugging Face Account
- Go to: https://huggingface.co/join
- Sign up for free

#### Step 2: Create a New Space

1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name**: `civ-board-ocr`
   - **License**: MIT
   - **Select SDK**: **Streamlit**
   - **Space hardware**: **CPU basic** (free)
4. Click **"Create Space"**

#### Step 3: Upload Your Files

You can either:

**Option A: Git Upload** (Recommended)
```bash
# Clone the space
git clone https://huggingface.co/spaces/YourUsername/civ-board-ocr
cd civ-board-ocr

# Copy your files
cp -r /path/to/Ocr-Challenges/* .

# Push to Hugging Face
git add .
git commit -m "Initial deployment"
git push
```

**Option B: Web Upload**
- Click "Files" tab
- Upload these files:
  - `app.py`
  - `requirements.txt`
  - `packages.txt`
  - All `.py` files (ocr_engines.py, db.py, etc.)
  - `.streamlit/config.toml`

#### Step 4: Create README.md for Space

Hugging Face needs a special README with frontmatter:

```markdown
---
title: CIV Board OCR
emoji: 📝
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
---

# CIV Board OCR Application

Multi-language OCR system for CIV board text extraction.

## Features
- Tesseract OCR
- EasyOCR
- Image preprocessing
- Multiple language support
```

#### Step 5: Wait for Build

- Build logs appear in the "Logs" tab
- Takes 5-15 minutes
- Space becomes public automatically

#### Step 6: Access Your App

URL: `https://huggingface.co/spaces/YourUsername/civ-board-ocr`

---

## 🚂 Option 3: Railway (Advanced)

### Step-by-Step Deployment

#### Step 1: Sign Up
- Go to: https://railway.app/
- Sign in with GitHub

#### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `Ocr-Challenges` repository
4. Railway auto-detects it's a Python app

#### Step 3: Add Environment Variables (if needed)

```
STREAMLIT_SERVER_PORT=8080
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

#### Step 4: Configure Start Command

In Railway dashboard:
- Go to **Settings**
- **Start Command**: `streamlit run app.py --server.port=$PORT`

#### Step 5: Deploy

- Click **"Deploy"**
- Wait 5-10 minutes
- Get your URL: `https://your-app-name.railway.app`

---

## ⚙️ Important Configuration for Free Tier

### Reduce Memory Usage

Edit `requirements.txt` and comment out heavy packages:

```txt
# Heavy models (comment out for free tier)
# surya-ocr>=0.22.0
# chandra-ocr>=0.2.0
# transformers>=5.12.1
```

### Keep Only Essential OCR Engines

For free deployment, use:
- ✅ Tesseract OCR (lightweight, pre-installed)
- ✅ EasyOCR (moderate size, ~300MB)
- ❌ Surya OCR (heavy, ~2GB)
- ❌ Chandra OCR (heavy, requires transformers)

### Optimize `config.py`

```python
# In config.py, reduce memory limits
CLOUD_CONFIG = {
    "max_file_size_mb": 10,  # Reduce from 50
    "enable_caching": True,
    "max_image_dimension": 2048  # Reduce from 4096
}
```

---

## 🐛 Common Deployment Issues

### Issue 1: Memory Limit Exceeded

**Error**: `Killed` or `Out of Memory`

**Solution**:
```bash
# Comment out heavy packages in requirements.txt
# surya-ocr
# chandra-ocr
# transformers
```

### Issue 2: Tesseract Not Found

**Error**: `TesseractNotFoundError`

**Solution**: Add to `packages.txt`:
```
tesseract-ocr
tesseract-ocr-eng
tesseract-ocr-hin
```

### Issue 3: Build Timeout

**Error**: Build takes > 30 minutes

**Solution**:
- Remove unnecessary dependencies
- Use `opencv-python-headless` instead of `opencv-python`
- Pin package versions in `requirements.txt`

### Issue 4: Port Issues (Railway)

**Error**: App not accessible

**Solution**: Use environment variable `$PORT`:
```bash
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## 📊 Platform Comparison

| Feature | Streamlit Cloud | Hugging Face | Railway |
|---------|----------------|--------------|---------|
| **RAM** | 1 GB | 16 GB | 8 GB |
| **Storage** | 1 GB | 50 GB | 5 GB |
| **Build Time** | Fast | Medium | Fast |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Performance** | Basic | Excellent | Good |
| **Free Forever?** | Yes | Yes | $5 credit |
| **Custom Domain** | No | Yes | Yes |

---

## 🎯 Recommended Approach

### For Beginners:
1. Start with **Streamlit Cloud** (easiest)
2. If memory issues → Switch to **Hugging Face Spaces**

### For Production:
1. Use **Hugging Face Spaces** (16GB RAM)
2. Keep heavy models enabled
3. Add authentication if needed

---

## 🔒 Security for Deployment

### Remove Sensitive Files

Make sure `.gitignore` includes:
```
.auth_config.json
*.db
.env
__pycache__/
*.pyc
ocr_env_312/
paddle_env/
```

### Add Authentication (Optional)

If deploying `app_secure.py`:
```python
# In app_secure.py, change default password
DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_in_production")
```

Set environment variable in platform:
- **Streamlit Cloud**: Secrets management
- **Hugging Face**: Settings → Repository secrets
- **Railway**: Environment variables

---

## 📝 Deployment Checklist

Before deploying:

- [ ] Push code to GitHub
- [ ] Test locally: `streamlit run app.py`
- [ ] Check `requirements.txt` (no local paths)
- [ ] Add `packages.txt` for system dependencies
- [ ] Remove `.env` files and secrets
- [ ] Test with smaller images first
- [ ] Monitor memory usage in logs

---

## 🚀 Quick Deploy Commands

### Streamlit Cloud
```bash
# 1. Prepare
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main

# 2. Go to https://share.streamlit.io/ and deploy
```

### Hugging Face
```bash
# 1. Clone space
git clone https://huggingface.co/spaces/USERNAME/SPACE_NAME
cd SPACE_NAME

# 2. Copy files
cp -r ../Ocr-Challenges/* .

# 3. Deploy
git add .
git commit -m "Deploy to HF Spaces"
git push
```

### Railway
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize
railway init

# 4. Deploy
railway up
```

---

## 🆘 Getting Help

### Streamlit Cloud
- Docs: https://docs.streamlit.io/streamlit-community-cloud
- Forum: https://discuss.streamlit.io/

### Hugging Face
- Docs: https://huggingface.co/docs/hub/spaces
- Discord: https://huggingface.co/join/discord

### Railway
- Docs: https://docs.railway.app/
- Discord: https://discord.gg/railway

---

## 📌 Post-Deployment

After successful deployment:

1. **Test all features**: Upload, crop, OCR, translate
2. **Monitor logs**: Check for errors
3. **Share the URL**: With your team
4. **Set up monitoring**: Check uptime
5. **Backup database**: Download `civ_board_ocr.db` regularly

---

## 🎉 You're Live!

Your CIV Board OCR app is now accessible worldwide! 🌍

Share your deployment URL and start extracting text from images!

---

**Created**: January 2025  
**Last Updated**: January 2025  
**Platform Compatibility**: Streamlit Cloud, Hugging Face Spaces, Railway
