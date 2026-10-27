"""
Advanced OCR Pipeline for Google-Level Accuracy
Implements state-of-the-art text detection and recognition
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import torch
import easyocr
import pytesseract

# Optional imports for advanced features
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ TrOCR features disabled. Install transformers library for advanced recognition: `pip install transformers`")

import re
from typing import List, Dict, Tuple, Optional
import json

try:
    from scipy.spatial import distance as dist
    from imutils import perspective
    ADVANCED_LIBS_AVAILABLE = True
except ImportError:
    ADVANCED_LIBS_AVAILABLE = False

import math

class AdvancedTextDetector:
    """Modern text detection using CRAFT-like approaches"""
    
    def __init__(self):
        self.easyocr_reader = None
        self.detection_models = {
            'easyocr': 'EasyOCR (CRAFT-based)',
            'craft': 'CRAFT Detection',
            'dbnet': 'DBNet Real-time'
        }
    
    def detect_text_regions_advanced(self, image, method='easyocr', confidence_threshold=0.3):
        """Advanced text detection with multiple methods"""
        if method == 'easyocr':
            return self._detect_with_easyocr(image, confidence_threshold)
        elif method == 'craft':
            return self._detect_with_craft_simulation(image)
        else:
            return self._detect_with_easyocr(image, confidence_threshold)
    
    def _detect_with_easyocr(self, image, threshold):
        """Enhanced EasyOCR detection with better preprocessing"""
        if self.easyocr_reader is None:
            self.easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
        
        # Advanced preprocessing
        processed_image = self._preprocess_for_detection(image)
        
        # Multi-scale detection
        detections = []
        scales = [1.0, 1.2, 0.8]  # Multiple scales for better detection
        
        for scale in scales:
            if scale != 1.0:
                h, w = processed_image.shape[:2]
                scaled_img = cv2.resize(processed_image, (int(w * scale), int(h * scale)))
            else:
                scaled_img = processed_image
            
            results = self.easyocr_reader.readtext(scaled_img, detail=1)
            
            for bbox, text, conf in results:
                if conf > threshold:
                    # Scale back coordinates if necessary
                    if scale != 1.0:
                        bbox = np.array(bbox) / scale
                    
                    detections.append({
                        'bbox': self._normalize_bbox(bbox),
                        'text': text,
                        'confidence': conf,
                        'detection_method': 'easyocr'
                    })
        
        # Remove duplicate detections
        return self._remove_duplicate_detections(detections)
    
    def _preprocess_for_detection(self, image):
        """Advanced preprocessing for better text detection"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Multi-stage preprocessing pipeline
        
        # 1. Noise reduction
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 2. Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 3. Edge-preserving smoothing
        smoothed = cv2.edgePreservingFilter(enhanced, flags=1, sigma_s=50, sigma_r=0.4)
        
        # 4. Sharpening kernel
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(smoothed, -1, kernel)
        
        return sharpened
    
    def _normalize_bbox(self, bbox):
        """Convert bbox to standard format [x_min, y_min, x_max, y_max]"""
        if isinstance(bbox, list) and len(bbox) == 4 and len(bbox[0]) == 2:
            # EasyOCR format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            bbox_array = np.array(bbox)
            x_min = int(bbox_array[:, 0].min())
            y_min = int(bbox_array[:, 1].min())
            x_max = int(bbox_array[:, 0].max())
            y_max = int(bbox_array[:, 1].max())
            return [x_min, y_min, x_max, y_max]
        return bbox
    
    def _remove_duplicate_detections(self, detections):
        """Remove overlapping detections using IoU threshold"""
        if not detections:
            return []
        
        # Sort by confidence
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        filtered = []
        for detection in detections:
            is_duplicate = False
            for existing in filtered:
                iou = self._calculate_iou(detection['bbox'], existing['bbox'])
                if iou > 0.5:  # IoU threshold for duplicates
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(detection)
        
        return filtered
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU) of two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Calculate intersection
        x_min = max(x1_min, x2_min)
        y_min = max(y1_min, y2_min)
        x_max = min(x1_max, x2_max)
        y_max = min(y1_max, y2_max)
        
        if x_min >= x_max or y_min >= y_max:
            return 0.0
        
        intersection = (x_max - x_min) * (y_max - y_min)
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _detect_with_craft_simulation(self, image):
        """Simulate CRAFT-like detection using advanced edge detection"""
        # Preprocess image
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
        
        # Multi-scale edge detection
        edges1 = cv2.Canny(gray, 50, 150, apertureSize=3)
        edges2 = cv2.Canny(gray, 100, 200, apertureSize=3)
        edges = cv2.bitwise_or(edges1, edges2)
        
        # Morphological operations to connect text characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for i, contour in enumerate(contours):
            # Filter by area and aspect ratio
            area = cv2.contourArea(contour)
            if area < 100:  # Too small
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio (text-like regions)
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio < 0.1 or aspect_ratio > 10:  # Not text-like
                continue
            
            # Extract text region for recognition
            text_region = gray[y:y+h, x:x+w]
            
            detections.append({
                'bbox': [x, y, x+w, y+h],
                'text': f"region_{i}",  # Placeholder, would need OCR
                'confidence': 0.8,  # Simulated confidence
                'detection_method': 'craft_sim'
            })
        
        return detections

class AdvancedTextRecognizer:
    """Modern text recognition using Transformer architectures"""
    
    def __init__(self):
        self.trocr_processor = None
        self.trocr_model = None
        self.loaded_model = None
    
    def recognize_text_regions(self, image, detections, method='easyocr'):
        """Advanced text recognition with multiple methods"""
        if method == 'trocr':
            return self._recognize_with_trocr(image, detections)
        elif method == 'easyocr_enhanced':
            return self._recognize_with_easyocr_enhanced(image, detections)
        else:
            return self._recognize_with_easyocr_enhanced(image, detections)
    
    def _load_trocr_model(self):
        """Load TrOCR model (lightweight version for demo)"""
        if not TRANSFORMERS_AVAILABLE:
            print("TrOCR requires transformers library. Install with: `pip install transformers`")
            return False
            
        try:
            if self.trocr_processor is None:
                print("🤖 Loading TrOCR model (first time may take a moment)...")
                self.trocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
                self.trocr_model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed")
                print("✅ TrOCR model loaded successfully!")
            return True
        except Exception as e:
            print(f"TrOCR model loading failed: {e}. Falling back to EasyOCR.")
            return False
    
    def _recognize_with_trocr(self, image, detections):
        """Recognize text using TrOCR transformer model"""
        if not self._load_trocr_model():
            return self._recognize_with_easyocr_enhanced(image, detections)
        
        results = []
        for detection in detections:
            try:
                # Extract text region
                bbox = detection['bbox']
                x_min, y_min, x_max, y_max = bbox
                text_region = image[y_min:y_max, x_min:x_max]
                
                # Convert to PIL Image
                if len(text_region.shape) == 3:
                    pil_image = Image.fromarray(text_region)
                else:
                    pil_image = Image.fromarray(text_region).convert('RGB')
                
                # Process with TrOCR
                pixel_values = self.trocr_processor(pil_image, return_tensors="pt").pixel_values
                generated_ids = self.trocr_model.generate(pixel_values)
                generated_text = self.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                detection['text'] = generated_text
                detection['recognition_method'] = 'trocr'
                results.append(detection)
                
            except Exception as e:
                print(f"TrOCR recognition failed for region: {e}")
                # Fallback to original text or empty
                detection['text'] = detection.get('text', '')
                detection['recognition_method'] = 'fallback'
                results.append(detection)
        
        return results
    
    def _recognize_with_easyocr_enhanced(self, image, detections):
        """Enhanced EasyOCR recognition with preprocessing"""
        reader = easyocr.Reader(['en', 'hi'], gpu=False)
        
        results = []
        for detection in detections:
            try:
                # Extract and preprocess text region
                bbox = detection['bbox']
                x_min, y_min, x_max, y_max = bbox
                
                # Add padding around text region
                padding = 5
                h, w = image.shape[:2]
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(w, x_max + padding)
                y_max = min(h, y_max + padding)
                
                text_region = image[y_min:y_max, x_min:x_max]
                
                # Enhance text region
                enhanced_region = self._enhance_text_region(text_region)
                
                # Recognize text
                ocr_results = reader.readtext(enhanced_region, detail=1)
                
                if ocr_results:
                    # Take the best result
                    best_result = max(ocr_results, key=lambda x: x[2])  # highest confidence
                    detection['text'] = best_result[1]
                    detection['confidence'] = best_result[2]
                else:
                    detection['text'] = ''
                    detection['confidence'] = 0.0
                
                detection['recognition_method'] = 'easyocr_enhanced'
                results.append(detection)
                
            except Exception as e:
                detection['text'] = detection.get('text', '')
                detection['confidence'] = 0.0
                detection['recognition_method'] = 'error'
                results.append(detection)
        
        return results
    
    def _enhance_text_region(self, region):
        """Enhance individual text region for better recognition"""
        if len(region.shape) == 3:
            gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
        else:
            gray = region.copy()
        
        # Resize if too small
        h, w = gray.shape
        if h < 32 or w < 32:
            scale_factor = max(32/h, 32/w, 2.0)
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4,4))
        enhanced = clahe.apply(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Sharpening
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(blurred, -1, kernel)
        
        return sharpened

class ConfidenceAnalyzer:
    """Analyze and visualize OCR confidence scores"""
    
    def __init__(self):
        pass
    
    def analyze_confidence_patterns(self, detections):
        """Analyze confidence patterns in OCR results"""
        if not detections:
            return {}
        
        confidences = [d.get('confidence', 0) for d in detections]
        
        analysis = {
            'total_regions': len(detections),
            'avg_confidence': np.mean(confidences),
            'min_confidence': np.min(confidences),
            'max_confidence': np.max(confidences),
            'std_confidence': np.std(confidences),
            'low_confidence_count': sum(1 for c in confidences if c < 0.7),
            'medium_confidence_count': sum(1 for c in confidences if 0.7 <= c < 0.9),
            'high_confidence_count': sum(1 for c in confidences if c >= 0.9),
        }
        
        return analysis
    
    def get_confidence_color(self, confidence):
        """Get color based on confidence level"""
        if confidence >= 0.9:
            return "#28a745"  # Green - High
        elif confidence >= 0.7:
            return "#ffc107"  # Yellow - Medium  
        elif confidence >= 0.5:
            return "#fd7e14"  # Orange - Low
        else:
            return "#dc3545"  # Red - Very Low
    
    def create_confidence_heatmap(self, image, detections):
        """Create confidence heatmap overlay"""
        overlay_image = image.copy()
        draw = ImageDraw.Draw(overlay_image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection.get('confidence', 0)
            
            x_min, y_min, x_max, y_max = bbox
            
            # Get confidence color
            color = self.get_confidence_color(confidence)
            
            # Draw bounding box with confidence color
            draw.rectangle([x_min, y_min, x_max, y_max], outline=color, width=3)
            
            # Draw confidence score
            conf_text = f"{confidence:.1%}"
            text_bbox = draw.textbbox((0, 0), conf_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            
            # Background for confidence text
            draw.rectangle([x_min, y_min-20, x_min + text_width + 4, y_min], fill=color)
            draw.text((x_min + 2, y_min - 18), conf_text, fill='white', font=font)
        
        return overlay_image
class StructuredDataExtractor:
    """Extract and parse structured data from OCR results"""
    
    def __init__(self):
        self.field_patterns = {
            'latitude': r'(?i)lat(?:itude)?[:=\s]*([+-]?\d+\.?\d*)',
            'longitude': r'(?i)long?(?:itude)?[:=\s]*([+-]?\d+\.?\d*)',
            'grant_number': r'(?i)grant\s*no?\.?\s*[:=]*\s*(\w+)',
            'date': r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            'time': r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)',
            'phone': r'(\d{10}|\d{3}[-.\s]\d{3}[-.\s]\d{4})',
            'amount': r'(?i)(?:rs?\.?\s*|₹\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            'percentage': r'(\d+(?:\.\d+)?%)',
        }
    
    def extract_structured_fields(self, all_text):
        """Extract structured fields from combined OCR text"""
        extracted_fields = {}
        
        for field_name, pattern in self.field_patterns.items():
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                extracted_fields[field_name] = matches[0] if len(matches) == 1 else matches
        
        return extracted_fields
    
    def validate_extracted_data(self, fields):
        """Validate extracted structured data"""
        validation_results = {}
        
        # Validate latitude
        if 'latitude' in fields:
            try:
                lat = float(fields['latitude'])
                validation_results['latitude'] = {
                    'valid': -90 <= lat <= 90,
                    'value': lat,
                    'message': 'Valid' if -90 <= lat <= 90 else 'Invalid range'
                }
            except:
                validation_results['latitude'] = {
                    'valid': False,
                    'value': fields['latitude'],
                    'message': 'Invalid format'
                }
        
        # Validate longitude  
        if 'longitude' in fields:
            try:
                lng = float(fields['longitude'])
                validation_results['longitude'] = {
                    'valid': -180 <= lng <= 180,
                    'value': lng,
                    'message': 'Valid' if -180 <= lng <= 180 else 'Invalid range'
                }
            except:
                validation_results['longitude'] = {
                    'valid': False,
                    'value': fields['longitude'],
                    'message': 'Invalid format'
                }
        
        # Validate phone numbers
        if 'phone' in fields:
            phone = re.sub(r'[^\d]', '', str(fields['phone']))
            validation_results['phone'] = {
                'valid': len(phone) == 10,
                'value': phone,
                'message': 'Valid' if len(phone) == 10 else 'Invalid length'
            }
        
        return validation_results

class InteractiveCorrectionInterface:
    """Advanced interface for text correction with confidence visualization"""
    
    def __init__(self):
        self.analyzer = ConfidenceAnalyzer()
        self.extractor = StructuredDataExtractor()
    
    def analyze_corrections_needed(self, image, detections):
        """Analyze which detections likely need correction"""
        
        # Initialize corrections tracking
        corrections = {i: det['text'] for i, det in enumerate(detections)}
        
        # Confidence analysis
        if detections:
            analysis = self.analyzer.analyze_confidence_patterns(detections)
            return analysis, corrections
        
        return {}, corrections
    
    def get_correction_suggestions(self, detections):
        """Get suggestions for text corrections based on confidence and patterns"""
        
        suggestions = []
        
        for i, detection in enumerate(detections):
            confidence = detection.get('confidence', 0)
            text = detection.get('text', '')
            
            suggestion = {
                'region_index': i,
                'original_text': text,
                'confidence': confidence,
                'needs_review': confidence < 0.7,
                'likely_errors': self._identify_likely_errors(text, confidence),
                'suggestions': self._get_text_suggestions(text)
            }
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _identify_likely_errors(self, text, confidence):
        """Identify likely OCR errors in text"""
        errors = []
        
        # Low confidence
        if confidence < 0.6:
            errors.append("Low confidence detection")
        
        # Common OCR artifacts
        if re.search(r'[|\\]+', text):
            errors.append("Contains OCR artifacts (| or \\)")
        
        # Very short or very long text
        if len(text.strip()) < 2:
            errors.append("Very short text")
        elif len(text) > 100:
            errors.append("Unusually long text")
        
        # Mixed numbers and symbols without clear structure
        if re.search(r'[0-9][^0-9\s][0-9]', text) and not re.search(r'\d+[-/]\d+', text):
            errors.append("Irregular number/symbol pattern")
        
        return errors
    
    def _get_text_suggestions(self, text):
        """Get basic text correction suggestions"""
        suggestions = []
        
        # Common OCR corrections
        corrections_map = {
            '|': 'I',
            '0': 'O',
            '5': 'S',
            '1': 'l',
            'rn': 'm',
            '8': 'B'
        }
        
        suggested_text = text
        for wrong, correct in corrections_map.items():
            if wrong in text:
                suggested_text = suggested_text.replace(wrong, correct)
                suggestions.append(f"Replace '{wrong}' with '{correct}'")
        
        if suggestions:
            return {'suggested_text': suggested_text, 'corrections': suggestions}
        
        return {'suggested_text': text, 'corrections': []}