"""
Pre-download PaddleOCR models to avoid timeout issues
Run this script once before using PaddleOCR in the app
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("PaddleOCR Model Download Script")
print("=" * 60)
print("\nThis will download PaddleOCR models (~76MB).")
print("This may take several minutes depending on your internet speed.")
print("Progress will be shown below.\n")
print("-" * 60)

try:
    print("\n[1/2] Importing PaddleOCR...")
    from paddleocr import PaddleOCR
    print("✓ Import successful")
    
    print("\n[2/2] Initializing PaddleOCR (downloading models if needed)...")
    print("This step may take 5-10 minutes on slow connections.")
    print("Please be patient...\n")
    
    ocr = PaddleOCR(
        use_textline_orientation=True,
        lang='en',
        enable_mkldnn=False
    )
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS! PaddleOCR models are downloaded and ready to use.")
    print("=" * 60)
    print("\nYou can now use PaddleOCR in the Streamlit app.")
    print("The models are cached at: C:\\Users\\pawar\\.paddlex\\official_models\\")
    
except Exception as e:
    print("\n" + "=" * 60)
    print("✗ ERROR during model download:")
    print("=" * 60)
    print(f"\n{str(e)}\n")
    print("Troubleshooting:")
    print("1. Check your internet connection")
    print("2. Try running the script again")
    print("3. If problems persist, try using a VPN or different network")
    sys.exit(1)
