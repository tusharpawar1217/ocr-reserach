import os
import json
import numpy as np
from PIL import Image
from pathlib import Path

def analyze_bstd_detection_dataset(base_path, json_files):
    """
    Analyze BSTD detection dataset to calculate statistics for Table 1.
    
    Args:
        base_path: Path to detection dataset root
        json_files: List of JSON annotation files
    
    Returns:
        Dictionary with statistics
    """
    all_resolutions = []
    all_word_counts = []
    total_characters = 0
    total_words = 0
    total_images = 0
    
    # Load all JSON files
    all_annotations = {}
    for json_file in json_files:
        json_path = os.path.join(base_path, json_file)
        if not os.path.exists(json_path):
            print(f"Warning: JSON file not found - {json_path}")
            continue
        
        print(f"Loading {json_file}...")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_annotations.update(data)
    
    print(f"\nTotal images in annotations: {len(all_annotations)}")
    
    # Process each image
    processed = 0
    for image_key, image_data in all_annotations.items():
        # Parse image key to get folder and filename
        # Format: "A_image_1005" -> folder "A", file "image_1005.jpg" (or .png)
        parts = image_key.split('_', 1)
        if len(parts) != 2:
            print(f"Warning: Invalid image key format - {image_key}")
            continue
        
        folder = parts[0]
        image_name = parts[1]
        
        # Try different image extensions
        img_path = None
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            potential_path = os.path.join(base_path, folder, f"{image_name}{ext}")
            if os.path.exists(potential_path):
                img_path = potential_path
                break
        
        if img_path is None:
            print(f"Warning: Image not found for key {image_key}")
            continue
        
        try:
            # Get image resolution
            with Image.open(img_path) as img:
                width, height = img.size
                resolution = width * height
                all_resolutions.append((width, height, resolution))
            
            # Process annotations for this image
            annotations = image_data.get('annotations', {})
            image_word_count = 0
            image_char_count = 0
            
            for ann_key, ann_data in annotations.items():
                text = ann_data.get('text', '')
                if text:
                    # Count words
                    words = text.strip().split()
                    image_word_count += len(words)
                    
                    # Count characters (without spaces)
                    chars = text.replace(' ', '')
                    image_char_count += len(chars)
            
            all_word_counts.append(image_word_count)
            total_words += image_word_count
            total_characters += image_char_count
            total_images += 1
            processed += 1
            
            # Progress indicator
            if processed % 500 == 0:
                print(f"  Processed {processed}/{len(all_annotations)} images...")
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
    
    # Calculate statistics
    if not all_resolutions:
        print("Error: No images were processed!")
        return None
    
    # Extract widths and heights
    widths = [r[0] for r in all_resolutions]
    heights = [r[1] for r in all_resolutions]
    resolutions_only = [r[2] for r in all_resolutions]
    
    # Resolution statistics
    min_res = min(all_resolutions, key=lambda x: x[2])
    max_res = max(all_resolutions, key=lambda x: x[2])
    std_dev_res = np.std(resolutions_only)
    
    # Width and height statistics
    min_width = min(widths)
    max_width = max(widths)
    avg_width = np.mean(widths)
    std_dev_width = np.std(widths)
    
    min_height = min(heights)
    max_height = max(heights)
    avg_height = np.mean(heights)
    std_dev_height = np.std(heights)
    
    # Text statistics
    avg_words_per_image = np.mean(all_word_counts)
    
    results = {
        'dataset': 'BSTD (Detection)',
        'total_images': total_images,
        'min_resolution': f"{min_res[0]}×{min_res[1]} ({min_res[2]:,} pixels)",
        'max_resolution': f"{max_res[0]}×{max_res[1]} ({max_res[2]:,} pixels)",
        'avg_resolution': f"{avg_width:.2f}×{avg_height:.2f} ({np.mean(resolutions_only):,.2f} pixels)",
        'std_dev_resolution': f"{std_dev_res:,.2f}",
        'words_per_image': f"{avg_words_per_image:.2f}",
        'total_words': f"{total_words:,}",
        'total_characters': f"{total_characters:,}",
        'avg_chars_per_image': f"{total_characters/total_images:.2f}",
        # Width/Height statistics
        'width_min': min_width,
        'width_max': max_width,
        'width_avg': f"{avg_width:.2f}",
        'width_std': f"{std_dev_width:.2f}",
        'height_min': min_height,
        'height_max': max_height,
        'height_avg': f"{avg_height:.2f}",
        'height_std': f"{std_dev_height:.2f}"
    }
    
    return results

def print_table_row(results):
    """Print results in table format"""
    if results is None:
        print("No results to display")
        return
    
    print("\n" + "="*80)
    print("TABLE 1 - Dataset Statistics")
    print("="*80)
    print(f"Dataset:                  {results['dataset']}")
    print(f"Total Images:             {results['total_images']}")
    print(f"Min Resolution:           {results['min_resolution']}")
    print(f"Max Resolution:           {results['max_resolution']}")
    print(f"Avg Resolution:           {results['avg_resolution']}")
    print(f"Std. Dev. (Resolution):   {results['std_dev_resolution']} pixels")
    print(f"\nWidth Statistics:")
    print(f"  Min: {results['width_min']}, Max: {results['width_max']}")
    print(f"  Avg: {results['width_avg']}, Std Dev: {results['width_std']}")
    print(f"\nHeight Statistics:")
    print(f"  Min: {results['height_min']}, Max: {results['height_max']}")
    print(f"  Avg: {results['height_avg']}, Std Dev: {results['height_std']}")
    print(f"\n# of Words/image:         {results['words_per_image']}")
    print(f"Total Words:              {results['total_words']}")
    print(f"# of Characters:          {results['total_characters']}")
    print(f"Avg Characters/image:     {results['avg_chars_per_image']}")
    print("="*80)

if __name__ == "__main__":
    # Dataset path
    detection_path = r"C:\Users\pawar\Downloads\detection\detection"
    
    # JSON annotation files
    json_files = [
        # "BSTD_release_v1.json",
        "BSTD_v17.57.json"
    ]
    
    print("Analyzing BSTD Detection Dataset...")
    print(f"Dataset path: {detection_path}")
    
    # Analyze dataset
    results = analyze_bstd_detection_dataset(detection_path, json_files)
    
    # Print results
    if results:
        print_table_row(results)
        
        # Also print in CSV format for easy table filling
        print("\nCSV Format (for table):")
        print(f"BSTD,{results['min_resolution']},{results['max_resolution']},"
              f"{results['std_dev_resolution']},{results['words_per_image']},"
              f"{results['total_characters']}")
    else:
        print("Failed to analyze dataset")
