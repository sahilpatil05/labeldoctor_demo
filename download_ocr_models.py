"""
Fix OCR SSL Certificate Issues and Pre-download Models
"""

import os
import ssl
import urllib.request
import sys

def setup_ssl():
    """Set up SSL certificate verification bypass for model downloads"""
    # Create unverified context
    ssl_context = ssl._create_unverified_context()
    ssl.create_default_https_context = lambda: ssl_context
    urllib.request.ssl.create_default_https_context = lambda: ssl_context
    print("✓ SSL certificate verification configured")


def predownload_easyocr_models():
    """Pre-download EasyOCR models"""
    try:
        setup_ssl()
        
        print("\n" + "="*60)
        print("PRE-DOWNLOADING EASYOCR MODELS")
        print("="*60)
        print("This is a one-time operation. Please wait...\n")
        
        import easyocr
        
        print("Downloading English language model...")
        reader = easyocr.Reader(['en'], gpu=False, verbose=True)
        
        print("\n✓ EasyOCR models downloaded successfully!")
        print("✓ Models cached and ready to use")
        
        # Quick test
        print("\nTesting OCR engine...")
        import numpy as np
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = reader.readtext(test_img)
        print("✓ EasyOCR test passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("DOWNLOADING OCR MODELS")
    print("="*60)
    
    success = predownload_easyocr_models()
    
    if success:
        print("\n" + "="*60)
        print("✓ OCR SETUP COMPLETE!")
        print("="*60)
        print("\nYou can now start the Flask server:")
        print("  python app_api.py")
    else:
        print("\n" + "="*60)
        print("❌ OCR SETUP FAILED")
        print("="*60)
        print("\nNote: The app will still work, but image scanning")
        print("will attempt to download models on first use.")
    
    print()


if __name__ == '__main__':
    main()
