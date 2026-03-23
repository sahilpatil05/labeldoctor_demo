"""
PaddleOCR Model Pre-Download Script
This script pre-downloads and caches OCR models to avoid initialization issues
"""

import os
import sys

def setup_paddle_env():
    """Set up environment variables for PaddleOCR"""
    # Set cache directory
    cache_dir = os.path.expanduser('~/.paddleocr')
    os.environ['PADDLE_CACHE_DIR'] = cache_dir
    os.environ['PADDLEOCR_MODEL_PATH'] = cache_dir
    
    # Disable model source check to allow offline mode
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    
    # Set inference model path
    os.environ['PADDLE_INFERENCE_MODEL_PATH'] = cache_dir
    
    print(f"✓ PaddleOCR cache directory set to: {cache_dir}")
    return cache_dir


def predownload_paddle_models():
    """Pre-download PaddleOCR models"""
    try:
        import warnings
        warnings.filterwarnings('ignore')
        
        cache_dir = setup_paddle_env()
        
        print("\n" + "="*60)
        print("PRE-DOWNLOADING PADDLEOCR MODELS")
        print("="*60)
        print("This is a one-time operation. Please wait...\n")
        
        # Import after env setup
        from paddleocr import PaddleOCR
        
        print("Downloading detection model...")
        ocr = PaddleOCR(
            lang=['en'],
            use_angle_cls=False,
            show_log=True,
            cache_dir=cache_dir
        )
        
        print("\n✓ Models downloaded successfully!")
        print(f"✓ Models cached in: {cache_dir}")
        
        # Test the OCR
        print("\nTesting OCR engine...")
        import numpy as np
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = ocr.ocr(test_img, cls=False)
        print("✓ OCR test passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during model download: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check internet connectivity")
        print("2. Ensure you have enough disk space (~100MB)")
        print("3. Try running with: python fix_paddle_ocr.py --clean")
        return False


def clean_paddle_cache():
    """Clean paddle OCR cache"""
    import shutil
    cache_dir = os.path.expanduser('~/.paddleocr')
    
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"✓ Cleared cache: {cache_dir}")
            return True
        except Exception as e:
            print(f"⚠ Could not clear cache: {e}")
            return False
    else:
        print(f"✓ Cache already empty: {cache_dir}")
        return True


def install_easyocr_fallback():
    """Install EasyOCR as fallback"""
    import subprocess
    
    try:
        print("\nInstalling EasyOCR as fallback...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'easyocr', '--quiet'])
        print("✓ EasyOCR installed successfully")
        return True
    except Exception as e:
        print(f"⚠ Could not install EasyOCR: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix PaddleOCR initialization issues')
    parser.add_argument('--clean', action='store_true', help='Clean cache before downloading')
    parser.add_argument('--easyocr', action='store_true', help='Install EasyOCR fallback')
    args = parser.parse_args()
    
    if args.clean:
        print("Cleaning PaddleOCR cache...")
        clean_paddle_cache()
        print()
    
    if args.easyocr:
        install_easyocr_fallback()
        print()
    
    # Download models
    success = predownload_paddle_models()
    
    print("\n" + "="*60)
    if success:
        print("✓ PADDLE OCR SETUP COMPLETE!")
        print("="*60)
        print("\nYou can now start the Flask server:")
        print("  python app_api.py")
    else:
        print("❌ PADDLE OCR SETUP FAILED")
        print("="*60)
        print("\nTo use EasyOCR fallback instead:")
        print("  python fix_paddle_ocr.py --easyocr")
    print()


if __name__ == '__main__':
    main()
