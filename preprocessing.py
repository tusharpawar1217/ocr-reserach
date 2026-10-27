"""
Image preprocessing functions for OCR
Reuses the exact validated preprocessing pipeline
"""

import cv2
import numpy as np
from typing import Tuple

def preprocess_image(image_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Preprocess image for OCR using the exact validated function
    
    Args:
        image_bgr: Input image in BGR format (from cv2 or PIL converted)
    
    Returns:
        Tuple of (gray, enhanced, binary) images
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Adaptive threshold
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )
    
    return gray, enhanced, binary

def prepare_image_for_ocr(image_array: np.ndarray, use_binary: bool = False) -> np.ndarray:
    """
    Prepare image for OCR based on preprocessing choice
    
    Args:
        image_array: Input image array
        use_binary: If True, return binary image; else return enhanced grayscale
    
    Returns:
        Processed image ready for OCR
    """
    # Convert PIL RGB to BGR if needed
    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
        # Assume RGB from PIL, convert to BGR for cv2
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    else:
        image_bgr = image_array
    
    gray, enhanced, binary = preprocess_image(image_bgr)
    
    return binary if use_binary else enhanced

def convert_pil_to_cv2(pil_image):
    """Convert PIL Image to OpenCV format"""
    import numpy as np
    # Convert PIL RGB to numpy array
    image_array = np.array(pil_image)
    # Convert RGB to BGR for OpenCV
    if len(image_array.shape) == 3:
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    else:
        image_bgr = image_array
    return image_bgr

def convert_cv2_to_pil(cv2_image):
    """Convert OpenCV image to PIL format"""
    from PIL import Image
    # Convert BGR to RGB
    if len(cv2_image.shape) == 3:
        image_rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = cv2_image
    return Image.fromarray(image_rgb)

if __name__ == "__main__":
    # Test preprocessing functions
    print("Testing preprocessing functions...")
    
    # Create a test image
    test_image = np.zeros((100, 200, 3), dtype=np.uint8)
    test_image[20:80, 50:150] = [255, 255, 255]  # White rectangle
    
    try:
        gray, enhanced, binary = preprocess_image(test_image)
        
        print(f"✅ Preprocessing successful:")
        print(f"   Original shape: {test_image.shape}")
        print(f"   Gray shape: {gray.shape}")
        print(f"   Enhanced shape: {enhanced.shape}")
        print(f"   Binary shape: {binary.shape}")
        
        # Test prepare_image_for_ocr
        enhanced_output = prepare_image_for_ocr(test_image, use_binary=False)
        binary_output = prepare_image_for_ocr(test_image, use_binary=True)
        
        print(f"   Enhanced output shape: {enhanced_output.shape}")
        print(f"   Binary output shape: {binary_output.shape}")
        
        print("✅ All preprocessing tests passed!")
        
    except Exception as e:
        print(f"❌ Preprocessing test failed: {e}")