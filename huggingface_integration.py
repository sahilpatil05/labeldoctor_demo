"""
Hugging Face Integration for OCR and Allergen Detection
Provides cloud-based models instead of local OCR engines
"""

import requests
import os
from typing import List, Dict, Optional

class HuggingFaceOCR:
    """Use Hugging Face API for OCR"""
    
    def __init__(self, api_token: str = None):
        """
        Initialize Hugging Face OCR
        
        Args:
            api_token: Hugging Face API token (from settings/tokens)
                      Get from: https://huggingface.co/settings/tokens
        """
        self.api_token = api_token or os.getenv('HF_API_TOKEN')
        if not self.api_token:
            raise ValueError(
                "Hugging Face API token not found. "
                "Set HF_API_TOKEN environment variable or pass api_token parameter"
            )
        
        # OCR Model options:
        # 1. GLM-OCR: Best for food labels
        # 2. PaddleOCR: Fast and accurate
        # 3. Qwen-OCR: Multi-language support
        self.ocr_model = "zai-org/GLM-OCR"  # Excellent for food labels
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        self.api_url = "https://api-inference.huggingface.co/models"
        
        print("✓ Hugging Face OCR initialized")
        print(f"  Model: {self.ocr_model}")
    
    def extract_text(self, image_np) -> str:
        """
        Extract text from image using Hugging Face OCR
        
        Args:
            image_np: numpy array of image
            
        Returns:
            Extracted text from image
        """
        import cv2
        import io
        
        try:
            # Convert numpy array to bytes
            _, buffer = cv2.imencode('.jpg', image_np)
            image_bytes = buffer.tobytes()
            
            # Call Hugging Face API
            response = requests.post(
                f"{self.api_url}/{self.ocr_model}",
                headers=self.headers,
                data=image_bytes,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from response
                if isinstance(result, list) and len(result) > 0:
                    # GLM-OCR returns list of detection results
                    extracted_text = ""
                    for item in result:
                        if isinstance(item, dict) and 'text' in item:
                            extracted_text += item['text'] + "\n"
                    return extracted_text.strip()
                elif isinstance(result, dict) and 'text' in result:
                    return result['text']
                else:
                    return str(result)
            else:
                raise Exception(f"HF API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ OCR extraction failed: {e}")
            return ""


class HuggingFaceAllergenDetector:
    """Use Hugging Face API for allergen detection"""
    
    def __init__(self, api_token: str = None):
        """
        Initialize Hugging Face allergen detector
        
        Args:
            api_token: Hugging Face API token
        """
        self.api_token = api_token or os.getenv('HF_API_TOKEN')
        if not self.api_token:
            raise ValueError("Hugging Face API token not found")
        
        # Zero-shot classification model for allergen detection
        # This model can classify text without needing training
        self.model = "facebook/bart-large-mnli"  # Or use "cross-encoder/nli-deberta-v3-large"
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        self.api_url = "https://api-inference.huggingface.co/models"
        
        print("✓ Hugging Face Allergen Detector initialized")
        print(f"  Model: {self.model}")
    
    def detect_allergens(self, ingredient: str, allergen_names: List[str]) -> Optional[str]:
        """
        Detect if ingredient contains allergen using zero-shot classification
        
        Args:
            ingredient: Ingredient text to check
            allergen_names: List of allergen names to check against
            
        Returns:
            Matched allergen name or None
        """
        try:
            # Prepare candidate labels
            labels = allergen_names + ["not an allergen"]
            
            response = requests.post(
                f"{self.api_url}/{self.model}",
                headers=self.headers,
                json={
                    "inputs": f"This ingredient is: {ingredient}",
                    "parameters": {"candidate_labels": labels}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Get top label
                if 'labels' in result and 'scores' in result:
                    top_label = result['labels'][0]
                    top_score = result['scores'][0]
                    
                    # If confidence is high enough and not "not an allergen"
                    if top_score > 0.5 and top_label != "not an allergen":
                        return top_label
                
                return None
            else:
                print(f"⚠ HF API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Allergen detection failed: {e}")
            return None


class HuggingFaceIntegration:
    """Combined Hugging Face integration"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv('HF_API_TOKEN')
        if not self.api_token:
            raise ValueError(
                "HF_API_TOKEN not set. "
                "Get token from: https://huggingface.co/settings/tokens"
            )
        
        self.ocr = HuggingFaceOCR(self.api_token)
        self.allergen_detector = HuggingFaceAllergenDetector(self.api_token)
    
    def process_image(self, image_np) -> str:
        """Extract text from image"""
        return self.ocr.extract_text(image_np)
    
    def check_allergen(self, ingredient: str, allergens: List[str]) -> Optional[str]:
        """Check if ingredient contains allergen"""
        return self.allergen_detector.detect_allergens(ingredient, allergens)


# Quick setup guide
if __name__ == "__main__":
    print("""
    ============================================
    Hugging Face Integration Setup Guide
    ============================================
    
    1. Get your API token:
       - Go to: https://huggingface.co/settings/tokens
       - Create new token (read access is fine)
       - Copy the token
    
    2. Set environment variable:
       export HF_API_TOKEN="your_token_here"
    
       Or on Windows (PowerShell):
       $env:HF_API_TOKEN="your_token_here"
    
    3. Test the integration:
       from huggingface_integration import HuggingFaceIntegration
       hf = HuggingFaceIntegration()
       
    4. Use in your Flask app:
       - See updated app_api.py for usage examples
    """)
