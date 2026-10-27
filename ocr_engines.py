"""
OCR Engine functions with caching for Streamlit
Extracted and refactored from the SimpleOCRAnalyzer notebook
Version: 1.1 - Fixed path handling for Windows subprocess
"""

import os
import time
import shutil
import importlib.util
import numpy as np
import pytesseract
import streamlit as st
from typing import Dict, Any, Optional

# Import config to set tesseract path
import config

# Import line clustering module
from line_clustering import (
    words_from_tesseract, words_from_easyocr,
    cluster_words_into_lines
)

# Optional imports with fallback
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Check for Chandra OCR availability
CHANDRA_OCR_AVAILABLE = False
try:
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from chandra.model.hf import generate_hf
    from chandra.model.schema import BatchInputItem
    from bs4 import BeautifulSoup
    import torch
    CHANDRA_OCR_AVAILABLE = True
except ImportError:
    CHANDRA_OCR_AVAILABLE = False

# PaddleOCR runs in a separate Python 3.10 environment via subprocess
# Check if the paddle_env environment exists
PADDLEOCR_AVAILABLE = False
try:
    paddle_env_path = r"C:\Users\pawar\OneDrive\Desktop\ISRO\Ocr-Challenges\paddle_env\Scripts\python.exe"
    PADDLEOCR_AVAILABLE = os.path.exists(paddle_env_path)
except Exception:
    PADDLEOCR_AVAILABLE = False

# Check for runtime dependencies required by advanced OCR engines
ACCELERATE_AVAILABLE = False
try:
    import accelerate
    ACCELERATE_AVAILABLE = True
except Exception:
    ACCELERATE_AVAILABLE = False

def _docker_daemon_available() -> bool:
    """Return True only if Docker is installed and the daemon is reachable."""
    docker = shutil.which("docker")
    if not docker:
        return False
    try:
        result = __import__("subprocess").run(
            [docker, "info"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return result.returncode == 0
    except Exception:
        return False


def _vllm_server_available(url: str = "http://localhost:8000/v1/models") -> bool:
    """Return True when a local Chandra vLLM server is reachable."""
    try:
        import requests
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def _transformers_supports_qwen3_5() -> bool:
    """Check whether the installed Transformers build registers the qwen3_5 architecture."""
    try:
        from transformers import AutoConfig

        model_type_map = getattr(AutoConfig, "_model_type_to_module_name", None)
        if model_type_map is not None:
            return "qwen3_5" in model_type_map

        from transformers.models.auto.configuration_auto import CONFIG_MAPPING
        return "qwen3_5" in CONFIG_MAPPING
    except Exception:
        return False

# Surya OCR needs a runnable backend. On Windows this can be either Docker-based
# vLLM or a local llama.cpp binary; if neither is present, the engine cannot start.
SURYAOCR_AVAILABLE = False
try:
    spec = importlib.util.find_spec("surya")
    SURYAOCR_AVAILABLE = spec is not None and (
        _docker_daemon_available() or shutil.which("llama-server") is not None
    )
except Exception:
    SURYAOCR_AVAILABLE = False

# Chandra OCR works in two ways:
# 1) with a local vLLM server (recommended / simplest), or
# 2) with the Hugging Face backend only if the installed transformers build
#    actually registers the qwen3_5 architecture.
CHANDRAOCR_AVAILABLE = False
try:
    spec = importlib.util.find_spec("chandra")
    CHANDRAOCR_AVAILABLE = spec is not None and (
        _vllm_server_available() or (ACCELERATE_AVAILABLE and _transformers_supports_qwen3_5())
    )
except Exception:
    CHANDRAOCR_AVAILABLE = False

# Check for GOT-OCR2.0 availability (runs in separate conda environment)
GOTOCR_AVAILABLE = False
try:
    # Check if GOT-OCR2.0 conda environment exists
    got_demo_path = r"GOT-OCR2.0\GOT\demo\run_ocr_2.0.py"
    got_weights_path = r"C:\GOT_weights"
    GOTOCR_AVAILABLE = os.path.exists(got_demo_path) and os.path.exists(got_weights_path)
except Exception:
    GOTOCR_AVAILABLE = False

# Check for DeepSeek-OCR availability (runs in separate conda environment)
DEEPSEEKOCR_AVAILABLE = False
try:
    # Check if DeepSeek-OCR conda environment and scripts exist
    deepseek_demo_path = r"DeepSeek-OCR\DeepSeek-OCR-hf\run_dpsk_ocr.py"
    DEEPSEEKOCR_AVAILABLE = os.path.exists(deepseek_demo_path)
except Exception:
    DEEPSEEKOCR_AVAILABLE = False

# Check for IndicPhotoOCR availability
INDICPHOTOOCR_AVAILABLE = False
try:
    from IndicPhotoOCR.ocr import OCR as IndicOCR
    INDICPHOTOOCR_AVAILABLE = True
except ImportError:
    INDICPHOTOOCR_AVAILABLE = False

@st.cache_resource
def get_easyocr_reader(languages=("en", "hi"), use_gpu=False):
    """
    Initialize and cache EasyOCR reader with comprehensive Indian language support
    """
    if not EASYOCR_AVAILABLE:
        raise ImportError("EasyOCR is not installed. Install with: pip install easyocr")
    
    try:
        # Comprehensive list of languages supported by EasyOCR for Indian scripts
        # Updated to include all available Indian languages
        supported_langs = {
            # Core languages with strong support
            'en': 'English',
            'hi': 'Hindi (Devanagari)',
            'mr': 'Marathi (Devanagari)', 
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'or': 'Oriya/Odia',
            'pa': 'Punjabi (Gurmukhi)',
            'as': 'Assamese',
            'ne': 'Nepali',
            
            # Additional supported languages
            'ur': 'Urdu',
            'sa': 'Sanskrit (Devanagari)'
        }
        
        # Validate languages
        valid_langs = []
        for lang in languages:
            if lang in supported_langs:
                valid_langs.append(lang)
        
        if not valid_langs:
            valid_langs = ['en', 'hi']  # Default fallback
        
        # Initialize reader with caching
        reader = easyocr.Reader(valid_langs, gpu=use_gpu, verbose=False)
        return reader, supported_langs
        
    except Exception as e:
        st.error(f"Failed to initialize EasyOCR: {str(e)}")
        return None, {}

@st.cache_resource  
def get_paddleocr_reader(languages=['en', 'hi'], use_gpu=False):
    """
    Initialize and cache PaddleOCR reader 
    """
    if not PADDLEOCR_AVAILABLE:
        return None, {}
    
    try:
        # Import PaddleOCR only when needed to avoid reinitialization errors
        from paddleocr import PaddleOCR
        
        # PaddleOCR language mapping
        paddle_langs = {
            'en': 'English',
            'hi': 'Hindi (Devanagari)',
            'mr': 'Marathi',
            'bn': 'Bengali', 
            'gu': 'Gujarati',
            'ta': 'Tamil',
            'te': 'Telugu',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'or': 'Oriya/Odia',
            'pa': 'Punjabi',
            'ur': 'Urdu'
        }
        
        # PaddleOCR supports multi-language in a single model
        # Use 'ch' for Chinese model which includes many Asian languages
        # or 'en' for English model
        lang_code = 'en' if 'en' in languages else 'ch'
        
        # Initialize PaddleOCR (show_log parameter removed - not supported in newer versions)
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang_code,
            use_gpu=use_gpu
        )
        
        return ocr, paddle_langs
        
    except Exception as e:
        st.warning(f"PaddleOCR initialization failed: {str(e)}")
        return None, {}

def get_available_engines():
    """
    Check which OCR engines are available
    Returns dict mapping engine names to availability status
    """
    availability = {
        "tesseract": False,
        "easyocr": EASYOCR_AVAILABLE,
        "paddleocr": PADDLEOCR_AVAILABLE,
        "suryaocr": SURYAOCR_AVAILABLE,
        "chandraocr": CHANDRAOCR_AVAILABLE,
        "gotocr": GOTOCR_AVAILABLE,
        "deepseekocr": DEEPSEEKOCR_AVAILABLE,
        "indicphotoocr": INDICPHOTOOCR_AVAILABLE
    }
    
    # Check Tesseract availability
    try:
        pytesseract.get_tesseract_version()
        availability["tesseract"] = True
    except Exception:
        availability["tesseract"] = False
    
    return availability

def tesseract_ocr(image_np: np.ndarray, config: str = '--psm 6', languages: str = 'eng+hin') -> Dict[str, Any]:
    """
    Perform OCR using Tesseract with timing and error handling
    """
    try:
        start_time = time.time()
        
        # Configure language string for Tesseract
        # Map common language codes to Tesseract format
        lang_mapping = {
            'en': 'eng', 'eng': 'eng',
            'hi': 'hin', 'hin': 'hin',
            'mr': 'mar', 'mar': 'mar',
            'bn': 'ben', 'ben': 'ben',
            'gu': 'guj', 'guj': 'guj',
            'ta': 'tam', 'tam': 'tam',
            'te': 'tel', 'tel': 'tel',
            'kn': 'kan', 'kan': 'kan',
            'ml': 'mal', 'mal': 'mal',
            'or': 'ori', 'ori': 'ori',
            'pa': 'pan', 'pan': 'pan',
            'as': 'asm', 'asm': 'asm',
            'ne': 'nep', 'nep': 'nep',
            'ur': 'urd', 'urd': 'urd'
        }
        
        # Process languages parameter if it's not already in Tesseract format
        if '+' not in languages:
            # Single language
            tesseract_lang = lang_mapping.get(languages, 'eng')
        else:
            # Multiple languages - convert each
            lang_list = languages.split('+')
            converted_langs = []
            for lang in lang_list:
                converted_langs.append(lang_mapping.get(lang.strip(), lang.strip()))
            tesseract_lang = '+'.join(converted_langs)
        
        # Perform OCR with line clustering
        # Get word boxes and cluster them geometrically
        words = words_from_tesseract(image_np, lang=tesseract_lang)
        lines = cluster_words_into_lines(words, y_tolerance_ratio=0.6)
        text = '\n'.join(lines)
        
        # Get confidence scores
        try:
            data = pytesseract.image_to_data(
                image_np,
                config=config,
                lang=tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
        except Exception:
            avg_confidence = 0
        
        processing_time = time.time() - start_time
        
        return {
            'engine': 'Tesseract',
            'text': text.strip(),
            'confidence': avg_confidence,
            'processing_time': processing_time,
            'languages_used': tesseract_lang,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        return {
            'engine': 'Tesseract',
            'text': '',
            'confidence': 0,
            'processing_time': 0,
            'languages_used': languages,
            'success': False,
            'error': str(e)
        }
        
def easyocr_ocr(image_path: str, languages=("en", "hi"), use_gpu=False) -> Dict[str, Any]:
    """
    Perform OCR using EasyOCR with timing and error handling
    """
    try:
        if not EASYOCR_AVAILABLE:
            return {
                'engine': 'EasyOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'EasyOCR not installed'
            }

        start_time = time.time()
        
        # Get cached reader
        reader, supported_langs = get_easyocr_reader(languages, use_gpu)
        if reader is None:
            return {
                'engine': 'EasyOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Failed to initialize EasyOCR reader'
            }
        
        # Perform OCR - returns list of (bbox, text, confidence)
        results = reader.readtext(str(image_path))
        
        # Use line clustering instead of simple sorting
        words = words_from_easyocr(results)
        lines = cluster_words_into_lines(words, y_tolerance_ratio=0.6)
        full_text = '\n'.join(lines)
        
        # Extract confidences for average calculation
        confidences = [conf * 100 for bbox, text, conf in results if text.strip()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        processing_time = time.time() - start_time
        
        return {
            'engine': 'EasyOCR',
            'text': full_text,
            'confidence': round(avg_confidence, 2),
            'processing_time': round(processing_time, 3),
            'languages_used': '+'.join(languages),
            'line_count': len(lines),
            'success': True,
            'error': None
        }
        
    except Exception as e:
        return {
            'engine': 'EasyOCR',
            'text': '',
            'confidence': 0,
            'processing_time': 0,
            'languages_used': '+'.join(languages) if languages else 'unknown',
            'success': False,
            'error': str(e)
        }

def paddleocr_ocr(image_input, languages=['en'], use_gpu=False) -> Dict[str, Any]:
    """
    Perform OCR using PaddleOCR with timing and error handling
    Uses separate 'env' virtual environment via subprocess
    """
    try:
        import subprocess
        import json
        import tempfile
        import os
        
        start_time = time.time()
        
        # Save image to temporary file
        temp_image_path = None
        if isinstance(image_input, str):
            # Convert to absolute path if relative
            temp_image_path = os.path.abspath(image_input)
        else:
            # Save numpy array as image
            from PIL import Image
            img = Image.fromarray(image_input)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                temp_image_path = os.path.abspath(tmp.name)
        
        # Path to PaddleOCR environment Python (Python 3.10)
        paddle_env_python = r"C:\Users\pawar\OneDrive\Desktop\ISRO\Ocr-Challenges\paddle_env\Scripts\python.exe"
        
        # Check if env exists
        if not os.path.exists(paddle_env_python):
            return {
                'engine': 'PaddleOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': f'PaddleOCR environment not found at: {paddle_env_python}'
            }
        
        primary_lang = languages[0] if languages else 'en'
        
        # Normalize path and escape backslashes for Windows
        temp_image_path_escaped = temp_image_path.replace('\\', '\\\\')
        
        # Create Python script to run in subprocess using PaddleOCR 3.x API
        script_code = f'''
import sys
import json
import io
import numpy as np
from dataclasses import dataclass
from typing import List

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from paddleocr import PaddleOCR

@dataclass
class WordBox:
    text: str
    left: float
    top: float
    width: float
    height: float
    conf: float

    @property
    def y_center(self) -> float:
        return self.top + self.height / 2

    @property
    def x_left(self) -> float:
        return self.left

def cluster_words_into_lines(words: List[WordBox], y_tolerance_ratio: float = 0.6) -> tuple:
    """
    Group word boxes into visual lines by y_center proximity, then sort each
    line left-to-right by x. Returns (lines, confidences).
    """
    if not words:
        return [], []
    
    # sort by vertical position first
    words = sorted(words, key=lambda w: w.y_center)
    
    lines_list = []
    current_line = [words[0]]
    current_y = words[0].y_center
    current_h = words[0].height
    
    for w in words[1:]:
        tolerance = current_h * y_tolerance_ratio
        if abs(w.y_center - current_y) <= tolerance:
            current_line.append(w)
            # update running average so tolerance adapts as we go down the line
            current_y = np.mean([x.y_center for x in current_line])
            current_h = np.mean([x.height for x in current_line])
        else:
            lines_list.append(current_line)
            current_line = [w]
            current_y = w.y_center
            current_h = w.height
    
    lines_list.append(current_line)
    
    # left-to-right order within each line, then join into text
    joined_lines = []
    all_confidences = []
    for line in lines_list:
        line_sorted = sorted(line, key=lambda w: w.x_left)
        line_text = " ".join(w.text for w in line_sorted if w.text.strip())
        if line_text.strip():
            joined_lines.append(line_text)
            # Average confidence for this line
            line_confs = [w.conf for w in line_sorted if w.text.strip()]
            if line_confs:
                all_confidences.append(sum(line_confs) / len(line_confs))
    
    return joined_lines, all_confidences

try:
    # Initialize PaddleOCR with new 3.x parameters
    # Language: {primary_lang}
    ocr = PaddleOCR(
        use_textline_orientation=True,
        lang="{primary_lang}",
        enable_mkldnn=False
    )
    
    # Use predict() method (new in 3.x)
    results = list(ocr.predict("{temp_image_path_escaped}"))
    
    word_boxes = []
    
    if results:
        res = results[0]
        
        # Handle dictionary structure (PaddleOCR 3.x format)
        if isinstance(res, dict) and "rec_texts" in res:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            boxes = res.get("dt_polys", [])
            
            for i, (text, score) in enumerate(zip(texts, scores)):
                if text.strip() and i < len(boxes):
                    bbox = boxes[i]
                    xs = [p[0] for p in bbox]
                    ys = [p[1] for p in bbox]
                    word_boxes.append(WordBox(
                        text=text.strip(),
                        left=min(xs),
                        top=min(ys),
                        width=max(xs) - min(xs),
                        height=max(ys) - min(ys),
                        conf=score
                    ))
        
        # Fallback for list structure (older format)
        elif isinstance(res, list):
            for item in res:
                if isinstance(item, list) and len(item) == 2:
                    bbox, (text, score) = item
                    if text.strip():
                        xs = [p[0] for p in bbox]
                        ys = [p[1] for p in bbox]
                        word_boxes.append(WordBox(
                            text=text.strip(),
                            left=min(xs),
                            top=min(ys),
                            width=max(xs) - min(xs),
                            height=max(ys) - min(ys),
                            conf=score
                        ))
    
    # Apply line clustering
    text_lines, confidences = cluster_words_into_lines(word_boxes, y_tolerance_ratio=0.6)
    
    full_text = "\\n".join(text_lines)
    avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 0
    
    output = {{
        "text": full_text,
        "confidence": round(avg_confidence, 2),
        "line_count": len(text_lines),
        "language_used": "{primary_lang}",
        "success": True,
        "error": None
    }}
    print(json.dumps(output, ensure_ascii=False))
except Exception as e:
    import traceback
    output = {{
        "text": "",
        "confidence": 0,
        "line_count": 0,
        "language_used": "{primary_lang}",
        "success": False,
        "error": str(e) + "\\n" + traceback.format_exc()
    }}
    print(json.dumps(output, ensure_ascii=False))
'''
        
        # Run subprocess with increased timeout for model download on first run
        # Force UTF-8 encoding for Hindi text
        result = subprocess.run(
            [paddle_env_python, '-c', script_code],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=300  # 5 minutes for first-time model download
        )
        
        # Clean up temp file if we created one
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
        if result.returncode != 0:
            return {
                'engine': 'PaddleOCR',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'success': False,
                'error': f'Subprocess error: {result.stderr}'
            }
        
        # Parse JSON output
        output = json.loads(result.stdout.strip())
        processing_time = time.time() - start_time
        
        return {
            'engine': 'PaddleOCR',
            'text': output.get('text', ''),
            'confidence': output.get('confidence', 0),
            'processing_time': round(processing_time, 3),
            'languages_used': output.get('language_used', primary_lang),
            'line_count': output.get('line_count', 0),
            'success': output.get('success', True),
            'error': output.get('error')
        }
        
    except subprocess.TimeoutExpired:
        # Clean up temp file on timeout
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
            except:
                pass
        return {
            'engine': 'PaddleOCR',
            'text': '',
            'confidence': 0,
            'processing_time': 300,
            'success': False,
            'error': 'PaddleOCR timeout (300s). First run may take longer due to model download. Please try again.'
        }
    except Exception as e:
        return {
            'engine': 'PaddleOCR',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time,
            'languages_used': '+'.join(languages) if languages else 'unknown',
            'success': False,
            'error': str(e)
        }

# Global Chandra model cache
_chandra_model = None
_chandra_processor = None

def chandra_ocr(image_input, model_path: str = None, use_gpu: bool = True) -> Dict[str, Any]:
    """
    Perform OCR using Chandra OCR model (offline mode)
    
    Args:
        image_input: PIL Image, numpy array, or file path
        model_path: Path to Chandra model directory (default: searches common locations)
        use_gpu: Use GPU if available (automatically detects)
    
    Returns:
        Dict with OCR results including HTML and markdown text
    """
    global _chandra_model, _chandra_processor
    
    try:
        if not CHANDRA_OCR_AVAILABLE:
            return {
                'engine': 'Chandra OCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Chandra OCR dependencies not installed. Install: transformers, torch, chandra, beautifulsoup4'
            }
        
        start_time = time.time()
        
        # Set offline mode
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        # Find model path if not provided
        if model_path is None:
            # Search common locations
            search_paths = [
                r"C:\Models\chandra-ocr-2",
                r"C:\Users\pawar\Models\chandra-ocr-2",
                r"./models/chandra-ocr-2",
                r"../models/chandra-ocr-2"
            ]
            for path in search_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                return {
                    'engine': 'Chandra OCR',
                    'text': '',
                    'confidence': 0,
                    'processing_time': 0,
                    'success': False,
                    'error': 'Chandra model not found. Please specify model_path or place model in C:\\Models\\chandra-ocr-2'
                }
        
        # Check if model exists
        if not os.path.exists(model_path):
            return {
                'engine': 'Chandra OCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': f'Chandra model not found at: {model_path}'
            }
        
        # Load model and processor (cached)
        if _chandra_model is None or _chandra_processor is None:
            _chandra_processor = AutoProcessor.from_pretrained(
                model_path,
                local_files_only=True
            )
            
            _chandra_model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto" if use_gpu and torch.cuda.is_available() else "cpu",
                local_files_only=True
            )
            
            _chandra_model.eval()
            _chandra_model.processor = _chandra_processor
        
        # Convert image input to PIL Image
        from PIL import Image as PILImage
        
        if isinstance(image_input, str):
            # File path
            image = PILImage.open(image_input)
        elif isinstance(image_input, np.ndarray):
            # Numpy array
            image = PILImage.fromarray(image_input)
        else:
            # Assume already PIL Image
            image = image_input
        
        # Prepare batch input
        batch = [
            BatchInputItem(
                image=image,
                prompt_type="ocr_layout"
            )
        ]
        
        # Run OCR
        result = generate_hf(batch, _chandra_model)[0]
        html_output = result.raw
        
        # Extract markdown text from HTML using BeautifulSoup
        soup = BeautifulSoup(html_output, "html.parser")
        markdown_lines = []
        
        # Extract paragraphs
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                markdown_lines.append(text)
        
        # Extract list items
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if text:
                markdown_lines.append(text)
        
        # Convert to markdown
        markdown_text = "\n\n".join(markdown_lines)
        
        processing_time = time.time() - start_time
        
        # Count lines
        line_count = len([line for line in markdown_text.split('\n') if line.strip()])
        
        return {
            'engine': 'Chandra OCR',
            'text': markdown_text,
            'html': html_output,
            'confidence': 95.0,  # Chandra doesn't provide confidence, use high default
            'processing_time': round(processing_time, 3),
            'languages_used': 'multilingual',
            'line_count': line_count,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        return {
            'engine': 'Chandra OCR',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time if 'start_time' in locals() else 0,
            'languages_used': 'multilingual',
            'success': False,
            'error': str(e)
        }

# ---------------------------------------------------------------------------
# IndicPhotoOCR Engine
# ---------------------------------------------------------------------------

# Global cache for IndicPhotoOCR model instance
_indic_photo_ocr_model = None

@st.cache_resource
def get_indic_photo_ocr_model(use_gpu: bool = True):
    """
    Initialize and cache IndicPhotoOCR model
    The model weights are automatically downloaded on first run if not cached
    """
    global _indic_photo_ocr_model
    
    if not INDICPHOTOOCR_AVAILABLE:
        return None
    
    if _indic_photo_ocr_model is None:
        print("Initializing IndicPhotoOCR model (this may take a few seconds)...")
        
        
        # Determine device
        device = "cuda:0" if use_gpu and torch.cuda.is_available() else "cpu"
        
        # Initialize model (auto-downloads weights if needed)
        # _indic_photo_ocr_model = from IndicPhotoOCR.ocr import OCR as IndicOCR
    
    return _indic_photo_ocr_model


def indic_photo_ocr(image_input, use_gpu: bool = True) -> Dict[str, Any]:
    """
    Perform OCR using IndicPhotoOCR engine
    
    IndicPhotoOCR is optimized for Indian language documents and photos.
    It handles multilingual content with support for all major Indian scripts.
    
    Args:
        image_input: PIL Image, numpy array, or file path
        use_gpu: Use GPU if available (default: True)
    
    Returns:
        Dict with OCR results including text, confidence, and processing time
    """
    try:
        # if not INDICPHOTOOCR_AVAILABLE:
        #     return {
        #         'engine': 'IndicPhotoOCR',
        #         'text': '',
        #         'confidence': 0,
        #         'processing_time': 0,
        #         'success': False,
        #         'error': 'IndicPhotoOCR not installed. Install with: pip install IndicPhotoOCR'
        #     }
        from IndicPhotoOCR.ocr import OCR as IndicOCR

        start_time = time.time()
        
        # Get cached model
        device = "cuda:0" if use_gpu and torch.cuda.is_available() else "cpu"
        ocr_model = IndicOCR(verbose=False, device=device)

        if ocr_model is None:
            return {
                'engine': 'IndicPhotoOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Failed to initialize IndicPhotoOCR model'
            }
        
        # Convert image input to appropriate format
        from PIL import Image as PILImage
        
        if isinstance(image_input, str):
            # File path - IndicPhotoOCR can work with file paths directly
            image_path = image_input
            image = PILImage.open(image_path)
        elif isinstance(image_input, np.ndarray):
            # Numpy array - convert to PIL
            image = PILImage.fromarray(image_input)
            # Save to temporary file for IndicPhotoOCR
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(tmp.name)
                image_path = tmp.name
        else:
            # Assume already PIL Image
            image = image_input
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                image.save(tmp.name)
                image_path = tmp.name
        
        # Run OCR using IndicPhotoOCR
        # The OCR model returns text output
        extracted_text = ocr_model.ocr(image_path)
        extracted_text_merged = [" ".join(line) for line in extracted_text]
        extracted_text_merged_m = "\n".join(extracted_text_merged)
        # print(f"IndicPhotoOCR extracted {(extracted_text_merged_m)} lines.")
        processing_time = time.time() - start_time
        
        # Count lines
        line_count = len(extracted_text)
        
        # IndicPhotoOCR doesn't provide confidence scores, use a high default
        confidence = 90.0
        
        return {
            'engine': 'IndicPhotoOCR',
            'text': extracted_text_merged_m,
            'confidence': confidence,
            'processing_time': round(processing_time, 3),
            'languages_used': 'multilingual (Indic)',
            'line_count': line_count,
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"IndicPhotoOCR error: {str(e)}")
        return {
            'engine': 'IndicPhotoOCR',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time if 'start_time' in locals() else 0,
            'languages_used': 'multilingual (Indic)',
            'success': False,
            'error': f"IndicPhotoOCR error: {str(e)}"
        }

def run_ocr_engine(engine_name: str, image_input, language_code: str = "eng+hin", **kwargs) -> Dict[str, Any]:
    """
    Run the specified OCR engine on the image with language support
    Models are cached and reused across requests for optimal performance
    """
    engine_name = engine_name.lower().replace(" ", "").replace("(", "").replace(")", "")
    
    if "notinstalled" in engine_name:
        engine_name = engine_name.replace("notinstalled", "")
    
    if engine_name == "tesseract":
        return tesseract_ocr(image_input, config=kwargs.get('config', '--psm 6'), languages=language_code)
    
    elif engine_name == "easyocr":
        # Convert language codes for EasyOCR
        lang_map = {
            'eng': 'en', 'hin': 'hi', 'mar': 'mr', 'ben': 'bn', 'guj': 'gu',
            'tam': 'ta', 'tel': 'te', 'kan': 'kn', 'mal': 'ml', 'ori': 'or',
            'pan': 'pa', 'asm': 'as', 'nep': 'ne', 'urd': 'ur', 'san': 'sa'
        }
        
        if '+' in language_code:
            langs = []
            for lang in language_code.split('+'):
                mapped = lang_map.get(lang.strip(), lang.strip())
                if mapped not in langs:
                    langs.append(mapped)
        else:
            langs = [lang_map.get(language_code.strip(), 'en')]
        
        return easyocr_ocr(image_input, languages=tuple(langs), use_gpu=kwargs.get('use_gpu', False))
    
    elif engine_name == "paddleocr":
        # Convert language codes for PaddleOCR
        lang_map = {
            'eng': 'en', 'hin': 'hi', 'mar': 'mr', 'ben': 'bn', 'guj': 'gu',
            'tam': 'ta', 'tel': 'te', 'kan': 'kn', 'mal': 'ml', 'ori': 'or',
            'pan': 'pa', 'urd': 'ur'
        }
        
        # Check if language_code is 'auto' for auto-detection
        if language_code == 'auto':
            # Use language detection with pytesseract
            try:
                import pytesseract
                from PIL import Image
                
                if isinstance(image_input, str):
                    img = Image.open(image_input)
                else:
                    img = Image.fromarray(image_input)
                
                # Detect language using pytesseract OSD
                try:
                    osd = pytesseract.image_to_osd(img)
                    # Parse script from OSD output
                    detected_script = None
                    for line in osd.split('\n'):
                        if 'Script:' in line:
                            detected_script = line.split(':')[1].strip()
                            break
                    
                    # Map script to PaddleOCR language
                    script_lang_map = {
                        'Latin': 'en',
                        'Devanagari': 'hi',
                        'Bengali': 'bn',
                        'Gujarati': 'gu',
                        'Tamil': 'ta',
                        'Telugu': 'te',
                        'Kannada': 'kn',
                        'Malayalam': 'ml',
                        'Gurmukhi': 'pa',
                        'Oriya': 'or'
                    }
                    paddle_lang = script_lang_map.get(detected_script, 'hi')  # Default to Hindi for Indian boards
                except Exception as osd_error:
                    # OSD failed, try simple heuristic
                    # If image has mostly non-ASCII characters, assume Hindi
                    try:
                        test_ocr = pytesseract.image_to_string(img)
                        non_ascii_ratio = sum(1 for c in test_ocr if ord(c) > 127) / max(len(test_ocr), 1)
                        paddle_lang = 'hi' if non_ascii_ratio > 0.3 else 'en'
                    except:
                        paddle_lang = 'hi'  # Default to Hindi for CIV boards
            except Exception:
                # Fallback to Hindi (common for Indian CIV boards)
                paddle_lang = 'hi'
        else:
            # Use first language from selection
            primary_lang = language_code.split('+')[0]
            paddle_lang = lang_map.get(primary_lang, 'hi')  # Default to Hindi instead of English
        
        return paddleocr_ocr(image_input, languages=[paddle_lang], use_gpu=kwargs.get('use_gpu', False))
    
    elif engine_name == "chandraocr" or engine_name == "chandra":
        # Chandra OCR - multilingual, no language code needed
        model_path = kwargs.get('model_path', None)
        return chandra_ocr(image_input, model_path=model_path, use_gpu=kwargs.get('use_gpu', True))
    
    elif engine_name == "suryaocr":
        # Convert language codes for Surya OCR
        lang_map = {
            'eng': 'en', 'hin': 'hi', 'mar': 'mr', 'ben': 'bn', 'guj': 'gu',
            'tam': 'ta', 'tel': 'te', 'kan': 'kn', 'mal': 'ml', 'ori': 'or',
            'pan': 'pa', 'asm': 'as', 'nep': 'ne', 'urd': 'ur', 'san': 'sa'
        }
        
        if '+' in language_code:
            langs = []
            for lang in language_code.split('+'):
                mapped = lang_map.get(lang.strip(), lang.strip())
                if mapped not in langs:
                    langs.append(mapped)
        else:
            langs = [lang_map.get(language_code.strip(), 'en')]
        
        return suryaocr_ocr(image_input, languages=langs)
    
    elif engine_name == "chandraocr":
        # Chandra OCR handles multilingual automatically
        return chandraocr_ocr(image_input)
    
    elif engine_name == "gotocr" or engine_name == "got-ocr2.0" or engine_name == "gotocr2.0":
        # GOT-OCR2.0 unified end-to-end model
        ocr_type = kwargs.get('ocr_type', 'ocr')  # 'ocr' or 'format'
        return gotocr_ocr(image_input, ocr_type=ocr_type)
    
    elif engine_name == "deepseekocr" or engine_name == "deepseek-ocr" or engine_name == "deepseek":
        # DeepSeek-OCR with free and grounding modes
        mode = kwargs.get('mode', 'free')  # 'free' or 'grounding'
        return deepseekocr_ocr(image_input, mode=mode)
    
    elif engine_name == "indicphotoocr" or engine_name == "indic-photo-ocr" or engine_name == "indicocr":
        # IndicPhotoOCR - multilingual for Indian languages, no language code needed
        return indic_photo_ocr(image_input, use_gpu=kwargs.get('use_gpu', True))
    
    else:
        return {
            "error": f"Unknown OCR engine: {engine_name}",
            "text": "",
            "average_confidence": 0,
            "processing_time": 0,
            "success": False,
            "engine": engine_name
        }


@st.cache_resource
def get_surya_ocr_models():
    """
    Initialize and cache Surya OCR models (downloaded once, stored locally)
    Models are automatically cached in ~/.cache/huggingface/
    """
    if not SURYAOCR_AVAILABLE:
        return None, None
    
    try:
        try:
            from surya.layout import LayoutPredictor
            layout_predictor_class = LayoutPredictor
        except ImportError:
            from surya.detection import DetectionPredictor as layout_predictor_class
        from surya.recognition import RecognitionPredictor
        
        # Initialize models - they will be cached locally after first download
        layout_predictor = layout_predictor_class()
        rec_predictor = RecognitionPredictor()
        
        return layout_predictor, rec_predictor
        
    except Exception as e:
        st.warning(f"Surya OCR initialization failed: {str(e)}")
        return None, None

@st.cache_resource
def get_chandra_ocr_client():
    """
    Initialize and cache Chandra OCR InferenceManager.

    Prefer the vLLM backend when a local server is already running. This is the
    recommended and most reliable path for the official chandra model, especially
    when the installed Transformers version does not recognize the checkpoint
    architecture.
    """
    if not CHANDRAOCR_AVAILABLE:
        return None

    try:
        from chandra.model import InferenceManager

        if _vllm_server_available():
            return InferenceManager(method="vllm")

        if ACCELERATE_AVAILABLE and _transformers_supports_qwen3_5():
            try:
                return InferenceManager(method="hf")
            except Exception as e:
                raise RuntimeError(
                    "Chandra HF backend failed because the installed Transformers build does not "
                    "recognize the qwen3_5 checkpoint architecture. Start a local vLLM server or "
                    "upgrade Transformers to a build that registers qwen3_5."
                ) from e

        raise RuntimeError(
            "Chandra OCR requires either a running local vLLM server or a Transformers build that "
            "registers qwen3_5. Install/update Transformers with a version that supports this model "
            "or run: chandra_vllm"
        )

    except Exception as e:
        st.warning(f"Chandra OCR initialization failed: {str(e)}")
        return None

def suryaocr_ocr(image_input, languages=['en', 'hi']) -> Dict[str, Any]:
    """
    Perform OCR using Surya OCR with timing and error handling
    Models are cached and reused across requests
    """
    try:
        if not SURYAOCR_AVAILABLE:
            return {
                'engine': 'SuryaOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Surya OCR not installed. Install with: pip install surya-ocr transformers "openai<3,>=1.55.0" pydantic-settings'
            }

        start_time = time.time()
        
        # Get cached models (loaded once, reused forever)
        layout_predictor, rec_predictor = get_surya_ocr_models()
        
        if layout_predictor is None or rec_predictor is None:
            return {
                'engine': 'SuryaOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Failed to initialize Surya OCR models'
            }
        
        # Load image robustly for both file paths, PIL images, and NumPy arrays
        from PIL import Image
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            image = Image.fromarray(np.asarray(image_input))

        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Surya has version-specific call conventions. Prefer the older explicit
        # detection-predictor form if available, then fall back to the newer
        # layout_results API used in more recent Surya releases.
        try:
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor

            # Requested compatibility path: DetectionPredictor is passed in as det_predictor
            rec_predictor_compat = RecognitionPredictor()
            det_predictor_compat = DetectionPredictor()
            rec_result = rec_predictor_compat([image], det_predictor=det_predictor_compat)
        except Exception:
            try:
                from surya.settings import settings

                if shutil.which("llama-server") is not None:
                    settings.SURYA_INFERENCE_BACKEND = "llamacpp"

                layout_results = layout_predictor([image])
                rec_result = rec_predictor(
                    [image],
                    full_page=False,
                    layout_results=layout_results,
                )
            except TypeError:
                try:
                    layout_results = layout_predictor([image])
                    rec_result = rec_predictor([image], layout_results, full_page=False)
                except TypeError:
                    rec_result = rec_predictor([image], full_page=False)
            except Exception:
                # Final fallback: if the environment still requires Docker/vLLM, fail cleanly
                # instead of crashing the app.
                try:
                    rec_result = rec_predictor([image], full_page=False)
                except TypeError:
                    rec_result = rec_predictor([image])

        # Extract text from blocks
        text_lines = []
        confidences = []
        
        if rec_result and len(rec_result) > 0:
            result_data = rec_result[0]
            
            # Check if result has blocks attribute (PageOCRResult structure)
            if hasattr(result_data, 'blocks') and result_data.blocks:
                for block in result_data.blocks:
                    # Each block has lines
                    if hasattr(block, 'lines') and block.lines:
                        for line in block.lines:
                            if hasattr(line, 'text') and line.text and line.text.strip():
                                text_lines.append(line.text.strip())
                                # Get confidence if available
                                if hasattr(line, 'confidence'):
                                    confidences.append(line.confidence * 100)
            # Fallback: check for text_lines attribute
            elif hasattr(result_data, 'text_lines') and result_data.text_lines:
                for line in result_data.text_lines:
                    if hasattr(line, 'text') and line.text and line.text.strip():
                        text_lines.append(line.text.strip())
                        if hasattr(line, 'confidence'):
                            confidences.append(line.confidence * 100)
        
        full_text = '\n'.join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        processing_time = time.time() - start_time
        
        return {
            'engine': 'SuryaOCR',
            'text': full_text,
            'confidence': round(avg_confidence, 2),
            'processing_time': round(processing_time, 3),
            'languages_used': '+'.join(languages) + ' (auto-detect)',
            'line_count': len(text_lines),
            'success': True,
            'error': None
        }
        
    except Exception as e:
        import traceback
        return {
            'engine': 'SuryaOCR',
            'text': '',
            'confidence': 0,
            'processing_time': 0,
            'languages_used': '+'.join(languages) if languages else 'unknown',
            'success': False,
            'error': f'{str(e)}\n{traceback.format_exc()}'
        }

def chandraocr_ocr(image_input) -> Dict[str, Any]:
    """
    Perform OCR using Chandra OCR with timing and error handling
    
    Chandra uses HuggingFace models for local inference.
    Model (datalab-to/chandra) is cached locally after first download.
    
    Model Cache Location: ~/.cache/huggingface/hub/models--datalab-to--chandra
    Size: ~7GB (downloaded once, reused forever)
    """
    try:
        if not CHANDRAOCR_AVAILABLE:
            return {
                'engine': 'ChandraOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Chandra OCR is not available. Start a local vLLM server or install a compatible Transformers stack for the Chandra model.'
            }

        start_time = time.time()

        manager = get_chandra_ocr_client()

        if manager is None:
            return {
                'engine': 'ChandraOCR',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': 'Failed to initialize Chandra OCR. A compatible Transformers build with qwen3_5 support or a running local vLLM server is required. Try: pip install --upgrade "transformers>=4.57.0" or run: chandra_vllm'
            }

        from PIL import Image
        from chandra.model.schema import BatchInputItem

        if isinstance(image_input, str):
            image = Image.open(image_input)
        else:
            image = Image.fromarray(image_input)

        if image.mode != 'RGB':
            image = image.convert('RGB')

        batch_input = [BatchInputItem(image=image, prompt_type="ocr_layout")]

        try:
            results = manager.generate(
                batch=batch_input,
                max_output_tokens=8192,
                include_images=False,
                include_headers_footers=False
            )
        except Exception as e:
            raise RuntimeError(
                "Chandra OCR generation failed. This usually means the installed Transformers build does not "
                "register the qwen3_5 checkpoint architecture, or no local vLLM server is running. Use a "
                "Transformers build with qwen3_5 support or start: chandra_vllm"
            ) from e

        if results and len(results) > 0:
            result = results[0]
            text = result.markdown
            confidence = 0
        else:
            text = ''
            confidence = 0

        processing_time = time.time() - start_time

        return {
            'engine': 'ChandraOCR',
            'text': text.strip(),
            'confidence': confidence,
            'processing_time': round(processing_time, 3),
            'success': True,
            'error': None
        }

    except Exception as e:
        return {
            'engine': 'ChandraOCR',
            'text': '',
            'confidence': 0,
            'processing_time': 0,
            'success': False,
            'error': str(e)
        }

def gotocr_ocr(image_input, ocr_type='ocr') -> Dict[str, Any]:
    """
    Perform OCR using GOT-OCR2.0 with timing and error handling
    Uses separate conda environment via subprocess
    
    GOT-OCR2.0 is a unified end-to-end OCR model that supports:
    - Plain text OCR
    - Format text OCR (preserves layout)
    - Fine-grained OCR with box/color selection
    - Multi-page OCR
    
    Args:
        image_input: Image path or numpy array
        ocr_type: 'ocr' for plain text or 'format' for formatted text
    
    Returns:
        Dictionary with OCR results
    """
    try:
        import subprocess
        import json
        import tempfile
        
        start_time = time.time()
        
        # Save image to temporary file if needed
        temp_image_path = None
        if isinstance(image_input, str):
            temp_image_path = os.path.abspath(image_input)
        else:
            from PIL import Image
            img = Image.fromarray(image_input)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                temp_image_path = os.path.abspath(tmp.name)
        
        # Paths
        got_demo_script = os.path.abspath(r"GOT-OCR2.0\GOT\demo\run_ocr_2.0.py")
        got_weights = os.path.abspath(r"C:\GOT_weights")
        conda_python = "conda"  # Assumes conda is in PATH
        
        # Check if files exist
        if not os.path.exists(got_demo_script):
            return {
                'engine': 'GOT-OCR2.0',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': f'GOT-OCR2.0 demo script not found at: {got_demo_script}. Run setup_got_ocr.py'
            }
        
        if not os.path.exists(got_weights):
            return {
                'engine': 'GOT-OCR2.0',
                'text': '',
                'confidence': 0,
                'processing_time': 0,
                'success': False,
                'error': f'GOT-OCR2.0 weights not found at: {got_weights}. Download from HuggingFace'
            }
        
        # Escape paths for Windows
        temp_image_path_escaped = temp_image_path.replace('\\', '\\\\')
        got_demo_escaped = got_demo_script.replace('\\', '\\\\')
        got_weights_escaped = got_weights.replace('\\', '\\\\')
        
        # Create command to run in conda environment
        # Note: This runs the GOT demo script and captures output
        cmd = [
            'conda', 'run', '-n', 'got', 'python',
            got_demo_script,
            '--model-name', got_weights,
            '--image-file', temp_image_path,
            '--type', ocr_type
        ]
        
        # Run subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )
        
        # Clean up temp file if created
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
            except:
                pass
        
        if result.returncode != 0:
            return {
                'engine': 'GOT-OCR2.0',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'success': False,
                'error': f'GOT-OCR2.0 error: {result.stderr[:500]}'
            }
        
        # Extract text from output
        # GOT-OCR2.0 prints results to stdout
        output_text = result.stdout.strip()
        
        processing_time = time.time() - start_time
        
        return {
            'engine': 'GOT-OCR2.0',
            'text': output_text,
            'confidence': 0,  # GOT-OCR2.0 doesn't provide confidence scores
            'processing_time': round(processing_time, 3),
            'ocr_type': ocr_type,
            'success': True,
            'error': None
        }
        
    except subprocess.TimeoutExpired:
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
            except:
                pass
        return {
            'engine': 'GOT-OCR2.0',
            'text': '',
            'confidence': 0,
            'processing_time': 120,
            'success': False,
            'error': 'GOT-OCR2.0 timeout (120s). GPU required for inference.'
        }
    except Exception as e:
        return {
            'engine': 'GOT-OCR2.0',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time,
            'success': False,
            'error': str(e)
        }

def deepseekocr_ocr(image_input, mode='free') -> Dict[str, Any]:
    """
    Perform OCR using DeepSeek-OCR with timing and error handling
    Uses separate conda environment via subprocess
    
    DeepSeek-OCR supports:
    - Free OCR (plain text extraction)
    - Grounding OCR (document to markdown with structure)
    - High accuracy with layout preservation
    
    Args:
        image_input: Image path or numpy array
        mode: 'free' for plain OCR or 'grounding' for structured markdown
    
    Returns:
        Dictionary with OCR results
    """
    try:
        import subprocess
        import json
        import tempfile
        
        start_time = time.time()
        
        # Save image to temporary file if needed
        temp_image_path = None
        if isinstance(image_input, str):
            temp_image_path = os.path.abspath(image_input)
        else:
            from PIL import Image
            img = Image.fromarray(image_input)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name)
                temp_image_path = os.path.abspath(tmp.name)
        
        # Escape paths for Windows
        temp_image_path_escaped = temp_image_path.replace('\\', '\\\\')
        
        # Select prompt based on mode
        if mode == 'grounding':
            prompt = "<image>\\n<|grounding|>Convert the document to markdown. "
        else:
            prompt = "<image>\\nFree OCR. "
        
        # Create Python script to run in subprocess
        script_code = f'''
import sys
import json
from transformers import AutoModel, AutoTokenizer
import torch

try:
    model_name = "deepseek-ai/DeepSeek-OCR"
    
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        _attn_implementation="flash_attention_2",
        trust_remote_code=True,
        use_safetensors=True
    )
    model = model.eval().cuda().to(torch.bfloat16)
    
    # Run inference
    prompt = "{prompt}"
    image_file = "{temp_image_path_escaped}"
    
    res = model.infer(
        tokenizer,
        prompt=prompt,
        image_file=image_file,
        base_size=1024,
        image_size=640,
        crop_mode=True,
        save_results=False,
        test_compress=True
    )
    
    # Output result as JSON
    output = {{
        "text": res,
        "success": True,
        "error": None
    }}
    print(json.dumps(output))
    
except Exception as e:
    output = {{
        "text": "",
        "success": False,
        "error": str(e)
    }}
    print(json.dumps(output))
'''
        
        # Run subprocess in deepseek-ocr conda environment
        cmd = ['conda', 'run', '-n', 'deepseek-ocr', 'python', '-c', script_code]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes timeout
        )
        
        # Clean up temp file if created
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
            except:
                pass
        
        if result.returncode != 0:
            return {
                'engine': 'DeepSeek-OCR',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'success': False,
                'error': f'DeepSeek-OCR error: {result.stderr[:500]}'
            }
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout.strip())
        except:
            # Fallback if JSON parsing fails
            output = {
                'text': result.stdout.strip(),
                'success': True,
                'error': None
            }
        
        processing_time = time.time() - start_time
        
        return {
            'engine': 'DeepSeek-OCR',
            'text': output.get('text', ''),
            'confidence': 0,  # DeepSeek-OCR doesn't provide confidence scores
            'processing_time': round(processing_time, 3),
            'mode': mode,
            'success': output.get('success', True),
            'error': output.get('error')
        }
        
    except subprocess.TimeoutExpired:
        if temp_image_path != image_input and os.path.exists(temp_image_path):
            try:
                os.unlink(temp_image_path)
            except:
                pass
        return {
            'engine': 'DeepSeek-OCR',
            'text': '',
            'confidence': 0,
            'processing_time': 180,
            'success': False,
            'error': 'DeepSeek-OCR timeout (180s). GPU required for inference.'
        }
    except Exception as e:
        return {
            'engine': 'DeepSeek-OCR',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time,
            'success': False,
            'error': str(e)
        }

def get_engine_info() -> Dict[str, str]:
    """
    Get information about OCR engines
    
    Returns:
        Dictionary with engine descriptions
    """
    return {
        "tesseract": "Google's Tesseract OCR - Fast and reliable for clean text, supports most Indian languages",
        "easyocr": "EasyOCR - Excellent for natural scenes and multilingual text, great for Hindi/Devanagari",
        "paddleocr": "PaddleOCR - Advanced neural OCR with high accuracy, good for complex documents (Python 3.10)",
        "suryaocr": "Surya OCR - State-of-the-art multilingual OCR with layout analysis (Auto-detects languages)",
        "chandraocr": "Chandra OCR - Advanced document OCR with HuggingFace models (Local inference, ~7GB model)",
        "gotocr": "GOT-OCR2.0 - Unified end-to-end OCR model, supports plain/formatted text OCR (GPU required, ~7GB model)",
        "deepseekocr": "DeepSeek-OCR - High-accuracy OCR with layout preservation, supports free/grounding modes (GPU required)",
        "indicphotoocr": "IndicPhotoOCR - Specialized OCR for Indian language photos and documents (Auto-downloads weights)"
    }
