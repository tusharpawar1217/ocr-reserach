import os
import numpy as np
from PIL import Image
from pathlib import Path

def find_all_images(root_path, extensions=['.jpg', '.jpeg', '.png', '.bmp', '.tiff']):
    """
    Recursively find all image files in directory tree
    """
    all_images = []
    
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                all_images.append(os.path.join(root, file))
    
    return all_images

def analyze_gt_files(gt_files, base_path):
    """
    Analyze GT files to count images and characters
    """
    total_images = 0
    total_characters = 0
    total_words = 0
    missing_images = []
    found_images = []
    
    for gt_file in gt_files:
        if not os.path.exists(gt_file):
            continue
        
        with open(gt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Split by tab: image_path<tab>word
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                
                img_relative_path, word = parts
                
                # Construct full image path
                img_full_path = os.path.join(base_path, img_relative_path)
                
                # Check if image exists
                if os.path.exists(img_full_path):
                    found_images.append(img_full_path)
                    total_images += 1
                    total_words += 1
                    total_characters += len(word)
                else:
                    missing_images.append(img_relative_path)
    
    return {
        'total_images': total_images,
        'total_words': total_words,
        'total_characters': total_characters,
        'missing_images': missing_images,
        'found_images': found_images
    }

def get_image_resolutions(image_paths, sample_size=None):
    """
    Get min/max resolutions from image files
    """
    resolutions = []
    widths = []
    heights = []
    processed = 0
    errors = 0
    
    # Sample if needed (with fixed seed for consistency)
    if sample_size and len(image_paths) > sample_size:
        import random
        random.seed(42)  # Fixed seed for consistent results
        image_paths = random.sample(image_paths, sample_size)
    
    for i, img_path in enumerate(image_paths):
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                resolutions.append((width, height, width * height))
                widths.append(width)
                heights.append(height)
                processed += 1
        except Exception as e:
            errors += 1
    
    if not resolutions:
        return None
    
    # Calculate statistics
    resolutions_only = [r[2] for r in resolutions]
    min_res = min(resolutions, key=lambda x: x[2])
    max_res = max(resolutions, key=lambda x: x[2])
    
    # Overall resolution stats
    avg_res = np.mean(resolutions_only)
    std_dev_res = np.std(resolutions_only)
    
    # Width stats
    min_width = min(widths)
    max_width = max(widths)
    avg_width = np.mean(widths)
    std_dev_width = np.std(widths)
    
    # Height stats
    min_height = min(heights)
    max_height = max(heights)
    avg_height = np.mean(heights)
    std_dev_height = np.std(heights)
    
    return {
        'min_width': min_res[0],
        'min_height': min_res[1],
        'min_pixels': min_res[2],
        'max_width': max_res[0],
        'max_height': max_res[1],
        'max_pixels': max_res[2],
        'avg_pixels': avg_res,
        'std_dev_pixels': std_dev_res,
        'processed': processed,
        'errors': errors,
        # Additional width/height statistics
        'width_min': min_width,
        'width_max': max_width,
        'width_avg': avg_width,
        'width_std': std_dev_width,
        'height_min': min_height,
        'height_max': max_height,
        'height_avg': avg_height,
        'height_std': std_dev_height
    }

def main():
    # Suppress verbose output
    base_path = r"C:\Users\pawar\Downloads\hindi\hindi"
    
    # Part 1: Count ALL images in all subfolders (silent)
    all_images = find_all_images(base_path)
    
    # Part 2: Analyze GT files (silent)
    gt_files = [
        r"C:\Users\pawar\Downloads\hindi\hindi\file\train_gt.txt",
        r"C:\Users\pawar\Downloads\hindi\hindi\file\val_gt.txt",
        r"C:\Users\pawar\Downloads\hindi\hindi\file\test_gt.txt"
    ]
    
    gt_stats = analyze_gt_files(gt_files, base_path)
    
    # Part 3: Get resolutions (silent sampling)
    sample_size = min(10000, len(gt_stats['found_images']))
    res_stats = get_image_resolutions(gt_stats['found_images'], sample_size=sample_size)
    
    # Final Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY FOR TABLE")
    print("="*80)
    print(f"Total images in GT files: {gt_stats['total_images']:,}")
    print(f"Total words: {gt_stats['total_words']:,}")
    print(f"Total characters: {gt_stats['total_characters']:,}")
    if res_stats:
        print(f"\nResolution (Height × Width):")
        print(f"  Min: {res_stats['min_height']}×{res_stats['min_width']} ({res_stats['min_pixels']:,} pixels)")
        print(f"  Max: {res_stats['max_height']}×{res_stats['max_width']} ({res_stats['max_pixels']:,} pixels)")
        print(f"  Avg: {res_stats['height_avg']:.0f}×{res_stats['width_avg']:.0f} ({res_stats['avg_pixels']:,.0f} pixels)")
        print(f"\nResolution (pixels) Stats:")
        print(f"  Avg: {res_stats['avg_pixels']:,.0f} pixels")
        print(f"  Std Dev: {res_stats['std_dev_pixels']:,.2f} pixels")
    if gt_stats['total_images'] > 0:
        print(f"\nText Stats:")
        print(f"  Words per image: {gt_stats['total_words'] / gt_stats['total_images']:.2f}")
        print(f"  Avg chars per word: {gt_stats['total_characters'] / gt_stats['total_words']:.2f}")
    print("="*80)

if __name__ == "__main__":
    main()
