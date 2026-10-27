import os
import numpy as np
from PIL import Image
from pathlib import Path

def analyze_tushar_dataset(base_path):
    """
    Analyze Tushar dataset to calculate statistics for Table 1.
    
    Args:
        base_path: Path to Tushar dataset root
    
    Returns:
        Dictionary with statistics
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    all_resolutions = []
    total_images = 0
    errors = 0
    
    print(f"Scanning directory: {base_path}")
    
    # Get all image files
    image_files = []
    for file in os.listdir(base_path):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(os.path.join(base_path, file))
    
    print(f"Found {len(image_files)} image files")
    
    # Process each image
    for idx, img_path in enumerate(image_files):
        try:
            # Get image resolution
            with Image.open(img_path) as img:
                width, height = img.size
                resolution = width * height
                all_resolutions.append((width, height, resolution))
                total_images += 1
            
            # Progress indicator every 10 images
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(image_files)} images...")
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            errors += 1
    
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
    
    results = {
        'dataset': 'Tushar Dataset',
        'total_images': total_images,
        'errors': errors,
        'min_resolution': f"{min_res[0]}×{min_res[1]} ({min_res[2]:,} pixels)",
        'max_resolution': f"{max_res[0]}×{max_res[1]} ({max_res[2]:,} pixels)",
        'avg_resolution': f"{avg_width:.2f}×{avg_height:.2f} ({np.mean(resolutions_only):,.2f} pixels)",
        'std_dev_resolution': f"{std_dev_res:,.2f}",
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
    if results['errors'] > 0:
        print(f"Errors:                   {results['errors']}")
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
    print("="*80)

if __name__ == "__main__":
    # Dataset path
    tushar_path = r"C:\Users\pawar\Downloads\Dataset\Tushar"
    
    print("Analyzing Tushar Dataset...")
    print(f"Dataset path: {tushar_path}")
    
    # Analyze dataset
    results = analyze_tushar_dataset(tushar_path)
    
    # Print results
    if results:
        print_table_row(results)
        
        # Also print in simple format for table filling
        print("\nSimple Format (for table):")
        print(f"Dataset: {results['dataset']}")
        print(f"Total Images: {results['total_images']}")
        print(f"Min: {results['min_resolution']}")
        print(f"Max: {results['max_resolution']}")
        print(f"Avg: {results['avg_resolution']}")
        print(f"Std Dev: {results['std_dev_resolution']}")
    else:
        print("Failed to analyze dataset")
