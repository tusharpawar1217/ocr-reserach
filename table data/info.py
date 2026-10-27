import os
import numpy as np
from PIL import Image
from pathlib import Path

def analyze_irsdhi_dataset(base_path):
    """
    Analyze IRSDhi dataset (BSTD) to calculate statistics for Table 1.
    
    Args:
        base_path: Path to IRSDhi dataset root
    
    Returns:
        Dictionary with statistics
    """
    splits = ['train', 'test', 'val']
    
    all_resolutions = []
    all_word_counts = []
    total_characters = 0
    total_images = 0
    
    for split in splits:
        split_path = os.path.join(base_path, split)
        images_txt = os.path.join(split_path, f'{split}_images.txt')
        labels_txt = os.path.join(split_path, f'{split}_labels.txt')
        
        # Check if files exist
        if not os.path.exists(images_txt) or not os.path.exists(labels_txt):
            print(f"Warning: Missing files in {split} split")
            continue
        
        # Read image paths and labels
        with open(images_txt, 'r', encoding='utf-8') as f:
            image_paths = [line.strip() for line in f.readlines()]
        
        with open(labels_txt, 'r', encoding='utf-8') as f:
            labels = [line.strip() for line in f.readlines()]
        
        # Verify counts match
        if len(image_paths) != len(labels):
            print(f"Warning: Mismatch in {split} - {len(image_paths)} images vs {len(labels)} labels")
        
        print(f"\nProcessing {split} split: {len(image_paths)} images")
        
        # Process each image
        for idx, (img_path, label) in enumerate(zip(image_paths, labels)):
            # Progress indicator every 1000 images
            if (idx + 1) % 1000 == 0:
                print(f"  Processed {idx + 1}/{len(image_paths)} images...")
            
            # Construct full image path
            full_img_path = os.path.join(base_path, img_path)
            
            if not os.path.exists(full_img_path):
                continue
            
            try:
                # Get image resolution (faster than opening full image)
                with Image.open(full_img_path) as img:
                    width, height = img.size
                    resolution = width * height
                    all_resolutions.append((width, height, resolution))
                
                # Count words and characters in label
                words = label.strip().split()
                word_count = len(words)
                char_count = len(label.replace(' ', ''))  # Characters without spaces
                
                all_word_counts.append(word_count)
                total_characters += char_count
                total_images += 1
                
            except Exception as e:
                continue
    
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
        'dataset': 'BSTD (IRSDhi)',
        'total_images': total_images,
        'min_resolution': f"{min_res[0]}×{min_res[1]} ({min_res[2]:,} pixels)",
        'max_resolution': f"{max_res[0]}×{max_res[1]} ({max_res[2]:,} pixels)",
        'avg_resolution': f"{avg_width:.2f}×{avg_height:.2f} ({np.mean(resolutions_only):,.2f} pixels)",
        'std_dev_resolution': f"{std_dev_res:,.2f}",
        'words_per_image': f"{avg_words_per_image:.2f}",
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
    print(f"# of Characters:          {results['total_characters']}")
    print(f"Avg Characters/image:     {results['avg_chars_per_image']}")
    print("="*80)

if __name__ == "__main__":
    # Dataset path
    irsdhi_path = r"C:\Users\pawar\Downloads\IRSDhi\IRSDhi"
    
    print("Analyzing BSTD (IRSDhi) Dataset...")
    print(f"Dataset path: {irsdhi_path}")
    
    # Analyze dataset
    results = analyze_irsdhi_dataset(irsdhi_path)
    
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
