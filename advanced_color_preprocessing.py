"""
Advanced Color-Based Preprocessing for OCR
Handles different text/background color combinations with specialized techniques
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

class AdvancedColorPreprocessor:
    def __init__(self):
        self.preprocessing_strategies = {
            'blue_on_white': self.preprocess_blue_on_white,
            'black_on_white': self.preprocess_black_on_white,
            'black_on_yellow': self.preprocess_black_on_yellow,
            'dark_on_light': self.preprocess_dark_on_light,
            'colored_text_on_white': self.preprocess_colored_text_on_white,
            'low_contrast': self.preprocess_low_contrast,
            'high_contrast': self.preprocess_high_contrast
        }
    
    def analyze_color_combination(self, image):
        """Analyze image to determine the best preprocessing strategy"""
        # Convert to different color spaces for analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Get dominant colors using K-means with more clusters for better separation
        data = image.reshape((-1, 3))
        
        # Use more clusters to better separate text from background
        n_clusters = min(5, len(np.unique(data, axis=0)))  # Adaptive cluster count
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(data)
        colors = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        # Count pixel distribution
        unique, counts = np.unique(labels, return_counts=True)
        percentages = (counts / len(labels)) * 100
        
        # Sort colors by dominance
        sorted_indices = np.argsort(percentages)[::-1]
        dominant_colors = []
        
        for i in sorted_indices:
            color = colors[i].astype(int)
            percentage = percentages[i]
            dominant_colors.append({
                'rgb': color,
                'percentage': percentage,
                'brightness': np.mean(color)
            })
        
        # Enhanced background/text detection
        # Background is typically the most dominant color
        background_color = dominant_colors[0]
        
        # Text color is typically a less dominant but significant color
        # Look for a color that contrasts well with background
        text_color = dominant_colors[1] if len(dominant_colors) > 1 else background_color
        
        # Find the best contrasting color for text
        best_contrast_ratio = 0
        for color_info in dominant_colors[1:]:
            # Calculate simple contrast ratio
            bg_luma = 0.299 * background_color['rgb'][0] + 0.587 * background_color['rgb'][1] + 0.114 * background_color['rgb'][2]
            text_luma = 0.299 * color_info['rgb'][0] + 0.587 * color_info['rgb'][1] + 0.114 * color_info['rgb'][2]
            
            contrast = abs(bg_luma - text_luma)
            if contrast > best_contrast_ratio and color_info['percentage'] > 5:  # Must be at least 5% of image
                best_contrast_ratio = contrast
                text_color = color_info
        
        # Determine color combination type
        strategy = self.determine_strategy(dominant_colors, image)
        
        return {
            'strategy': strategy,
            'dominant_colors': dominant_colors,
            'color_analysis': {
                'background_color': background_color,
                'text_color': text_color,
                'contrast_colors': dominant_colors,
                'contrast_ratio': best_contrast_ratio
            }
        }
    
    def analyze_manual_colors(self, image, manual_text_color, manual_bg_color):
        """Analyze image using manually specified text and background colors"""
        
        # Convert manual colors to the expected format
        text_color_info = {
            'rgb': np.array(manual_text_color),
            'percentage': 0,  # Will be calculated
            'brightness': np.mean(manual_text_color)
        }
        
        bg_color_info = {
            'rgb': np.array(manual_bg_color),
            'percentage': 0,  # Will be calculated
            'brightness': np.mean(manual_bg_color)
        }
        
        # Calculate actual percentages of these colors in the image
        image_flat = image.reshape(-1, 3)
        
        # Find pixels close to manual colors (within threshold)
        color_threshold = 50  # Increased threshold for more forgiving matching
        
        # Calculate distances for text color
        text_distances = np.sqrt(np.sum((image_flat - manual_text_color) ** 2, axis=1))
        text_matches = np.sum(text_distances < color_threshold)
        text_color_info['percentage'] = (text_matches / len(image_flat)) * 100
        
        # Calculate distances for background color  
        bg_distances = np.sqrt(np.sum((image_flat - manual_bg_color) ** 2, axis=1))
        bg_matches = np.sum(bg_distances < color_threshold)
        bg_color_info['percentage'] = (bg_matches / len(image_flat)) * 100
        
        print(f"🎨 Manual Color Analysis:")
        print(f"   Text color {manual_text_color} found in {text_color_info['percentage']:.1f}% of image")
        print(f"   Background color {manual_bg_color} found in {bg_color_info['percentage']:.1f}% of image")
        
        # Create dominant colors list with manual colors first
        dominant_colors = [bg_color_info, text_color_info]
        
        # Determine strategy based on manual colors
        strategy = self.determine_strategy_from_manual_colors(manual_text_color, manual_bg_color)
        
        # Calculate contrast ratio
        bg_luma = 0.299 * manual_bg_color[0] + 0.587 * manual_bg_color[1] + 0.114 * manual_bg_color[2]
        text_luma = 0.299 * manual_text_color[0] + 0.587 * manual_text_color[1] + 0.114 * manual_text_color[2]
        contrast_ratio = abs(bg_luma - text_luma)
        
        return {
            'strategy': strategy,
            'dominant_colors': dominant_colors,
            'color_analysis': {
                'background_color': bg_color_info,
                'text_color': text_color_info,
                'contrast_colors': dominant_colors,
                'contrast_ratio': contrast_ratio
            },
            'manual_mode': True
        }
    
    def determine_strategy_from_manual_colors(self, text_color, bg_color):
        """Determine preprocessing strategy from manually specified colors"""
        
        text_brightness = np.mean(text_color)
        bg_brightness = np.mean(bg_color)
        
        # Check if background is white/light (brightness > 180 and low color variation)
        is_white_bg = bg_brightness > 180 and np.std(bg_color) < 50
        
        # Check if background is yellow (high R&G, low B)
        is_yellow_bg = (bg_color[0] > 150 and bg_color[1] > 150 and bg_color[2] < 100) or \
                      (bg_color[0] > 200 and bg_color[1] > 180 and bg_color[2] < 150)
        
        # Check if text is blue (B > R and B > G, with significant difference)
        is_blue_text = (text_color[2] > text_color[0] + 20 and text_color[2] > text_color[1] + 20 and text_color[2] > 80) or \
                       (text_color[2] > 100 and text_color[2] > text_color[0] and text_color[2] > text_color[1])
        
        # Check if text is dark/black
        is_dark_text = text_brightness < 100
        
        # Check if text is red
        is_red_text = (text_color[0] > text_color[1] + 20 and text_color[0] > text_color[2] + 20)
        
        # Check if text is green
        is_green_text = (text_color[1] > text_color[0] + 20 and text_color[1] > text_color[2] + 20)
        
        print(f"🔍 Manual Color Strategy Analysis:")
        print(f"   Background RGB: {bg_color}, brightness: {bg_brightness:.1f}")
        print(f"   Text RGB: {text_color}, brightness: {text_brightness:.1f}")
        print(f"   Is white bg: {is_white_bg}, Is yellow bg: {is_yellow_bg}")
        print(f"   Is blue text: {is_blue_text}, Is dark text: {is_dark_text}")
        print(f"   Is red text: {is_red_text}, Is green text: {is_green_text}")
        
        # Decision logic for manual colors
        if (is_white_bg or bg_brightness > 180) and is_blue_text:
            return 'blue_on_white'
        elif (is_yellow_bg) and is_dark_text:
            return 'black_on_yellow'
        elif is_white_bg and is_dark_text:
            return 'black_on_white'
        elif is_red_text:
            return 'colored_text_on_white'
        elif is_green_text:
            return 'colored_text_on_white'
        elif bg_brightness > text_brightness + 30:
            return 'dark_on_light'
        elif abs(bg_brightness - text_brightness) < 50:
            return 'low_contrast'
        else:
            return 'high_contrast'
    
    def determine_strategy(self, colors, image):
        """Determine the best preprocessing strategy based on color analysis"""
        if len(colors) < 2:
            return 'high_contrast'
        
        bg_color = colors[0]['rgb']
        text_color = colors[1]['rgb']
        
        bg_brightness = np.mean(bg_color)
        text_brightness = np.mean(text_color)
        
        # More sophisticated color detection
        
        # Check if background is white/light (brightness > 200 and low color variation)
        is_white_bg = bg_brightness > 180 and np.std(bg_color) < 50
        
        # Check if background is yellow (high R&G, low B)
        is_yellow_bg = (bg_color[0] > 150 and bg_color[1] > 150 and bg_color[2] < 100) or \
                      (bg_color[0] > 200 and bg_color[1] > 180 and bg_color[2] < 150)
        
        # Check for light colored backgrounds (could be white, cream, light yellow)
        is_light_bg = bg_brightness > 180
        
        # Check if text is blue (B > R and B > G, with significant difference)
        is_blue_text = (text_color[2] > text_color[0] + 20 and text_color[2] > text_color[1] + 20 and text_color[2] > 80) or \
                       (text_color[2] > 100 and text_color[2] > text_color[0] and text_color[2] > text_color[1])
        
        # Check if text is dark/black
        is_dark_text = text_brightness < 100
        
        # Enhanced blue detection using HSV
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Sample some pixels to check for blue hues
        h_values = hsv_image[:, :, 0].flatten()
        blue_hue_count = np.sum((h_values >= 100) & (h_values <= 130))  # Blue hue range
        total_pixels = len(h_values)
        blue_percentage = (blue_hue_count / total_pixels) * 100
        
        # Enhanced yellow detection
        yellow_hue_count = np.sum((h_values >= 20) & (h_values <= 30))  # Yellow hue range
        yellow_percentage = (yellow_hue_count / total_pixels) * 100
        
        print(f"🔍 Color Analysis Debug:")
        print(f"   Background RGB: {bg_color}, brightness: {bg_brightness:.1f}")
        print(f"   Text RGB: {text_color}, brightness: {text_brightness:.1f}")
        print(f"   Blue pixels: {blue_percentage:.1f}%, Yellow pixels: {yellow_percentage:.1f}%")
        print(f"   Is white bg: {is_white_bg}, Is yellow bg: {is_yellow_bg}")
        print(f"   Is blue text: {is_blue_text}, Is dark text: {is_dark_text}")
        
        # Decision logic with enhanced detection
        if (is_white_bg or is_light_bg) and (is_blue_text or blue_percentage > 10):
            return 'blue_on_white'
        elif (is_yellow_bg or yellow_percentage > 20) and (is_dark_text or bg_brightness > text_brightness + 50):
            return 'black_on_yellow'
        elif blue_percentage > 15:  # Strong blue presence indicates blue text
            return 'blue_on_white'
        elif yellow_percentage > 25:  # Strong yellow presence indicates yellow background
            return 'black_on_yellow'
        elif is_white_bg and is_dark_text:
            return 'black_on_white'
        elif is_light_bg and not is_dark_text:
            return 'colored_text_on_white'
        elif bg_brightness > text_brightness + 30:
            return 'dark_on_light'
        elif abs(bg_brightness - text_brightness) < 50:
            return 'low_contrast'
        else:
            return 'high_contrast'
    
    def preprocess_blue_on_white(self, image, color_info):
        """Specialized preprocessing for blue text on white background (like img_069)"""
        results = {}
        
        # Original
        results['original'] = image.copy()
        
        # Method 1: HSV-based blue isolation
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Define blue color range in HSV
        lower_blue = np.array([100, 50, 50])   # Lower HSV values for blue
        upper_blue = np.array([130, 255, 255]) # Upper HSV values for blue
        
        # Create mask for blue regions
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Invert mask to make blue text black and rest white
        blue_isolated = cv2.bitwise_not(blue_mask)
        results['hsv_blue_isolation'] = blue_isolated
        
        # Method 2: LAB color space processing
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel = lab[:, :, 0]
        a_channel = lab[:, :, 1]
        b_channel = lab[:, :, 2]
        
        # B channel emphasizes blue-yellow differences
        b_enhanced = cv2.equalizeHist(b_channel)
        
        # Threshold on B channel (blue text will be darker)
        _, b_thresh = cv2.threshold(b_enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['lab_b_channel'] = b_thresh
        
        # Method 3: Blue channel extraction and enhancement
        blue_channel = image[:, :, 2]  # Blue channel in RGB
        
        # Enhance blue channel contrast
        blue_enhanced = cv2.equalizeHist(blue_channel)
        
        # Apply adaptive threshold
        blue_adaptive = cv2.adaptiveThreshold(
            blue_enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        results['blue_channel_enhanced'] = blue_adaptive
        
        # Method 4: Color distance-based segmentation
        text_color = color_info['color_analysis']['text_color']['rgb']
        
        # Calculate color distance from estimated text color
        color_distance = np.sqrt(np.sum((image - text_color) ** 2, axis=2))
        
        # Normalize and threshold
        color_distance_norm = ((color_distance - color_distance.min()) / 
                              (color_distance.max() - color_distance.min()) * 255).astype(np.uint8)
        
        _, color_thresh = cv2.threshold(color_distance_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['color_distance_segmentation'] = color_thresh
        
        # Method 5: Morphological operations for noise reduction
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Apply morphological operations to the best result
        morph_cleaned = cv2.morphologyEx(blue_isolated, cv2.MORPH_CLOSE, kernel)
        morph_cleaned = cv2.morphologyEx(morph_cleaned, cv2.MORPH_OPEN, kernel)
        results['morphological_cleaned'] = morph_cleaned
        
        return results
    
    def preprocess_black_on_white(self, image, color_info):
        """Standard preprocessing for black text on white background"""
        results = {}
        results['original'] = image.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        results['grayscale'] = gray
        
        # Simple binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['otsu_threshold'] = binary
        
        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        results['adaptive_threshold'] = adaptive
        
        return results
    
    def preprocess_black_on_yellow(self, image, color_info):
        """Preprocessing for black text on yellow background (like image_5)"""
        results = {}
        results['original'] = image.copy()
        
        # Method 1: HSV-based yellow background removal
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Define yellow color range
        lower_yellow = np.array([20, 50, 50])
        upper_yellow = np.array([30, 255, 255])
        
        # Create mask for yellow regions
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Create inverse mask for non-yellow regions (text)
        text_mask = cv2.bitwise_not(yellow_mask)
        results['yellow_background_removed'] = text_mask
        
        # Method 2: LAB color space - emphasize text
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        b_channel = lab[:, :, 2]  # Blue-Yellow channel
        
        # Yellow background will have high B values, black text will have lower B values
        _, lab_thresh = cv2.threshold(b_channel, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        results['lab_yellow_separation'] = lab_thresh
        
        # Method 3: Saturation-based separation
        s_channel = hsv[:, :, 1]  # Saturation channel
        
        # Yellow background has high saturation, black text has low saturation
        _, sat_thresh = cv2.threshold(s_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['saturation_based'] = sat_thresh
        
        return results
    
    def preprocess_colored_text_on_white(self, image, color_info):
        """General preprocessing for colored text on white background"""
        results = {}
        results['original'] = image.copy()
        
        # Method 1: Luminance-based separation
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel = lab[:, :, 0]
        
        # Apply CLAHE to enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)
        
        _, luminance_thresh = cv2.threshold(l_enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        results['luminance_based'] = luminance_thresh
        
        # Method 2: Color saturation enhancement
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        v_channel = hsv[:, :, 2]  # Value channel
        
        # Enhance value channel
        v_enhanced = cv2.equalizeHist(v_channel)
        _, value_thresh = cv2.threshold(v_enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        results['value_enhanced'] = value_thresh
        
        return results
    
    def preprocess_dark_on_light(self, image, color_info):
        """General preprocessing for dark text on light background"""
        results = {}
        results['original'] = image.copy()
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Enhanced contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        results['contrast_enhanced'] = enhanced
        
        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)
        results['adaptive_enhanced'] = adaptive
        
        return results
    
    def preprocess_low_contrast(self, image, color_info):
        """Specialized preprocessing for low contrast images"""
        results = {}
        results['original'] = image.copy()
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Histogram equalization
        eq = cv2.equalizeHist(gray)
        results['histogram_equalized'] = eq
        
        # CLAHE with aggressive settings
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        clahe_enhanced = clahe.apply(gray)
        results['clahe_aggressive'] = clahe_enhanced
        
        # Unsharp masking for enhancement
        gaussian = cv2.GaussianBlur(gray, (9, 9), 10.0)
        unsharp = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
        results['unsharp_mask'] = unsharp
        
        return results
    
    def preprocess_high_contrast(self, image, color_info):
        """Standard preprocessing for high contrast images"""
        results = {}
        results['original'] = image.copy()
        
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        results['grayscale'] = gray
        
        # Simple threshold works well for high contrast
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['otsu_threshold'] = binary
        
        return results
    
    def process_image(self, image, manual_text_color=None, manual_bg_color=None):
        """Main processing function that analyzes and applies appropriate preprocessing
        
        Args:
            image: Input image array
            manual_text_color: Optional RGB tuple for text color (r, g, b)
            manual_bg_color: Optional RGB tuple for background color (r, g, b)
        """
        # If manual colors provided, use them to override automatic detection
        if manual_text_color is not None and manual_bg_color is not None:
            analysis = self.analyze_manual_colors(image, manual_text_color, manual_bg_color)
            print(f"🎨 Manual colors specified - Text: {manual_text_color}, Background: {manual_bg_color}")
        else:
            # Analyze color combination automatically
            analysis = self.analyze_color_combination(image)
        
        strategy = analysis['strategy']
        
        print(f"🎨 Detected strategy: {strategy}")
        print(f"📊 Background: {analysis['color_analysis']['background_color']['rgb']}")
        print(f"📝 Text: {analysis['color_analysis']['text_color']['rgb']}")
        
        # Apply appropriate preprocessing strategy
        if strategy in self.preprocessing_strategies:
            results = self.preprocessing_strategies[strategy](image, analysis)
        else:
            # Fallback to general preprocessing
            results = self.preprocess_dark_on_light(image, analysis)
        
        # Add analysis info to results
        results['analysis'] = analysis
        
        return results
    
    def get_best_result(self, processed_results, ocr_engine_func=None):
        """Select the best preprocessing result based on OCR quality or heuristics"""
        
        # If OCR engine function is provided, test each result
        if ocr_engine_func:
            best_result = None
            best_score = 0
            
            for name, image in processed_results.items():
                if name == 'analysis' or name == 'original':
                    continue
                
                try:
                    # Test OCR on this processed image
                    text, confidence = ocr_engine_func(image)
                    score = len(text.strip()) * (confidence / 100)  # Simple scoring
                    
                    if score > best_score:
                        best_score = score
                        best_result = (name, image)
                        
                except Exception as e:
                    continue
            
            return best_result if best_result else ('original', processed_results['original'])
        
        # Fallback: return the first non-original result
        for name, image in processed_results.items():
            if name != 'analysis' and name != 'original':
                return (name, image)
        
        return ('original', processed_results['original'])

def test_specific_images():
    """Test the preprocessing on specific problem images"""
    
    # Test cases
    test_cases = [
        {
            'path': r"C:\Users\pawar\Downloads\Dataset\Tushar\img_069.jpg",
            'description': "Blue text on white background",
            'expected_strategy': 'blue_on_white'
        },
        {
            'path': r"C:\Users\pawar\Downloads\Dataset\Tushar\image_5.jpg", 
            'description': "Black text on yellow background",
            'expected_strategy': 'black_on_yellow'
        }
    ]
    
    preprocessor = AdvancedColorPreprocessor()
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['description']}")
        print(f"📁 File: {test_case['path']}")
        print("-" * 60)
        
        try:
            # Load image
            image = cv2.imread(test_case['path'])
            if image is None:
                print("❌ Could not load image")
                continue
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = preprocessor.process_image(image_rgb)
            
            # Display results info
            strategy = results['analysis']['strategy']
            print(f"✅ Strategy used: {strategy}")
            
            if strategy == test_case['expected_strategy']:
                print(f"🎯 Strategy matches expected: {test_case['expected_strategy']}")
            else:
                print(f"⚠️ Strategy mismatch. Expected: {test_case['expected_strategy']}, Got: {strategy}")
            
            # Show available preprocessing methods
            methods = [k for k in results.keys() if k not in ['analysis', 'original']]
            print(f"🔧 Available methods: {', '.join(methods)}")
            
        except Exception as e:
            print(f"❌ Error processing image: {str(e)}")

if __name__ == "__main__":
    print("🎨 Advanced Color-Based Preprocessing Test")
    print("=" * 60)
    test_specific_images()