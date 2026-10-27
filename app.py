"""
CIV Board OCR Streamlit Application - Cloud Deployment Version
Optimized for Streamlit Cloud with reduced dependencies
"""

import streamlit as st
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import cv2

# Configure page first
st.set_page_config(
    page_title="CIV Board OCR System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with Charcoal, Forest Green, Crimson Red, White
st.markdown("""
<style>
    /* Main color scheme */
    :root {
        --charcoal-black: #171717;
        --forest-green: #06110C;
        --crimson-red: #A31C18;
        --white: #FFFFFF;
    }
    
    /* Headers styling */
    .main h1, .main h2, .main h3 {
        color: #A31C18 !important;
        font-weight: 700;
    }
    
    /* Buttons - Crimson Red */
    .stButton>button {
        background-color: #A31C18;
        color: white;
        border: 2px solid #A31C18;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #8B1714;
        border-color: #8B1714;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(163, 28, 24, 0.3);
    }
    
    /* Success messages - Forest Green accent */
    .stSuccess {
        background-color: rgba(6, 17, 12, 0.3);
        border-left: 4px solid #06110C;
    }
    
    /* Info messages */
    .stInfo {
        background-color: rgba(163, 28, 24, 0.1);
        border-left: 4px solid #A31C18;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #A31C18;
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #06110C;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Expander headers */
    .streamlit-expanderHeader {
        background-color: rgba(6, 17, 12, 0.5);
        color: white;
        font-weight: 600;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #A31C18;
        background-color: rgba(6, 17, 12, 0.2);
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #06110C;
        color: white;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #A31C18;
    }
    
    /* Dataframe styling */
    .dataframe {
        border: 1px solid #A31C18;
    }
    
    /* Text input and textarea */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-color: #06110C;
        background-color: rgba(23, 23, 23, 0.9);
        color: white;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #A31C18;
        box-shadow: 0 0 0 1px #A31C18;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #A31C18;
    }
    
    /* Links */
    a {
        color: #A31C18 !important;
        font-weight: 600;
    }
    
    a:hover {
        color: #8B1714 !important;
        text-decoration: underline;
    }
    
    /* Checkbox and radio */
    [data-testid="stCheckbox"] span,
    [data-testid="stRadio"] span {
        color: white !important;
    }
    
    /* Number input */
    .stNumberInput>div>div>input {
        border-color: #06110C;
        background-color: rgba(23, 23, 23, 0.9);
        color: white;
    }
    
    /* Select box */
    .stSelectbox>div>div {
        background-color: rgba(23, 23, 23, 0.9);
        border-color: #06110C;
    }
    
    /* Custom card styling */
    div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background-color: rgba(6, 17, 12, 0.2);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #A31C18;
    }
</style>
""", unsafe_allow_html=True)

# Import our modules with cloud compatibility
try:
    from db import (
        init_db, save_record, get_all_records, get_record_by_id, delete_record, get_stats,
        get_all_images, delete_image, compute_image_hash
    )
    from preprocessing import preprocess_image, prepare_image_for_ocr, convert_pil_to_cv2
    from ocr_engines import (
        run_ocr_engine, get_available_engines, get_engine_info, 
        PADDLEOCR_AVAILABLE, SURYAOCR_AVAILABLE, CHANDRAOCR_AVAILABLE, GOTOCR_AVAILABLE, DEEPSEEKOCR_AVAILABLE
    )
    from translation import translate_text, get_available_languages
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Import streamlit-cropper with fallback
try:
    from streamlit_cropper import st_cropper
    CROPPER_AVAILABLE = True
except ImportError:
    CROPPER_AVAILABLE = False
    st.error("⚠️ streamlit-cropper not available. Some features may be limited.")

# Cloud deployment optimizations
@st.cache_data
def get_cloud_config():
    """Get cloud-specific configuration"""
    try:
        # Try to get from secrets first (Streamlit Cloud)
        config = {
            'max_file_size_mb': st.secrets.get("general", {}).get("max_file_size_mb", 10),
            'max_files_per_session': st.secrets.get("general", {}).get("max_files_per_session", 5),
            'default_ocr_engine': st.secrets.get("general", {}).get("default_ocr_engine", "tesseract"),
            'enable_easyocr': st.secrets.get("general", {}).get("enable_easyocr", True),
            'enable_paddleocr': st.secrets.get("general", {}).get("enable_paddleocr", False),
        }
    except:
        # Fallback for local development
        config = {
            'max_file_size_mb': 10,
            'max_files_per_session': 5, 
            'default_ocr_engine': 'tesseract',
            'enable_easyocr': True,
            'enable_paddleocr': False,
        }
    return config

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'stage': 'upload',
        'original_image': None,
        'crop_box': None,
        'cropped_image': None,
        'preprocessed': None,
        'civ_board_language': 'Auto-Detect (Recommended)',
        'engine': get_cloud_config()['default_ocr_engine'],
        'raw_text': '',
        'confidence': 0,
        'corrected_text': '',
        'correction_mode': 'as_is',
        'target_lang': 'Hindi',
        'translated_text': '',
        'use_preprocessing': True,
        'use_binary': False,
        'processing_complete': False,
        'ocr_completed': False,
        'correction_completed': False,
        'translation_completed': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def convert_image_format(uploaded_file):
    """
    Convert various image formats to PIL Image
    Handles special formats like HEIC, SVG, etc.
    """
    try:
        # Get file extension
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        # Handle special formats
        if file_extension in ['heic', 'heif']:
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                image = Image.open(uploaded_file)
            except ImportError:
                st.error("HEIC format requires pillow-heif. Install with: pip install pillow-heif")
                return None
        
        elif file_extension == 'svg':
            try:
                import cairosvg
                from io import BytesIO
                
                # Convert SVG to PNG first
                png_bytes = cairosvg.svg2png(bytestring=uploaded_file.getvalue())
                image = Image.open(BytesIO(png_bytes))
            except ImportError:
                st.error("SVG format requires cairosvg. Install with: pip install cairosvg")
                return None
        
        else:
            # Standard PIL formats
            image = Image.open(uploaded_file)
        
        # Convert to RGB if necessary (for compatibility)
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create white background for transparency
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        return image
        
    except Exception as e:
        st.error(f"Failed to process image format '{file_extension}': {e}")
        return None

def get_supported_formats():
    """Get list of supported image formats with descriptions"""
    return {
        'Common Formats': ['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        'High Quality': ['tiff', 'tif'],  
        'Modern Formats': ['webp', 'heic', 'heif'],
        'Vector/Other': ['svg', 'ico'],
        'Scientific': ['ppm', 'pgm', 'pbm']
    }

def detect_image_language(image):
    """
    Detect the primary language of text in an image using pytesseract OSD
    
    Args:
        image: PIL Image or numpy array
        
    Returns:
        str: Detected language name (e.g., 'Hindi', 'English')
    """
    try:
        import pytesseract
        from PIL import Image
        
        # Convert to PIL if needed
        if isinstance(image, np.ndarray):
            img = Image.fromarray(image)
        else:
            img = image
        
        # Try OSD (Orientation and Script Detection)
        try:
            osd = pytesseract.image_to_osd(img)
            detected_script = None
            
            for line in osd.split('\n'):
                if 'Script:' in line:
                    detected_script = line.split(':')[1].strip()
                    break
            
            # Map script to language name
            script_to_language = {
                'Latin': 'English',
                'Devanagari': 'Hindi',
                'Bengali': 'Bengali',
                'Gujarati': 'Gujarati',
                'Tamil': 'Tamil',
                'Telugu': 'Telugu',
                'Kannada': 'Kannada',
                'Malayalam': 'Malayalam',
                'Gurmukhi': 'Punjabi',
                'Oriya': 'Oriya/Odia'
            }
            
            detected_language = script_to_language.get(detected_script, 'Hindi')
            return detected_language
            
        except Exception as osd_error:
            # OSD failed, use heuristic
            try:
                # Quick OCR test to detect non-ASCII characters
                test_text = pytesseract.image_to_string(img)
                non_ascii_count = sum(1 for c in test_text if ord(c) > 127)
                total_chars = len(test_text.strip())
                
                if total_chars > 0:
                    non_ascii_ratio = non_ascii_count / total_chars
                    # If more than 30% non-ASCII, assume Hindi (common for CIV boards)
                    return 'Hindi' if non_ascii_ratio > 0.3 else 'English'
                else:
                    return 'Hindi'  # Default for empty/unclear text
            except:
                return 'Hindi'  # Default fallback
                
    except Exception as e:
        # If detection completely fails, default to Hindi (most common for Indian CIV boards)
        return 'Hindi'

def save_uploaded_file(uploaded_file, upload_dir="uploads"):
    """Save uploaded file and return the path - Cloud optimized"""
    # Use temp directory for cloud deployment
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def save_image_array(image_array, suffix, upload_dir="uploads"):
    """Save image array and return the path - Cloud optimized"""
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{suffix}.jpg"
    filepath = os.path.join(upload_dir, filename)
    
    # Convert array to PIL Image and save
    if len(image_array.shape) == 3:
        image = Image.fromarray(image_array.astype(np.uint8))
    else:
        image = Image.fromarray(image_array.astype(np.uint8))
    
    image.save(filepath, quality=85, optimize=True)  # Optimize for cloud storage
    return filepath

def main_app():
    """Main application interface"""
    
    st.title("📄 CIV Board OCR System")
    st.markdown("### Extract → Crop → Preprocess → OCR → Correct → Translate → Save")
    
    # Cloud deployment info
    cloud_config = get_cloud_config()
    
    with st.expander("ℹ️ System Information"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max File Size", f"{cloud_config['max_file_size_mb']} MB")
        with col2:
            st.metric("Default Engine", cloud_config['default_ocr_engine'].title())
        with col3:
            available_engines = get_available_engines()
            engine_count = sum(available_engines.values())
            st.metric("OCR Engines", f"{engine_count} Available")
    
    # Navigation sidebar
    with st.sidebar:
        st.header("📋 Navigation")
        app_mode = st.radio(
            "Choose Mode:",
            ["New Extraction", "View Records"],
            index=0,
            key="main_navigation_radio"
        )
    
    if app_mode == "New Extraction":
        extraction_pipeline()
    else:
        view_records()

def extraction_pipeline():
    """Main extraction pipeline - Cloud optimized"""
    
    cloud_config = get_cloud_config()
    
    # Stage 1: Upload
    st.header("1. 📤 Upload Image")
    
    # Show supported formats info
    with st.expander("📋 Supported Image Formats", expanded=False):
        formats = get_supported_formats()
        for category, format_list in formats.items():
            st.write(f"**{category}**: {', '.join(format_list).upper()}")
        
        st.info("💡 **Tips:**\n"
               "- HEIC/HEIF (iPhone photos) supported\n" 
               "- SVG files converted to raster images\n"
               "- Transparent images get white background\n"
               "- All formats optimized for OCR processing")
    
    uploaded_file = st.file_uploader(
        "Choose a board/document photo:",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'tif', 'webp', 'svg', 'ico', 'ppm', 'pgm', 'pbm', 'heic', 'heif'],
        help=f"Upload any image format (max {cloud_config['max_file_size_mb']} MB)",
        key="main_file_uploader"
    )
    
    if uploaded_file is not None:
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > cloud_config['max_file_size_mb']:
            st.error(f"File too large ({file_size_mb:.1f} MB). Maximum allowed: {cloud_config['max_file_size_mb']} MB")
            return
        
        # Check if this is a new file (different from the one in session state)
        current_filename = uploaded_file.name
        if 'last_uploaded_filename' not in st.session_state or st.session_state.last_uploaded_filename != current_filename:
            # New file uploaded - clear all previous session state
            st.session_state.last_uploaded_filename = current_filename
            st.session_state.original_image = None
            st.session_state.cropped_image = None
            st.session_state.preprocessed = None
            st.session_state.raw_text = ''
            st.session_state.corrected_text = ''
            st.session_state.translated_text = ''
            st.session_state.ocr_completed = False
            st.session_state.confidence = 0
            if 'last_cropped_hash' in st.session_state:
                del st.session_state.last_cropped_hash
            if 'detected_language' in st.session_state:
                del st.session_state.detected_language
        
        # Save uploaded file (only once per file)
        if st.session_state.original_image is None:
            original_path = save_uploaded_file(uploaded_file)
            st.session_state.original_image = original_path
        
        # Display original image with format support
        image = convert_image_format(uploaded_file)
        if image is None:
            st.error("Failed to load image. Please try a different format.")
            return
            
        st.image(image, caption=f"Uploaded Image ({uploaded_file.name})", use_container_width=True)
        
        # Stage 2: Crop
        st.header("2. ✂️ Crop Text Region")
        
        # Add "Use Full Image" option
        col_crop1, col_crop2 = st.columns([3, 1])
        with col_crop1:
            st.write("Use the crop tool below to select the text region, or use the full image.")
        with col_crop2:
            if st.button("📄 Use Full Image", help="Skip cropping and use entire image"):
                st.session_state.cropped_image = np.array(image)
                orig_h, orig_w = st.session_state.cropped_image.shape[:2]
                st.session_state.crop_box = {
                    "original_width": orig_w,
                    "original_height": orig_h,
                    "cropped_width": orig_w,
                    "cropped_height": orig_h,
                    "crop_method": "full_image"
                }
                st.success("✅ Using full image (no crop)")
                st.rerun()
        
        if CROPPER_AVAILABLE:
            cropped_img = st_cropper(
                image,
                realtime_update=True,
                box_color='#FF0004',
                aspect_ratio=None,
                return_type='image'
            )
            
            if cropped_img is not None:
                st.session_state.cropped_image = np.array(cropped_img)
                
                # Calculate crop box for database
                crop_h, crop_w = st.session_state.cropped_image.shape[:2]
                orig_h, orig_w = np.array(image).shape[:2]
                
                st.session_state.crop_box = {
                    "original_width": orig_w,
                    "original_height": orig_h,
                    "cropped_width": crop_w,
                    "cropped_height": crop_h,
                    "crop_method": "streamlit_cropper"
                }
                
                # Show crop info and warning
                crop_ratio = (crop_h * crop_w) / (orig_h * orig_w)
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Original Size", f"{orig_w}×{orig_h}")
                with col_info2:
                    st.metric("Cropped Size", f"{crop_w}×{crop_h}")
                with col_info3:
                    st.metric("Area Used", f"{crop_ratio*100:.1f}%")
                
                # Warning if cropping too much
                if crop_ratio < 0.3:
                    st.warning("⚠️ You're using less than 30% of the image. Make sure you're not cutting off important text!")
                elif crop_h < orig_h * 0.5:
                    st.info("ℹ️ Crop height is less than 50% of original. Ensure all text lines are included.")
                
                # Auto-detect language from cropped image (only once per crop)
                if 'last_cropped_hash' not in st.session_state or st.session_state.last_cropped_hash != hash(cropped_img.tobytes()):
                    st.session_state.last_cropped_hash = hash(cropped_img.tobytes())
                    detected_lang = detect_image_language(cropped_img)
                    st.session_state.detected_language = detected_lang
                    st.session_state.civ_board_language = detected_lang
                
                # Continue with the rest of the pipeline...
                process_cropped_image(cropped_img, cloud_config)
        else:
            st.warning("⚠️ Cropping not available. Using full image.")
            st.session_state.cropped_image = np.array(image)
            process_cropped_image(image, cloud_config)

def process_cropped_image(cropped_img, cloud_config):
    """Process the cropped image through the OCR pipeline"""
    
    # Stage 3: Preprocess
    st.header("3. 🎨 Preprocess")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.use_preprocessing = st.checkbox(
            "Enable preprocessing", 
            value=st.session_state.use_preprocessing,
            help="Apply grayscale → denoise → CLAHE → adaptive threshold",
            key="preprocessing_checkbox"
        )
        
        if st.session_state.use_preprocessing:
            st.session_state.use_binary = st.checkbox(
                "Use binary threshold (alternative processing)",
                value=st.session_state.use_binary,
                help="Use binary image instead of enhanced grayscale",
                key="binary_checkbox"
            )
    
    # Show cropped vs preprocessed
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Cropped Image")
        st.image(cropped_img, caption="Cropped Region")
    
    with col2:
        st.subheader("Preprocessed Image")
        
        if st.session_state.use_preprocessing:
            # Apply preprocessing
            cropped_bgr = convert_pil_to_cv2(cropped_img)
            gray, enhanced, binary = preprocess_image(cropped_bgr)
            
            # Choose enhanced or binary
            processed_img = binary if st.session_state.use_binary else enhanced
            st.session_state.preprocessed = processed_img
            
            st.image(processed_img, caption="Preprocessed")
        else:
            # Use original cropped image
            st.session_state.preprocessed = np.array(cropped_img)
            st.image(cropped_img, caption="No preprocessing")
    
    # Stage 4: Language Selection & OCR
    st.header("4. 🌐 Select CIV Board Language")
    
    # Initialize session state for detected language
    if 'detected_language' not in st.session_state:
        st.session_state.detected_language = None
    
    # Language selection for OCR
    civ_languages = {
        # Auto-detection option (intelligently picks dominant language)
        'Auto-Detect (Recommended)': 'auto',
        
        # Single languages only
        'English': 'eng',
        'Hindi': 'hin', 
        'Marathi': 'mar',
        'Bengali': 'ben',
        'Gujarati': 'guj',
        'Tamil': 'tam',
        'Telugu': 'tel',
        'Kannada': 'kan',
        'Malayalam': 'mal',
        'Oriya/Odia': 'ori',
        'Punjabi': 'pan',
        'Assamese': 'asm',
        'Nepali': 'nep',
        'Urdu': 'urd',
        'Sanskrit': 'san'
    }
    
    # Reverse mapping for detection
    lang_code_to_name = {v: k for k, v in civ_languages.items()}
    
    # Auto-detect button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.session_state.civ_board_language = st.selectbox(
            "Select the primary language of the CIV board:",
            list(civ_languages.keys()),
            index=list(civ_languages.keys()).index(st.session_state.get('civ_board_language', 'Auto-Detect (Recommended)')),
            help="Choose language or use Auto-Detect to let the system identify it",
            key="civ_language_selector"
        )
    
    with col2:
        if st.button("🔍 Detect Language", help="Analyze image to detect language"):
            if st.session_state.cropped_image is not None:
                with st.spinner("Detecting language..."):
                    try:
                        import pytesseract
                        from PIL import Image
                        import numpy as np
                        
                        # Convert to PIL Image
                        if isinstance(st.session_state.cropped_image, np.ndarray):
                            img = Image.fromarray(st.session_state.cropped_image)
                        else:
                            img = st.session_state.cropped_image
                        
                        # Try OSD detection
                        try:
                            osd = pytesseract.image_to_osd(img)
                            detected_script = None
                            for line in osd.split('\n'):
                                if 'Script:' in line:
                                    detected_script = line.split(':')[1].strip()
                                    break
                            
                            # Map script to language code
                            script_lang_map = {
                                'Latin': 'eng',
                                'Devanagari': 'hin',
                                'Bengali': 'ben',
                                'Gujarati': 'guj',
                                'Tamil': 'tam',
                                'Telugu': 'tel',
                                'Kannada': 'kan',
                                'Malayalam': 'mal',
                                'Gurmukhi': 'pan',
                                'Oriya': 'ori'
                            }
                            detected_code = script_lang_map.get(detected_script, 'hin')
                            st.session_state.detected_language = lang_code_to_name.get(detected_code, 'Hindi')
                            st.session_state.civ_board_language = st.session_state.detected_language
                            st.success(f"✅ Detected: **{st.session_state.detected_language}**")
                            st.rerun()
                        except:
                            # Fallback: Check for non-ASCII characters
                            test_ocr = pytesseract.image_to_string(img)
                            non_ascii_ratio = sum(1 for c in test_ocr if ord(c) > 127) / max(len(test_ocr), 1)
                            if non_ascii_ratio > 0.3:
                                st.session_state.detected_language = 'Hindi'
                                st.session_state.civ_board_language = 'Hindi'
                                st.success(f"✅ Detected: **Hindi** (high non-ASCII content)")
                            else:
                                st.session_state.detected_language = 'English'
                                st.session_state.civ_board_language = 'English'
                                st.success(f"✅ Detected: **English**")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Detection failed: {str(e)}")
                        st.session_state.detected_language = 'Hindi'
            else:
                st.warning("⚠️ Please crop an image first (Step 2)")
    
    # Show detected language info
    if st.session_state.detected_language:
        st.info(f"🔍 **Auto-detected**: {st.session_state.detected_language} - You can change it using the dropdown if incorrect")
    elif st.session_state.civ_board_language == 'Auto-Detect (Recommended)':
        st.info("💡 **Auto-Detect** will analyze the image during OCR and select the best language model")
    else:
        st.info(f"💡 OCR will use **{st.session_state.civ_board_language}** language model for text extraction")
    
    # Get language code for OCR engines
    selected_lang_code = civ_languages[st.session_state.civ_board_language]
    
    st.header("5. 🔍 OCR Extraction")
    
    # Engine selection - Always show all engines
    available_engines = get_available_engines()
    engine_info = get_engine_info()
    
    # Build options list - show all engines (available and unavailable)
    available_options = []
    engine_mapping = {}  # Map display name to engine key
    
    for engine, available in available_engines.items():
        if available:
            display_name = engine.title()
            if engine == 'suryaocr':
                display_name = "SuryaOCR"
            elif engine == 'chandraocr':
                display_name = "ChandraOCR"
            available_options.append(display_name)
            engine_mapping[display_name] = engine
        else:
            # Show unavailable engines with indicator
            display_name = f"{engine.title()} (Not Installed)"
            if engine == 'paddleocr':
                display_name = "PaddleOCR (Not Installed)"
            elif engine == 'suryaocr':
                display_name = "SuryaOCR (Not Installed)"
            elif engine == 'chandraocr':
                display_name = "ChandraOCR (Not Installed)"
            available_options.append(display_name)
            engine_mapping[display_name] = engine
    
    if available_options:
        selected_engine = st.selectbox(
            "Select OCR Engine:",
            available_options,
            index=0,
            help="Choose the OCR engine for text extraction",
            key="ocr_engine_selector"
        )
        
        # Get actual engine name from mapping
        new_engine = engine_mapping[selected_engine]
        
        # Clear previous OCR results if engine changed
        if 'engine' in st.session_state and st.session_state.engine != new_engine:
            # Engine changed - clear previous results
            st.session_state.raw_text = ''
            st.session_state.corrected_text = ''
            st.session_state.ocr_completed = False
            st.session_state.confidence = 0
            st.info(f"🔄 Switched from **{st.session_state.engine.upper()}** to **{new_engine.upper()}** - Previous results cleared")
        
        st.session_state.engine = new_engine
        
        # Check if PaddleOCR is selected but not installed
        if "paddleocr" in selected_engine.lower() and not PADDLEOCR_AVAILABLE:
            st.warning("⚠️ PaddleOCR is not installed")
            with st.expander("📦 How to Install PaddleOCR", expanded=True):
                st.markdown("""
                ### Installation Options:
                
                **Note:** PaddleOCR requires Python 3.8-3.11 (not compatible with Python 3.14)
                
                **Option 1: CPU Version (Recommended for most users)**
                ```bash
                pip install paddlepaddle
                pip install paddleocr
                ```
                
                **Option 2: GPU Version (For CUDA-enabled systems)**
                ```bash
                pip install paddlepaddle-gpu
                pip install paddleocr
                ```
                
                After installation, restart the Streamlit app to use PaddleOCR.
                """)
            st.info("💡 You can use Tesseract or EasyOCR while PaddleOCR is being installed")
        
        # Check if Surya OCR is selected but not installed
        if st.session_state.engine == 'suryaocr' and not SURYAOCR_AVAILABLE:
            st.warning("⚠️ Surya OCR is not installed")
            with st.expander("📦 How to Install Surya OCR", expanded=True):
                st.markdown("""
                ### Surya OCR Installation:
                
                **Note:** Surya OCR requires Python 3.10-3.12 (not compatible with Python 3.13+)
                
                ```bash
                pip install surya-ocr transformers "openai<3,>=1.55.0" pydantic-settings
                pip install opencv-python-headless==4.11.0.86
                ```
                
                **Features:**
                - State-of-the-art multilingual OCR (85.9% olmOCR benchmark)
                - Built-in layout analysis
                - Excellent for complex documents and Indian scripts
                - Handles tables, forms, and multi-column layouts
                
                After installation, restart the Streamlit app to use Surya OCR.
                """)
            st.info("💡 Surya OCR offers superior accuracy for complex multilingual documents")
        
        # Check if Chandra OCR is selected but not installed
        if st.session_state.engine == 'chandraocr' and not CHANDRAOCR_AVAILABLE:
            st.warning("⚠️ Chandra OCR is not installed")
            with st.expander("📦 How to Install Chandra OCR", expanded=True):
                st.markdown("""
                ### Chandra OCR Installation:
                
                **Note:** Chandra OCR requires Python 3.10-3.12
                
                ```bash
                pip install chandra-ocr
                ```
                
                **Features:**
                - Advanced document OCR (77.8% on 43-language benchmark)
                - Outputs HTML, Markdown, JSON (structure-preserving)
                - Handles handwriting, tables, forms, math equations
                - 4B parameter vision-language model
                
                After installation, restart the Streamlit app to use Chandra OCR.
                """)
            st.info("💡 Chandra OCR provides high-performance OCR with document structure preservation")
        
        # Check if GOT-OCR2.0 is selected but not installed
        if st.session_state.engine == 'gotocr' and not GOTOCR_AVAILABLE:
            st.warning("⚠️ GOT-OCR2.0 is not installed")
            with st.expander("📦 How to Install GOT-OCR2.0", expanded=True):
                st.markdown("""
                ### GOT-OCR2.0 Installation:
                
                **Requirements:**
                - CUDA 11.8+ GPU (GPU required for inference)
                - Python 3.10
                - ~7GB model weights
                - Minimum 8GB GPU VRAM
                
                **Installation Steps:**
                
                1. **Run setup helper:**
                   ```bash
                   python setup_got_ocr.py
                   ```
                
                2. **Or manual setup:**
                   ```bash
                   # Clone repository
                   git clone https://github.com/Ucas-HaoranWei/GOT-OCR2.0.git
                   cd GOT-OCR2.0
                   
                   # Create conda environment
                   conda create -n got python=3.10 -y
                   conda activate got
                   pip install -e .
                   
                   # Install Flash-Attention
                   pip install ninja
                   pip install flash-attn --no-build-isolation
                   ```
                
                3. **Download model weights (~7GB):**
                   - HuggingFace: https://huggingface.co/stepfun-ai/GOT-OCR2_0
                   - Save to: `C:/GOT_weights/`
                
                **Features:**
                - Unified end-to-end OCR model
                - Plain text OCR
                - Formatted text OCR (preserves layout)
                - Fine-grained OCR with box/color selection
                - Multi-page document support
                
                After installation, restart the Streamlit app to use GOT-OCR2.0.
                """)
            st.error("⚠️ GOT-OCR2.0 requires CUDA GPU. Not suitable for CPU-only systems.")
        
        # Check if DeepSeek-OCR is selected but not installed
        if st.session_state.engine == 'deepseekocr' and not DEEPSEEKOCR_AVAILABLE:
            st.warning("⚠️ DeepSeek-OCR is not installed")
            with st.expander("📦 How to Install DeepSeek-OCR", expanded=True):
                st.markdown("""
                ### DeepSeek-OCR Installation:
                
                **Requirements:**
                - CUDA 11.8+ GPU (GPU required for inference)
                - Python 3.12.9
                - PyTorch 2.6.0+
                - vLLM 0.8.5 custom wheel
                - Minimum 16GB GPU VRAM recommended
                
                **Installation Steps:**
                
                1. **Run setup helper:**
                   ```bash
                   python setup_deepseek_ocr.py
                   ```
                
                2. **Or manual setup:**
                   ```bash
                   # Clone repository
                   git clone https://github.com/deepseek-ai/DeepSeek-OCR.git
                   cd DeepSeek-OCR
                   
                   # Create conda environment
                   conda create -n deepseek-ocr python=3.12.9 -y
                   conda activate deepseek-ocr
                   
                   # Install PyTorch
                   pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
                   
                   # Download and install vLLM wheel
                   pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
                   
                   # Install requirements
                   pip install -r requirements.txt
                   pip install flash-attn==2.7.3 --no-build-isolation
                   ```
                
                3. **Model auto-downloads from HuggingFace:**
                   - Model: deepseek-ai/DeepSeek-OCR
                   - Downloads automatically on first use
                
                **Features:**
                - Free OCR (plain text extraction)
                - Grounding OCR (document to markdown with structure)
                - High accuracy with layout preservation
                - Streaming output support
                - Batch processing with vLLM (~2500 tokens/s on A100)
                
                After installation, restart the Streamlit app to use DeepSeek-OCR.
                """)
            st.error("⚠️ DeepSeek-OCR requires CUDA GPU with 16GB+ VRAM. Not suitable for CPU-only systems.")
        
        # Show engine info
        with st.expander("ℹ️ Engine Information"):
            for engine, available in available_engines.items():
                status = "✅ Available" if available else "❌ Not installed"
                st.write(f"**{engine.title()}**: {status}")
                st.write(f"_{engine_info[engine]}_")
                
                # Show installation hint for PaddleOCR
                if engine == 'paddleocr' and not available:
                    st.info("💡 PaddleOCR offers high accuracy for complex documents. See installation instructions above.")
        
        # OCR button - Check if engine is available
        engine_available = available_engines.get(st.session_state.engine, False)
        
        button_disabled = not engine_available
        button_label = "🔍 Extract Text" if engine_available else "⚠️ Install Engine First"
        
        if st.button(button_label, type="primary", key="extract_text_button", disabled=button_disabled):
            # Check again before processing
            if not engine_available:
                st.error(f"❌ {st.session_state.engine.title()} is not installed. Please install it first.")
            else:
                with st.spinner(f"Extracting text with {selected_engine}..."):
                    
                    # Prepare image for OCR
                    if st.session_state.engine == 'tesseract':
                        # Tesseract uses the preprocessed image directly
                        if st.session_state.use_preprocessing:
                            ocr_input = st.session_state.preprocessed
                        else:
                            ocr_input = convert_pil_to_cv2(cropped_img)
                    else:
                        # EasyOCR and PaddleOCR need file paths
                        temp_path = save_image_array(
                            st.session_state.cropped_image, 
                            f"temp_crop_{st.session_state.engine}"
                        )
                        ocr_input = temp_path
                    
                    # Run OCR with selected language
                    # Show which language is being used
                    with st.spinner(f"Extracting text with {selected_engine} (Language: {st.session_state.civ_board_language})..."):
                        # Prepare kwargs based on engine
                        if st.session_state.engine == 'chandraocr':
                            # Chandra OCR - multilingual, doesn't need language_code
                            # Pass model_path if specified
                            model_path = st.session_state.get('chandra_model_path', None)
                            result = run_ocr_engine(
                                st.session_state.engine,
                                ocr_input,
                                model_path=model_path,
                                use_gpu=True
                            )
                        elif st.session_state.engine == 'indicphotoocr':
                            # IndicPhotoOCR - multilingual for Indian languages, doesn't need language_code
                            result = run_ocr_engine(
                                st.session_state.engine,
                                ocr_input,
                                use_gpu=True
                            )
                        else:
                            # Other engines - use language codes
                            result = run_ocr_engine(
                                st.session_state.engine,
                                ocr_input,
                                language_code=selected_lang_code,
                                languages=tuple(selected_lang_code.split('+')) if st.session_state.engine == 'easyocr' else None
                            )
                
                # Store results
                if result.get('success', False):
                    st.session_state.raw_text = result['text']
                    st.session_state.confidence = result.get('confidence', result.get('average_confidence', 0))
                    st.session_state.ocr_completed = True
                    
                    # Store detected language
                    detected_lang = result.get('languages_used', selected_lang_code)
                    
                    # Map language codes to full names for display
                    lang_display_map = {
                        'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 'bn': 'Bengali',
                        'gu': 'Gujarati', 'ta': 'Tamil', 'te': 'Telugu', 'kn': 'Kannada',
                        'ml': 'Malayalam', 'or': 'Oriya', 'pa': 'Punjabi', 'ur': 'Urdu',
                        'as': 'Assamese', 'ne': 'Nepali', 'sa': 'Sanskrit'
                    }
                    detected_lang_name = lang_display_map.get(detected_lang, detected_lang)
                    
                    # If auto-detect was used, update the display
                    if st.session_state.civ_board_language == 'Auto-Detect (Recommended)':
                        lang_display = f"Auto-Detect (detected: {detected_lang_name})"
                    else:
                        lang_display = detected_lang_name
                    
                    # Display results with language info
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                    with col2:
                        st.metric("Language Used", lang_display)
                    with col3:
                        st.metric("Confidence", f"{result.get('confidence', 0):.1f}%")
                    
                    st.success("✅ Text extraction completed!")
                    
                    # Show extracted text
                    st.subheader("📝 Extracted Text")
                    st.text_area(
                        "Raw OCR Output:",
                        value=st.session_state.raw_text,
                        height=150,
                        disabled=True,
                        key="raw_ocr_display"
                    )
                    
                else:
                    st.error(f"❌ OCR failed: {result.get('error', 'Unknown error')}")
    else:
        st.error("❌ No OCR engines available. Please check installation.")
    
    # Show correction interface if OCR has been completed
    if st.session_state.ocr_completed and st.session_state.raw_text:
        show_correction_interface(cropped_img)

def show_correction_interface(cropped_img):
    """Show text correction and translation interface with auto-correction"""
    
    if st.session_state.raw_text:
        # Stage 6: Correction
        st.header("6. ✏️ Text Correction")
        
        # Check if this image already has a saved correction
        existing_correction = None
        correction_exists = False
        
        if st.session_state.get('image_id'):
            from db import get_correction
            existing_correction = get_correction(st.session_state.image_id)
            correction_exists = existing_correction is not None
        
        # Show banner if correction already exists
        if correction_exists:
            st.info(f"""
            📌 **Previously Corrected Text Found**
            
            This image was already corrected on **{existing_correction.get('updated_at', 'unknown date')}** 
            (Engine: {existing_correction.get('corrected_by_engine', 'unknown')})
            
            The corrected text is shown below. If you want to make changes, edit the text and save again.
            """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Determine which text to show
            if correction_exists and not st.session_state.get('override_existing_correction', False):
                # Show existing corrected text (read-only by default)
                display_text = existing_correction.get('eocr_corrected', st.session_state.raw_text)
                correction_mode = existing_correction.get('correction_mode', 'previously_saved')
                
                # Option to edit existing correction
                st.subheader("📝 Previously Corrected Text")
                
                col_view, col_edit = st.columns([1, 1])
                with col_view:
                    st.info("✅ This text was previously corrected and saved.")
                with col_edit:
                    if st.button("✏️ Edit Correction", key="edit_existing_correction"):
                        st.session_state.override_existing_correction = True
                        st.rerun()
                
                # Show in disabled text area (read-only view)
                st.text_area(
                    "Corrected Text (saved):",
                    value=display_text,
                    height=200,
                    disabled=True,
                    key="saved_correction_display",
                    help="This is the previously saved correction. Click 'Edit Correction' above to modify."
                )
                
                # Store in session state for saving
                st.session_state.corrected_text = display_text
                st.session_state.correction_mode = correction_mode
                
            else:
                # First time or editing mode - show editable correction interface
                if correction_exists and st.session_state.get('override_existing_correction'):
                    st.warning("⚠️ You are editing a previously saved correction. Changes will update the saved version.")
                    display_text = existing_correction.get('eocr_corrected', st.session_state.raw_text)
                else:
                    display_text = st.session_state.corrected_text or st.session_state.raw_text
                
                # Auto-correction option with warning
                st.subheader("⚙️ Auto-Correction Options")
                
                col_auto, col_manual = st.columns([1, 1])
                
                with col_auto:
                    if st.button("🤖 Auto-Correct", key="main_auto_correct_button", help="Conservatively fix obvious OCR errors"):
                        with st.spinner("Applying conservative auto-correction..."):
                            original_text = st.session_state.corrected_text or st.session_state.raw_text
                            corrected = auto_correct_text(
                                original_text, 
                                st.session_state.civ_board_language
                            )
                            
                            if corrected != original_text:
                                st.session_state.corrected_text = corrected
                                st.session_state.correction_mode = 'auto_corrected'
                                st.success("✅ Auto-correction applied!")
                            else:
                                st.session_state.corrected_text = original_text
                                st.info("ℹ️ No corrections needed - text looks good!")
                
                with col_manual:
                    if st.button("↩️ Reset to Original", key="main_reset_correction_button", help="Reset to original OCR output"):
                        st.session_state.corrected_text = st.session_state.raw_text
                        st.session_state.correction_mode = 'reset_to_original'
                        st.session_state.override_existing_correction = False
                        st.success("✅ Reset to original OCR text!")
                        st.rerun()
                
                if correction_exists:
                    st.info("💡 **Tip**: You are updating an existing correction. The changes will overwrite the previous version.")
                else:
                    st.info("💡 **Tip**: The raw OCR text is often quite good. Only use auto-correct if you see obvious errors.")
                
                # Manual correction text area (editable)
                st.session_state.corrected_text = st.text_area(
                    "Edit the extracted text (preserves line breaks):",
                    value=display_text,
                    height=200,
                    help="Manual editing: Correct any OCR errors. The original text might already be quite accurate.",
                    key="main_correction_text_area"
                )
        
        with col2:
            st.subheader("📋 Text Comparison")
            
            # Show original vs current side by side
            original_text = st.session_state.raw_text or "No OCR text available"
            current_text = st.session_state.corrected_text or st.session_state.raw_text or ""
            
            # Quick stats
            col_orig, col_curr = st.columns(2)
            with col_orig:
                st.metric("Original Lines", len(original_text.split('\n')))
                st.metric("Original Words", len(original_text.split()))
            with col_curr:
                st.metric("Current Lines", len(current_text.split('\n')))
                st.metric("Current Words", len(current_text.split()))
            
            # Show reference image
            st.image(cropped_img, caption="Reference Image", use_container_width=True)
            
            # Show difference indicator
            if original_text.strip() == current_text.strip():
                st.success("✅ Text unchanged from OCR output")
            else:
                changes = abs(len(current_text) - len(original_text))
                st.info(f"📝 Text modified ({changes} character difference)")
        
        # Stage 7: Translation (Optional)
        if st.session_state.corrected_text or st.session_state.raw_text:
            st.header("7. 🌐 Translation (Optional)")
            
            # Check if translation already exists for this image
            if correction_exists and existing_correction.get('translated_text'):
                st.info(f"""
                📌 **Previously Translated Text Found**
                
                Target Language: **{existing_correction.get('target_language', 'unknown')}**
                
                The translation is shown below. Click "Translate" to create a new translation.
                """)
                
                # Show existing translation
                st.text_area(
                    f"Saved Translation ({existing_correction.get('target_language', 'unknown')}):",
                    value=existing_correction.get('translated_text', ''),
                    height=150,
                    disabled=True,
                    key="saved_translation_display"
                )
                
                # Store in session state
                if not st.session_state.get('translated_text'):
                    st.session_state.translated_text = existing_correction.get('translated_text', '')
                    st.session_state.target_lang = existing_correction.get('target_language', 'English')
            
            st.info("💡 **Tip**: You can translate to multiple languages. Each translation will be saved separately when you click Save Record.")
            
            # Smart default for translation target
            source_lang = st.session_state.civ_board_language
            default_target = "English" if "English" not in source_lang else "Hindi"
            
            languages = get_available_languages()
            
            # Use a unique key based on current time to allow re-translation
            import time
            translation_key = f"translation_selector_{int(time.time())}"
            
            st.session_state.target_lang = st.selectbox(
                "Select target language for translation:",
                languages,
                index=languages.index(default_target) if default_target in languages else 0,
                key="main_target_language_selector",
                help="Change language and click Translate again for multiple translations"
            )
            
            # Translation button and processing
            col_translate, col_status = st.columns([1, 2])
            
            with col_translate:
                # Clear cache button
                if st.button("🔄 Clear Translation Cache", key="clear_translation_cache", help="Click this if translation is stuck"):
                    if hasattr(st.session_state, 'last_translation_result'):
                        del st.session_state.last_translation_result
                    st.success("✅ Cache cleared! You can now translate again.")
                
                if st.button("🌐 Translate", key="main_translate_button"):
                    try:
                        with st.spinner("Translating..."):
                            # Use corrected text if available, otherwise raw text
                            text_to_translate = st.session_state.corrected_text or st.session_state.raw_text
                            
                            if not text_to_translate or not text_to_translate.strip():
                                st.error("❌ No text available for translation")
                            else:
                                # Don't use cached translation - translate fresh each time
                                from translation import translate_text_no_cache
                                
                                translation_result = translate_text_no_cache(
                                    text_to_translate,
                                    st.session_state.target_lang
                                )
                                
                                if translation_result['success']:
                                    st.session_state.translated_text = translation_result['translated_text']
                                    st.session_state.translation_completed = True
                                    st.session_state.last_translation_result = translation_result
                                    backend_used = translation_result.get('backend', 'Unknown')
                                    st.success(f"✅ Translation to {st.session_state.target_lang} completed using {backend_used}")
                                    
                                    # Show any additional notes
                                    if 'note' in translation_result:
                                        st.info(f"ℹ️ {translation_result['note']}")
                                        
                                else:
                                    error_msg = translation_result.get('error', 'Unknown error')
                                    st.error(f"❌ Translation failed: {error_msg}")
                                    
                                    # Show fallback suggestion
                                    if 'suggestion' in translation_result:
                                        st.info(f"💡 Suggestion: {translation_result['suggestion']}")
                                    
                                    # Show which backends were tried
                                    if 'backends_tried' in translation_result:
                                        with st.expander("🔧 Technical Details"):
                                            st.write("**Backends attempted:**")
                                            for backend_error in translation_result['backends_tried']:
                                                st.write(f"• {backend_error}")
                    except Exception as e:
                        st.error(f"❌ Translation error: {str(e)}")
                        st.info("💡 Try with shorter text or check your internet connection")
            
            with col_status:
                # Show translation status
                if st.session_state.translated_text:
                    st.success(f"✅ Latest translation: {st.session_state.target_lang}")
                    if hasattr(st.session_state, 'last_translation_result'):
                        backend = st.session_state.last_translation_result.get('backend', 'Unknown')
                        st.caption(f"Using: {backend}")
                else:
                    st.info("ℹ️ Click 'Translate' to convert text to your target language")
            
            # Show translation result - Always show if translation exists
            if st.session_state.translated_text:
                st.session_state.translated_text = st.text_area(
                    f"Translated Text ({st.session_state.target_lang}):",
                    value=st.session_state.translated_text,
                    height=150,
                    help="You can edit the translation if needed. To translate to another language, select a different language above and click Translate again.",
                    key="main_translated_text_area"
                )
                
                # Show note about multiple translations
                st.caption("💾 **Note**: When you save the record, the currently displayed translation will be saved. To save multiple translations, save the record after each translation.")
        
        # Stage 8: Save to Database (show as soon as we have corrected_text OR raw_text)
        if st.session_state.corrected_text or st.session_state.raw_text:
            show_save_interface(cropped_img)

def auto_correct_text(text: str, language: str) -> str:
    """
    Conservative auto-correct OCR text - only fix obvious errors
    """
    try:
        corrected = text
        
        # Only apply very conservative corrections for obvious OCR errors
        # Common OCR character misreads (only when context is clear)
        conservative_corrections = {
            # Only fix these in specific contexts to avoid over-correction
            'MGNREGAJ': 'MGNREGA',  # Specific program name
            'HATERIAL': 'MATERIAL',
            'OISTRICT': 'DISTRICT', 
            'GOVERNHENT': 'GOVERNMENT',
            'EMPLOYIHEHT': 'EMPLOYMENT',
            'DEVELOPNENT': 'DEVELOPMENT',
            'HINISTRY': 'MINISTRY',
            'NATINAL': 'NATIONAL',
            'MAHATIA': 'MAHATMA',
            'GANDIII': 'GANDHI'
        }
        
        # Apply only specific known corrections
        for wrong, right in conservative_corrections.items():
            if wrong.upper() in corrected.upper():
                # Case-preserving replacement
                import re
                corrected = re.sub(re.escape(wrong), right, corrected, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and line breaks but preserve structure
        lines = corrected.split('\n')
        cleaned_lines = []
        for line in lines:
            # Only clean excessive whitespace, preserve single spaces
            cleaned_line = re.sub(r' +', ' ', line.strip())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        corrected = '\n'.join(cleaned_lines)
        
        # If no significant changes were made, return original
        if len(corrected.strip()) < len(text.strip()) * 0.8:
            # Too much text lost, return original
            return text.strip()
            
        return corrected if corrected.strip() else text.strip()
        
    except Exception as e:
        # If auto-correction fails, return original text
        print(f"Auto-correction failed: {e}")
        return text.strip()

def show_save_interface(cropped_img):
    """Show save to database interface"""
    
    st.header("8. 💾 Save Record")
    
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if st.button("💾 Save Record", type="primary", key="save_record_button"):
            try:
                # Save cropped image
                cropped_path = save_image_array(
                    st.session_state.cropped_image,
                    f"cropped_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                # Save to database with new schema
                import uuid
                image_id = str(uuid.uuid4())[:8]  # Short unique ID
                
                record_id = save_record(
                    image_id=image_id,
                    civ_board_language=st.session_state.civ_board_language,
                    original_image_path=st.session_state.original_image,
                    crop_box=st.session_state.crop_box,
                    cropped_image_path=cropped_path,
                    engine_used=st.session_state.engine,
                    eocr_pred=st.session_state.raw_text,  # Line-by-line OCR output
                    ocr_confidence=st.session_state.confidence,
                    correction_mode=getattr(st.session_state, 'correction_mode', 'as_is'),
                    eocr_corrected=st.session_state.corrected_text or st.session_state.raw_text,
                    target_language=st.session_state.target_lang if st.session_state.translated_text else None,
                    translated_text=st.session_state.translated_text if st.session_state.translated_text else None
                )
                
                st.success(f"✅ Record saved successfully! ID: {record_id}")
                
                # Reset session state for next image
                if st.button("🔄 Process Another Image", key="process_another_button"):
                    for key in list(st.session_state.keys()):
                        if key.startswith(('stage', 'original_', 'crop_', 'cropped_', 
                                         'preprocessed', 'raw_', 'corrected_', 'translated_')):
                            del st.session_state[key]
                    st.rerun()
            
            except Exception as e:
                st.error(f"❌ Failed to save record: {e}")

def view_records():
    """View saved OCR records - Cloud optimized"""
    
    st.header("📊 Saved OCR Records")
    
    # Get statistics
    try:
        stats = get_stats()
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Images", stats.get('total_images', 0))
        
        with col2:
            st.metric("Total Attempts", stats.get('total_attempts', 0))
        
        with col3:
            st.metric("Corrections Made", stats.get('total_corrections', 0))
        
        with col4:
            if stats.get('engine_usage'):
                most_used = max(stats['engine_usage'], key=stats['engine_usage'].get)
                st.metric("Most Used Engine", most_used.title())
            else:
                st.metric("Most Used Engine", "None")
        
        # Get all images (new schema)
        images = get_all_images()
        
        if images:
            # Create DataFrame for display
            df_data = []
            for idx, img in enumerate(images):
                # Get first attempt for display
                first_attempt = img['attempts'][0] if img['attempts'] else {}
                correction = img.get('correction', {})
                
                df_data.append({
                    'Index': idx,
                    'Image ID': img['image_id'][:8] + '...',  # Shortened
                    'Language': img.get('civ_board_language', 'N/A'),
                    'Filename': os.path.basename(img.get('original_image_path', 'N/A')),
                    'Engines Used': len(img['attempts']),
                    'Corrected': "Yes" if correction else "No",
                    'Has Translation': "Yes" if correction and correction.get('translated_text') else "No",
                    'Date': img.get('created_at', '')[:10] if img.get('created_at') else "N/A"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Detailed view
            st.subheader("📋 Image Details")
            
            # Limit records shown for performance
            max_records = 50
            display_images = images[:max_records] if len(images) > max_records else images
            
            if len(images) > max_records:
                st.info(f"Showing latest {max_records} images (total: {len(images)})")
            
            selected_idx = st.selectbox(
                "Select image to view:",
                options=range(len(display_images)),
                format_func=lambda x: f"{display_images[x]['image_id'][:12]} - {os.path.basename(display_images[x]['original_image_path'])}",
                key="image_selector"
            )
            
            if selected_idx is not None:
                img = display_images[selected_idx]
                
                # Display image details
                with st.expander("🖼️ Images", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if os.path.exists(img['original_image_path']):
                            st.image(img['original_image_path'], caption="Original Image")
                        else:
                            st.warning("Original image file not found")
                    
                    with col2:
                        if os.path.exists(img['cropped_image_path']):
                            st.image(img['cropped_image_path'], caption="Cropped Image")
                        else:
                            st.warning("Cropped image file not found")
                
                # Show all OCR attempts
                with st.expander("🔍 OCR Attempts (All Engines)", expanded=True):
                    st.write(f"**Total attempts:** {len(img['attempts'])}")
                    
                    for attempt in img['attempts']:
                        st.subheader(f"Engine: {attempt['engine_used'].title()}")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.code(attempt['eocr_pred'] or "", language='text')
                        with col2:
                            st.metric("Confidence", f"{attempt.get('ocr_confidence', 0):.1f}%")
                            st.caption(f"Run: {attempt.get('created_at', 'N/A')[:16]}")
                        st.divider()
                
                # Show correction if exists
                correction = img.get('correction')
                if correction:
                    with st.expander("✏️ Correction", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.subheader("Corrected Text")
                            st.code(correction['eocr_corrected'] or "", language='text')
                            
                            if correction.get('translated_text'):
                                st.subheader(f"Translation ({correction.get('target_language', 'N/A')})")
                                st.code(correction['translated_text'], language='text')
                        
                        with col2:
                            st.subheader("Technical Details")
                            st.write(f"**Image ID:** {img['image_id']}")
                            st.write(f"**CIV Board Language:** {correction.get('civ_board_language', 'N/A')}")
                            st.write(f"**Engine Used:** {correction.get('engine_used', 'N/A').title()}")
                            st.write(f"**Correction Mode:** {correction.get('correction_mode', 'N/A').replace('_', ' ').title()}")
                            st.write(f"**Created:** {correction.get('created_at', 'N/A')}")
                            
                            if correction.get('translated_text'):
                                st.subheader(f"Translation ({correction.get('target_language', 'N/A')})")
                                st.code(correction['translated_text'], language='text')
                    
                    # Delete button with proper confirmation flow
                    st.subheader("🗑️ Actions")
                    
                    # Get the image_id for this record
                    image_id_to_delete = img['image_id']
                    
                    # Initialize delete confirmation state
                    if 'confirm_delete' not in st.session_state:
                        st.session_state.confirm_delete = False
                    if 'delete_record_id' not in st.session_state:
                        st.session_state.delete_record_id = None
                    
                    # Check if we're confirming deletion for this specific record
                    if st.session_state.confirm_delete and st.session_state.delete_record_id == image_id_to_delete:
                        st.warning(f"⚠️ **Are you sure you want to delete this record?**")
                        st.info("This action cannot be undone. All data including images will be permanently deleted.")
                        
                        col_confirm, col_cancel = st.columns(2)
                        
                        with col_confirm:
                            if st.button("✅ Yes, Delete", type="primary", key=f"confirm_delete_{image_id_to_delete}"):
                                try:
                                    if delete_image(image_id_to_delete):
                                        st.success("✅ Record deleted successfully!")
                                        # Reset confirmation state
                                        st.session_state.confirm_delete = False
                                        st.session_state.delete_record_id = None
                                        # Wait a moment and rerun
                                        import time
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete record")
                                        st.session_state.confirm_delete = False
                                        st.session_state.delete_record_id = None
                                except Exception as e:
                                    st.error(f"❌ Error deleting record: {e}")
                                    st.session_state.confirm_delete = False
                                    st.session_state.delete_record_id = None
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_delete_{image_id_to_delete}"):
                                st.session_state.confirm_delete = False
                                st.session_state.delete_record_id = None
                                st.info("Deletion cancelled")
                                st.rerun()
                    else:
                        # Show initial delete button
                        if st.button(f"🗑️ Delete This Record", type="secondary", key=f"delete_record_button_{image_id_to_delete}"):
                            st.session_state.confirm_delete = True
                            st.session_state.delete_record_id = image_id_to_delete
                            st.rerun()
        
        else:
            st.info("No records found. Create some OCR extractions first!")
    
    except Exception as e:
        st.error(f"Error loading records: {e}")

if __name__ == "__main__":
    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
    
    # Initialize session state
    init_session_state()
    
    # Run main app
    try:
        main_app()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please refresh the page and try again.")