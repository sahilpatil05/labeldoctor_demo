from flask import Flask, render_template, request, jsonify, Response, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import base64
import cv2
print(f"[STARTUP] OpenCV version: {cv2.__file__}")
print(f"[STARTUP] OpenCV library: {cv2.getBuildInformation() if hasattr(cv2, 'getBuildInformation') else 'N/A'}")
import numpy as np
import os
from PIL import Image
import io
import uuid
from datetime import datetime
from functools import wraps
import ssl
import urllib.request
import traceback
import re
import sys
import warnings
import itertools

# ========== FIX PILLOW COMPATIBILITY ==========
# Handle Pillow 10.0+ deprecation of Image.ANTIALIAS
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
    print("[STARTUP] Applied Pillow 10.0+ compatibility fix (ANTIALIAS -> LANCZOS)")

# ========== IMPORT ENHANCED PREPROCESSING ==========
try:
    from image_preprocessor import OCRImagePreprocessor, AdaptiveLineThresholdCalculator
    PREPROCESSOR_AVAILABLE = True
    print("[STARTUP] ✓ Enhanced preprocessor loaded successfully")
except ImportError as import_error:
    print(f"[STARTUP] ⚠ Enhanced preprocessor not available: {import_error}")
    print("[STARTUP] Will use minimal PIL-based fallback")
    PREPROCESSOR_AVAILABLE = False
except Exception as unexpected_error:
    print(f"[STARTUP] ✗ Unexpected error loading preprocessor: {unexpected_error}")
    PREPROCESSOR_AVAILABLE = False

# ========== SSL CERTIFICATE FIX ==========
# Fix SSL certificate verification issues
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

try:
    from urllib.request import urlopen
    import ssl as ssl_module
    context = ssl_module._create_unverified_context()
    ssl_module._create_default_https_context = lambda: context
except:
    pass

# ========== OCR SETUP ==========
# Using EasyOCR for ingredient scanning

# Try to import OCR libraries
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    print("[STARTUP] ✓ EasyOCR loaded successfully")
except ImportError:
    EASYOCR_AVAILABLE = False
    print("[STARTUP] ⚠ EasyOCR not available")

# ========== HUGGING FACE INTEGRATION ==========
# Check if using Hugging Face cloud models (recommended for mobile)
USE_HUGGINGFACE = os.getenv('USE_HUGGINGFACE', 'False').lower() == 'true'
HF_API_TOKEN = os.getenv('HF_API_TOKEN', '')

if USE_HUGGINGFACE:
    try:
        from huggingface_integration import HuggingFaceOCR
        HF_AVAILABLE = True
        print("✓ Hugging Face integration available - will use cloud models")
    except ImportError as e:
        print(f"⚠ Hugging Face integration not found: {e}")
        HF_AVAILABLE = False
else:
    HF_AVAILABLE = False
    print("[INFO] Using local OCR engines (PaddleOCR/EasyOCR)")

# ========== NER (NAMED ENTITY RECOGNITION) INTEGRATION ==========
# Import NER processor for enhanced ingredient extraction
try:
    from ner_processor import IngredientNERProcessor, NER_AVAILABLE, ner_processor
    print(f"✓ NER processor imported successfully (spaCy available: {NER_AVAILABLE})")
except ImportError as e:
    print(f"⚠ NER processor import failed: {e}")
    ner_processor = None
    NER_AVAILABLE = False

# ========== INGREDIENT DETECTION INTEGRATION ==========
# Import ingredient detector for comprehensive ingredient database searching
try:
    from ingredient_detector import IngredientDetector, INGREDIENT_DETECTOR_AVAILABLE
    ingredient_detector = IngredientDetector()
    print(f"✓ Ingredient detector imported successfully")
except ImportError as e:
    print(f"⚠ Ingredient detector import failed: {e}")
    ingredient_detector = None
    INGREDIENT_DETECTOR_AVAILABLE = False
except Exception as e:
    print(f"⚠ Ingredient detector initialization warning: {e}")
    ingredient_detector = None
    INGREDIENT_DETECTOR_AVAILABLE = False

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'labeldoctor_secret_key_2026'  # Change this to a secure key

# Configure session settings
app.config['SESSION_COOKIE_SECURE'] = False  # Allow over HTTP for localhost
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access to session
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow navigation between pages
app.config['PERMANENT_SESSION_LIFETIME'] = 604800  # 7 days

CORS(app, supports_credentials=True)  # Enable credentials in CORS

# Add headers for camera and media access
@app.after_request
def add_security_headers(response):
    """Add security headers for camera and media access"""
    # Allow camera and microphone access from all origins (for localhost testing)
    response.headers['Permissions-Policy'] = 'camera=(*), microphone=(*), geolocation=(*)'
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    return response

# Database Configuration
import os
# Support both local SQLite and cloud databases (PostgreSQL for Render)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # For Render/Cloud deployment (PostgreSQL)
    # Fix for SQLAlchemy 1.4+ with psycopg2
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # For local development (SQLite)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labeldoctor.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path.replace(os.sep, "/")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Global OCR instance management
ocr = None
ocr_engine = None  # Track which engine is being used
ocr_lock = __import__('threading').Lock()

class EasyOCRWrapper:
    """EasyOCR wrapper for text detection and recognition"""
    def __init__(self, reader):
        self.reader = reader
        self.engine_type = 'easyocr'
        self.lang_map = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'zh': 'Chinese', 'ja': 'Japanese', 'ar': 'Arabic', 'hi': 'Hindi', 'pt': 'Portuguese'
        }
    
    def ocr(self, image, cls=False):
        """Process image with EasyOCR
        
        Args:
            image: numpy array or file path
            cls: ignored (for API compatibility)
        
        Returns:
            List of lines with format: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)], ...]
        """
        try:
            # EasyOCR expects images as numpy arrays in RGB format
            # PIL images converted to numpy are already RGB, so no conversion needed
            # (Avoiding cv2.cvtColor which triggered Gaussian blur errors)
            
            print(f"[EasyOCR] Starting readtext with image shape: {image.shape if hasattr(image, 'shape') else 'unknown'}")
            
            # Run OCR with detail=1 for detailed output (bounding boxes + text + confidence)
            # EasyOCR auto-detects language from reader initialization
            results = self.reader.readtext(image, detail=1, paragraph=False)
            
            print(f"[EasyOCR] Got {len(results) if results else 0} detections")
            
            # Convert EasyOCR format to PaddleOCR format for consistency
            # PaddleOCR format: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]]
            formatted_results = []
            if results:
                formatted_line = []
                for detection in results:
                    try:
                        bbox = detection[0]  # coordinates (list of 4 points)
                        text = detection[1]  # detected text
                        confidence = detection[2]  # confidence score (0-1)
                        # Convert to PaddleOCR format
                        formatted_line.append([bbox, (text, confidence)])
                    except (IndexError, TypeError) as parse_error:
                        print(f"[EasyOCR] Warning: Could not parse detection: {parse_error}")
                        continue
                
                formatted_results.append(formatted_line)
                print(f"[EasyOCR] Formatted into {len(formatted_line)} items")
            
            result = formatted_results if formatted_results else [[]]
            print(f"[EasyOCR] Returning: {len(result)} pages")
            return result
            
        except Exception as e:
            print(f"[EasyOCR] ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return [[]]


def merge_text_boxes_into_lines(ocr_results, y_threshold=None, image_height=None):
    """
    Merge OCR text boxes that belong to the same horizontal line.
    
    Handles EasyOCR format with confidence filtering to reduce noise.
    
    Args:
        ocr_results: Results from EasyOCR
        y_threshold: Maximum vertical distance for same line grouping (auto-calculated if None)
        image_height: Image height for adaptive threshold calculation
    
    Returns:
        List of merged lines with text and confidence
    """
    
    if not ocr_results:
        print("[MERGE] No OCR results to process")
        return []
    
    # ===== CONFIDENCE FILTERING =====
    # Only accept OCR results with confidence above this threshold
    MIN_CONFIDENCE = 0.4  # Only keep results with >40% confidence to reduce noise
    
    # Use adaptive threshold if not specified
    if y_threshold is None:
        y_threshold = 20  # Default
        if image_height is not None:
            # Calculate based on image height
            if image_height < 600:
                y_threshold = 15
            elif image_height < 1200:
                y_threshold = 20
            else:
                y_threshold = 30
            print(f"[MERGE] Using adaptive y_threshold={y_threshold} (image_height={image_height})")
    
    ocr_result = ocr_results[0]
    boxes = []
    
    try:
        # Try to access as new PaddleOCR format (OCRResult with dict interface)
        if hasattr(ocr_result, 'json') and isinstance(ocr_result.get('rec_texts'), list):
            print(f"[MERGE] Detected new PaddleOCR format (OCRResult)")
            
            rec_texts = ocr_result.get('rec_texts', [])
            rec_scores = ocr_result.get('rec_scores', [])
            rec_boxes = ocr_result.get('rec_boxes', [])
            
            if not rec_texts:
                print("[MERGE] No text extracted")
                return []
            
            print(f"[MERGE] Processing {len(rec_texts)} text elements")
            
            for text, score, box in zip(rec_texts, rec_scores, rec_boxes):
                text = str(text).strip()
                if len(text) < 2:
                    continue
                
                if len(box) >= 4:
                    y_center = (box[1] + box[3]) / 2
                    x_left = box[0]
                else:
                    continue
                
                boxes.append({
                    'text': text,
                    'confidence': float(score),
                    'y_center': y_center,
                    'x_left': x_left
                })
        
        # Try EasyOCR format: (coordinates, text, confidence) tuples
        # Coordinates are typically: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
        elif isinstance(ocr_result, list) and len(ocr_result) > 0:
            # Try to detect format by inspecting first element
            first_elem = ocr_result[0]
            
            # EasyOCR format: 3-tuple (coords, text, conf)
            if isinstance(first_elem, (tuple, list)) and len(first_elem) >= 2:
                # Check if it looks like EasyOCR (has coordinates) or PaddleOCR
                try:
                    coords = first_elem[0]
                    text_info = first_elem[1]
                    
                    # EasyOCR detection: coords should be list of [x, y] points
                    if isinstance(coords, (list, tuple)) and len(coords) > 0:
                        first_coord = coords[0]
                        if isinstance(first_coord, (list, tuple)) and len(first_coord) >= 2:
                            # This looks like EasyOCR format
                            print(f"[MERGE] Detected EasyOCR format")
                            
                            for detection in ocr_result:
                                if len(detection) >= 2:
                                    coords = detection[0]
                                    
                                    # Extract text and confidence
                                    if isinstance(detection[1], str):
                                        text = detection[1].strip()
                                        confidence = detection[2] if len(detection) >= 3 else 0.0
                                    elif isinstance(detection[1], tuple):
                                        text = detection[1][0] if len(detection[1]) > 0 else ""
                                        confidence = detection[1][1] if len(detection[1]) > 1 else 0.0
                                    else:
                                        text = str(detection[1]).strip()
                                        confidence = detection[2] if len(detection) >= 3 else 0.0
                                    
                                    text = text.strip()
                                    if len(text) < 2:
                                        continue
                                    
                                    # Apply confidence filter to reduce noise
                                    if float(confidence) < MIN_CONFIDENCE:
                                        print(f"[MERGE] Skipping low-confidence text: '{text}' (conf: {confidence:.2f})")
                                        continue
                                    
                                    # Calculate Y center from coordinates
                                    try:
                                        y_coords = [point[1] for point in coords if isinstance(point, (list, tuple)) and len(point) >= 2]
                                        y_center = sum(y_coords) / len(y_coords) if y_coords else 0
                                        x_coords = [point[0] for point in coords if isinstance(point, (list, tuple)) and len(point) >= 2]
                                        x_left = min(x_coords) if x_coords else 0
                                        
                                        boxes.append({
                                            'text': text,
                                            'confidence': float(confidence) if confidence else 0.0,
                                            'y_center': y_center,
                                            'x_left': x_left
                                        })
                                    except (ValueError, TypeError):
                                        continue
                        else:
                            # Try old PaddleOCR format
                            raise ValueError("Not recognized as EasyOCR, trying PaddleOCR format")
                    else:
                        raise ValueError("Not recognized as EasyOCR, trying PaddleOCR format")
                        
                except (ValueError, IndexError, TypeError) as e:
                    # Fall back to old PaddleOCR format
                    print(f"[MERGE] Detected old PaddleOCR format (list of tuples)")
                    
                    for detection in ocr_result:
                        if len(detection) >= 2:
                            try:
                                coords = detection[0]
                                text_info = detection[1]
                                
                                if isinstance(text_info, tuple):
                                    text = text_info[0]
                                    confidence = text_info[1] if len(text_info) > 1 else 0.0
                                else:
                                    text = str(text_info)
                                    confidence = 0.0
                                
                                text = text.strip()
                                if len(text) <= 1:
                                    continue
                                
                                # Handle coordinate formats
                                try:
                                    if isinstance(coords, (list, tuple)) and len(coords) > 0:
                                        y_coords = []
                                        x_coords = []
                                        
                                        for point in coords:
                                            if isinstance(point, (list, tuple)) and len(point) >= 2:
                                                y_coords.append(point[1])
                                                x_coords.append(point[0])
                                        
                                        if y_coords and x_coords:
                                            y_center = sum(y_coords) / len(y_coords)
                                            x_left = min(x_coords)
                                        else:
                                            continue
                                    else:
                                        continue
                                except TypeError:
                                    continue
                                
                                boxes.append({
                                    'text': text,
                                    'confidence': float(confidence),
                                    'y_center': y_center,
                                    'x_left': x_left
                                })
                            except (IndexError, TypeError, ValueError):
                                continue
            else:
                print(f"[MERGE] Cannot determine format of list elements")
                return []
        else:
            print(f"[MERGE] Unknown result format: {type(ocr_result)}")
            return []
        
        print(f"[MERGE] Extracted {len(boxes)} valid boxes")
        
        if not boxes:
            return []
        
        # Sort by Y position (top to bottom), then X (left to right)
        boxes.sort(key=lambda b: (b['y_center'], b['x_left']))
        
        # Group into lines by Y proximity with adaptive threshold
        lines = []
        current_line = [boxes[0]]
        
        for i in range(1, len(boxes)):
            y_diff = abs(boxes[i]['y_center'] - current_line[0]['y_center'])
            if y_diff <= y_threshold:
                current_line.append(boxes[i])
            else:
                lines.append(current_line)
                current_line = [boxes[i]]
        
        if current_line:
            lines.append(current_line)
        
        print(f"[MERGE] Grouped into {len(lines)} lines (y_threshold={y_threshold})")
        
        # Merge text within each line
        merged_lines = []
        for line in lines:
            line.sort(key=lambda b: b['x_left'])
            line_text = ' '.join([box['text'] for box in line])
            avg_confidence = sum([box['confidence'] for box in line]) / len(line) if line else 0.0
            merged_lines.append({
                'text': line_text,
                'confidence': avg_confidence
            })
        
        return merged_lines
        
    except Exception as e:
        print(f"[MERGE] Error processing results: {e}")
        import traceback
        traceback.print_exc()
        return []



def extract_full_text_from_ocr(ocr_results, image_height=None):
    """
    Extract complete text from OCR results with proper line handling.
    
    Args:
        ocr_results: OCR results from PaddleOCR or EasyOCR
        image_height: Image height for adaptive threshold calculation
    
    Returns:
        Tuple of (full_text, merged_lines_list, confidence_score)
    """
    merged_lines = merge_text_boxes_into_lines(ocr_results, image_height=image_height)
    
    if not merged_lines:
        return "", [], 0.0
    
    # Combine all lines into full text
    full_text = '\n'.join([line['text'] for line in merged_lines])
    
    # Calculate average confidence
    avg_confidence = sum([line['confidence'] for line in merged_lines]) / len(merged_lines) if merged_lines else 0.0
    
    return full_text, merged_lines, avg_confidence


def initialize_ocr():
    """Initialize OCR engine - uses EasyOCR exclusively for stability"""
    global ocr, ocr_engine
    
    with ocr_lock:
        # Check if already initialized
        if ocr is not None:
            # Skip health check - it was causing Gaussian blur kernel errors with small test images
            # Just return the cached OCR instance
            print(f"✓ {ocr_engine} engine is ready (using cached instance)")
            return ocr
        
        # ===== PRIMARY: EASYOCR (Stable on Windows CPU) =====
        if EASYOCR_AVAILABLE:
            try:
                print("Initializing EasyOCR (primary - stable for Windows CPU)...")
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    # Using compatible languages: Latin-script languages that work together well
                    # English, Spanish, French, Portuguese, German, Italian
                    reader = easyocr.Reader(['en', 'es', 'fr', 'pt', 'de', 'it'], gpu=False, verbose=False)
                ocr = EasyOCRWrapper(reader)
                ocr_engine = 'EasyOCR'
                print("✓ EasyOCR initialized successfully for multilingual text")
                print("  Supported languages: English, Spanish, French, Portuguese, German, Italian")
                print("  Processing speed: ~1-2s per image")
                return ocr
            except Exception as e:
                print(f"❌ EasyOCR multilingual initialization failed: {e}")
                print("   Attempting English-only EasyOCR...")
                try:
                    # Fallback to English only (always works)
                    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                    ocr = EasyOCRWrapper(reader)
                    ocr_engine = 'EasyOCR'
                    print("✓ EasyOCR initialized successfully (English support)")
                    return ocr
                except Exception as e2:
                    print(f"❌ EasyOCR English-only initialization failed: {e2}")
                    print("   Falling back to Hugging Face...")
        
        # ===== FALLBACK TO HUGGING FACE (Cloud-based) =====
        if HF_AVAILABLE and USE_HUGGINGFACE:
            try:
                print("Initializing Hugging Face OCR (cloud-based)...")
                if not HF_API_TOKEN:
                    raise ValueError("HF_API_TOKEN not set but USE_HUGGINGFACE=True")
                ocr = HuggingFaceOCR(api_token=HF_API_TOKEN)
                ocr_engine = 'HuggingFace'
                print("✓ Hugging Face OCR initialized successfully")
                return ocr
            except Exception as e:
                print(f"❌ Hugging Face OCR failed: {e}")
        
        # No engines available
        print("❌ No OCR engine available!")
        print("   Available options:")
        print(f"   - EasyOCR: {EASYOCR_AVAILABLE} (primary - stable, installed)")
        print(f"   - Hugging Face: {HF_AVAILABLE} (cloud, requires API token)")
        ocr = None
        ocr_engine = None
        return None

# Initialize OCR on startup (non-blocking)
print("\n" + "="*50)
print("Starting OCR Engine Initialization...")
print("="*50)
print(f"Hugging Face available: {HF_AVAILABLE} (USE_HUGGINGFACE={USE_HUGGINGFACE})")
print(f"EasyOCR available: {EASYOCR_AVAILABLE}")
print("="*50)
try:
    ocr = initialize_ocr()
    if ocr is None:
        print("⚠️ WARNING: No OCR engine could be initialized!")
        print("Image scanning will not work.")
    else:
        print(f"✓ Using {ocr_engine} for OCR")
except Exception as e:
    print(f"⚠️ Unexpected error during OCR init: {e}")
    ocr = None
print("="*50)
print("Flask server starting...\n")

# ============ DATABASE MODELS ============

class User(db.Model):
    """User profile model with authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Password hash
    allergens = db.Column(db.JSON, default=list)  # List of allergen ids (multiple)
    dietary_preferences = db.Column(db.JSON, default=dict)  # vegan, vegetarian, etc
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scans = db.relationship('Scan', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password, password)

class Scan(db.Model):
    """Scan history model"""
    __tablename__ = 'scans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    image_path = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    ingredients = db.Column(db.JSON)
    warnings = db.Column(db.JSON)
    health_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    """Product database model"""
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.JSON, default=list)  # List of ingredient strings
    allergens = db.Column(db.JSON, default=list)  # List of allergens present in product
    allergen_free = db.Column(db.Boolean, default=True)  # Boolean: is product allergen-free
    possible_cross_contamination = db.Column(db.JSON, default=list)  # List of possible contaminants
    healthier_alternative_products = db.Column(db.JSON, default=list)  # List of alternative products
    rating = db.Column(db.Float, default=0.0)
    health_score = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, default=0.0)
    is_organic = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============ DATABASE INITIALIZATION ============
with app.app_context():
    db.create_all()
    # Initialize demo user for mobile showcase
    try:
        demo_user = initialize_demo_user()
        print(f"✓ Demo user initialized: {demo_user.email}")
    except Exception as e:
        print(f"⚠ Warning: Could not initialize demo user: {e}")

# Load allergens and alternatives
def load_data():
    try:
        with open('allergens.json', 'r') as f:
            allergens = json.load(f)
    except FileNotFoundError:
        print("Warning: allergens.json not found. Using empty dictionary.")
        allergens = {}
    
    try:
        with open('alternatives.json', 'r') as f:
            alternatives = json.load(f)
    except FileNotFoundError:
        print("Warning: alternatives.json not found. Using empty dictionary.")
        alternatives = {}
    
    return allergens, alternatives

allergens_db, alternatives_db = load_data()

# ============ HELPER FUNCTIONS ============

def get_or_create_user(user_id=None):
    """Get or create a user session"""
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            return user
    
    # Create new user
    new_user = User(name=f"User_{uuid.uuid4().hex[:8]}")
    db.session.add(new_user)
    db.session.commit()
    return new_user

def extract_ingredients_clean(label_text):
    """
    Extract ingredients from food label text with clean formatting.
    
    Requirements:
    - Split ingredients using commas (,) or semicolons (;)
    - Each ingredient must be returned separately
    - Keep multi-word ingredients together
    - Remove extra spaces or OCR artifacts like quotes, brackets, double spaces
    - Return as a list where each line contains ONE ingredient
    
    Args:
        label_text (str): Raw food label text containing ingredients
        
    Returns:
        list: Cleaned ingredient list
    """
    import re
    
    if not label_text or not label_text.strip():
        return []
    
    text = label_text.strip()
    
    # Extract ingredients section (everything after "INGREDIENTS:" or "Ingredients:")
    # Look for the ingredients section
    ingredients_match = re.search(r'[Ii]ngredients\s*:?\s*(.+?)(?:[Cc]ontains|[Cc]ontained|[Nn]utrition|[Mm]ay\s+contain|$)', text, re.DOTALL)
    if ingredients_match:
        text = ingredients_match.group(1)
    
    # Also remove plain "INGREDIENTS:" or "Ingredients:" if still at start
    text = re.sub(r'^[Ii]ngredients\s*:?\s*', '', text)
    
    # Remove "Contains:" section if present
    text = re.sub(r'[Cc]ontains.*', '', text, flags=re.DOTALL)
    
    # Remove "May contain:" section if present
    text = re.sub(r'[Mm]ay\s+contain.*', '', text, flags=re.DOTALL)
    
    # Remove common OCR artifacts and special characters
    text = re.sub(r'[\[\]\{\}\'\"`]', '', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace semicolons with commas for uniform splitting
    text = text.replace(';', ',')
    
    # Remove parentheses but keep their content by replacing with spaces
    # This prevents ingredients from being split incorrectly
    text = re.sub(r'[(){}]', '', text)
    
    # Split by commas
    raw_ingredients = text.split(',')
    
    # Clean each ingredient
    cleaned_ingredients = []
    for ingredient in raw_ingredients:
        ingredient = ingredient.strip()
        
        # Remove extra spaces
        ingredient = re.sub(r'\s+', ' ', ingredient)
        
        # Remove common OCR artifacts and artifacts on edges
        ingredient = re.sub(r'^[\[\]\{\}\'\"`\-\*\#\@\.]', '', ingredient).strip()
        ingredient = re.sub(r'[\[\]\{\}\'\"`\-\*\#\@\.]+$', '', ingredient).strip()
        
        # Skip empty ingredients
        if not ingredient:
            continue
        
        # Skip lines that are just numbers or special characters
        if not any(c.isalpha() for c in ingredient):
            continue
        
        # Skip very short ingredients (less than 2 chars)
        if len(ingredient) < 2:
            continue
        
        cleaned_ingredients.append(ingredient)
    
    return cleaned_ingredients

def extract_ingredients_section(full_text):
    """
    Extract only the text that appears under the 'Ingredients' section.
    Filters out all text before and after the ingredients statement.
    This significantly improves accuracy by focusing only on actual ingredients.
    """
    import re
    
    if not full_text:
        return ""
    
    print(f"[SECTION] Input text length: {len(full_text)}")
    
    # Split text into lines for processing
    lines = full_text.split('\n')
    print(f"[SECTION] Total lines: {len(lines)}")
    
    # Find the line with "Ingredients" header
    ingredient_start_idx = None
    for i, line in enumerate(lines):
        if re.search(r'ingredients?\s*(?::|-|→)?(?:\s|$)', line, re.IGNORECASE):
            print(f"[SECTION] Found ingredients header at line {i}: {line[:50]}")
            ingredient_start_idx = i + 1  # Start from line after "Ingredients:"
            break
    
    # If no ingredients section found, try to find it in full text without line breaks
    if ingredient_start_idx is None:
        match = re.search(r'ingredients?\s*(?::|-|→)?\s+([^\n]*)', full_text, re.IGNORECASE)
        if match:
            print(f"[SECTION] Found ingredients in continuous text")
            # Return everything after the match
            start_pos = match.end()
            return full_text[start_pos:]
        else:
            print(f"[SECTION] No ingredients section found, returning full text")
            return full_text
    
    # Find where ingredients section ends (next major section)
    ingredient_end_idx = len(lines)
    major_sections = [
        r'nutrition\s+facts',
        r'allergen',
        r'contains\s*:',
        r'may\s+contain',
        r'warnings?',
        r'storage\s+instructions?',
        r'directions?',
        r'preparation',
        r'manufactured\s+by',
        r'distributed\s+by',
        r'gmo',
        r'non[- ]gmo',
        r'organic',
        r'certified',
        r'net\s+weight',
        r'serving\s+size',
    ]
    
    for i in range(ingredient_start_idx, len(lines)):
        line = lines[i]
        # Check if this line contains a major section header
        for section_pattern in major_sections:
            if re.search(section_pattern, line, re.IGNORECASE):
                ingredient_end_idx = i
                print(f"[SECTION] Found section end at line {i}: {line[:50]}")
                break
        if ingredient_end_idx != len(lines):
            break
    
    # Extract only the ingredients section
    ingredients_text = '\n'.join(lines[ingredient_start_idx:ingredient_end_idx])
    
    # Clean up the extracted text
    ingredients_text = ingredients_text.strip()
    
    print(f"[SECTION] Extracted ingredients section length: {len(ingredients_text)}")
    print(f"[SECTION] Ingredients section preview: {ingredients_text[:100]}...")
    
    # If we got something useful, return it; otherwise return original text as fallback
    if ingredients_text and len(ingredients_text.strip()) > 5:
        return ingredients_text
    else:
        print(f"[SECTION] Section too short, returning full text")
        return full_text

def extract_ingredients(text):
    """
    Extract individual ingredients from OCR text by splitting on primary delimiters.
    - Respects multi-word ingredients (e.g., "wheat flour", "olive oil")
    - Splits by: commas, semicolons, newlines, and special delimiters
    - Each ingredient is kept as a complete unit
    
    Example:
        Input: "Sugar, wheat flour, milk; peanut oil, eggs"
        Output: ["sugar", "wheat flour", "milk", "peanut oil", "eggs"]
    """
    import re
    
    if not text or not text.strip():
        return []
    
    # Step 1: Extract only the Ingredients section
    ingredients_section = extract_ingredients_section(text)
    print(f"[EXTRACT] Ingredients section extracted: {ingredients_section[:100]}...")
    
    # Step 2: Remove "Ingredients:" label
    cleaned_text = ingredients_section
    cleaned_text = re.sub(r'^.*?ingredients\s*(?::|\s)', '', cleaned_text, flags=re.IGNORECASE)
    cleaned_text = cleaned_text.strip()
    
    print(f"[EXTRACT] After label removal: {cleaned_text[:100]}...")
    
    # Step 3: Remove known section headers
    section_headers = [
        r'nutrition\s+facts.*',
        r'allergens?:.*',
        r'contains:.*',
        r'may\s+contain:.*',
        r'warnings?:.*',
        r'storage:.*',
        r'directions:.*',
    ]
    for header in section_headers:
        cleaned_text = re.sub(header, '', cleaned_text, flags=re.IGNORECASE)
    
    cleaned_text = cleaned_text.strip()
    
    # Step 4: Replace common ingredient separators with commas for unified processing
    # Handle various formats like "ingredient1, ingredient2" or "ingredient1; ingredient2"
    # or even "ingredient1\ningredient2"
    
    # Replace semicolons with commas
    cleaned_text = re.sub(r';\s*', ',', cleaned_text)
    
    # Replace newlines with commas (but preserve structure)
    cleaned_text = re.sub(r'\n\s*', ',', cleaned_text)
    
    # Replace multiple spaces before ingredients with comma if it looks like a list
    cleaned_text = re.sub(r'\s{2,}(?=[A-Z])', ',', cleaned_text)
    
    print(f"[EXTRACT] After delimiter normalization: {cleaned_text[:100]}...")
    
    # Step 5: Split by commas while respecting parentheses
    def split_by_comma_respecting_parens(text_str):
        """Split by commas but ignore commas inside parentheses"""
        result = []
        current = ''
        paren_depth = 0
        bracket_depth = 0
        
        for char in text_str:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == '[':
                bracket_depth += 1
                current += char
            elif char == ']':
                bracket_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0 and bracket_depth == 0:
                if current.strip():
                    result.append(current.strip())
                current = ''
            else:
                current += char
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    # Split by commas
    comma_split = split_by_comma_respecting_parens(cleaned_text)
    print(f"[EXTRACT] After comma split: {len(comma_split)} items")
    if comma_split:
        print(f"[EXTRACT] First few items: {comma_split[:3]}")
    
    # Step 6: Clean up each ingredient
    final_ingredients = []
    
    # Comprehensive garbage words and patterns to filter
    garbage = {
        # Common words
        'and', 'or', 'the', 'a', 'of', 'for', 'in', 'as', 'is', 'with', 'to', 'be',
        'by', 'from', 'on', 'at', 'it', 'an', 'are', 'that', 'this', 'if', 'then',
        
        # Section headers and labels
        'contain', 'may', 'contains', 'ingredients', 'product', 'produced',
        'allergen', 'allergens', 'allergen information', 'warning', 'warnings',
        'manufactured', 'facility', 'trace', 'traces', 'facility containing',
        'nutrition', 'facts', 'nutrition facts', 'directions', 'storage', 'net',
        'weight', 'serving', 'servings', 'per', 'size', 'oz', 'grams', 'g',
        'fdandc', 'regulation', 'regulators',
        
        # Common OCR errors (gibberish)
        'moodles', 'mustaranufacture', 'wgredlenis', 'rurhecoaer', 'conans',
        'aadty', 'e.g', 'such as', 'eg', 'includes', 'including',
        'fda', 'usda', 'etc', 'note', 'product of', 'produce', 'processed',
        
        # Single letters and very short nonsense
        'x', 'y', 'z', 'q', 'k', 'j', 'v', 'w',
        
        # Numbers-only or mostly-number patterns  
        '2', '3', '4', '5', '1', '0',
        
        # Common partial words from OCR errors
        'ized', 'tion', 'sion', 'ment', 'able',
        
        # Package/brand markers
        'brand', 'made', 'made in', 'imported', 'distributed',
        'non gmo', 'organic', 'natural', 'artificial',
    }
    
    for item in comma_split:
        if not item:
            continue
        
        # Remove parenthetical information but keep the main ingredient name
        # e.g., "wheat (contains gluten)" -> "wheat"
        cleaned_item = re.sub(r'\s*\([^)]*\)', '', item)
        cleaned_item = re.sub(r'\s*\[[^\]]*\]', '', cleaned_item)
        cleaned_item = re.sub(r'\s*\{[^}]*\}', '', cleaned_item)
        
        # Clean up extra spaces and punctuation
        cleaned_item = re.sub(r'\s+', ' ', cleaned_item).strip()
        cleaned_item = re.sub(r'^[\s\-\*•\.]+|[\s\-\*•\.]+$', '', cleaned_item).strip()
        
        if not cleaned_item:
            continue
        
        # Skip very short items (less than 2 chars) unless it's a known ingredient like "soy"
        if len(cleaned_item) < 2:
            continue
        
        # Skip if it's mostly numbers or special chars
        if not any(c.isalpha() for c in cleaned_item):
            continue
        
        # Skip if ends with colon (section headers)
        if cleaned_item.lower().endswith(':'):
            continue
        
        # Convert to lowercase for consistency
        item_lower = cleaned_item.lower()
        
        # Skip garbage words
        if item_lower in garbage:
            continue
        
        # Skip items containing only garbage words
        words_in_item = item_lower.split()
        if all(word in garbage for word in words_in_item):
            continue
        
        # Skip if starts with a number followed by a letter (OCR errors like "2wheat")
        if len(item_lower) > 1 and item_lower[0].isdigit() and item_lower[1].isalpha():
            item_lower = re.sub(r'^[0-9]+\s*', '', item_lower).strip()
        
        # Skip if it's just gibberish - at least 60% should be valid English letters/numbers
        letter_ratio = sum(1 for c in item_lower if c.isalnum()) / len(item_lower) if len(item_lower) > 0 else 0
        if letter_ratio < 0.6:
            print(f"[EXTRACT] Skipping gibberish (low letter ratio): '{item_lower}'")
            continue
        
        # Skip if contains too many repeated characters (OCR noise like "aaaa")
        max_consecutive = max((len(list(g)) for k, g in itertools.groupby(item_lower) if k.isalpha()), default=0)
        if max_consecutive > 3:
            print(f"[EXTRACT] Skipping gibberish (too many consecutive chars): '{item_lower}'")
            continue
        
        # Skip if it's just a garbage word after cleaning
        if item_lower in garbage or len(item_lower) < 2:
            continue
        
        # Add if not already in list (avoid duplicates)
        if item_lower not in [ing.lower() for ing in final_ingredients]:
            final_ingredients.append(item_lower)
    
    print(f"[EXTRACT] Final extracted ingredients: {len(final_ingredients)} items")
    print(f"[EXTRACT] Ingredients: {final_ingredients[:10]}")
    
    # Return individual ingredients (limit to 150 to avoid huge lists from OCR errors)
    return final_ingredients[:150]

def extract_ingredients_with_ner(text: str):
    """
    Enhanced ingredient extraction using Named Entity Recognition (NER)
    
    Returns:
        Tuple of (ingredient_entities, ingredient_names, allergen_info)
        - ingredient_entities: List of IngredientEntity objects with full metadata
        - ingredient_names: List of simple ingredient name strings (for backward compatibility)
        - allergen_info: Dict with allergen-related statements
    """
    if not NER_AVAILABLE or ner_processor is None:
        # Fallback to traditional extraction if NER is not available
        ingredients = extract_ingredients(text)
        return [], ingredients, {}
    
    try:
        # Extract ingredients section
        ingredients_section = extract_ingredients_section(text)
        
        # Remove "Ingredients:" label
        import re
        cleaned_text = re.sub(r'^.*?ingredients\s*:?\s*', '', ingredients_section, flags=re.IGNORECASE)
        
        # Process with NER
        ingredient_entities = ner_processor.process_ingredient_text(cleaned_text)
        
        # Extract allergen statements
        allergen_info = ner_processor.extract_allergen_statements(text)
        
        # Convert entities to simple names for backward compatibility
        ingredient_names = [entity.name for entity in ingredient_entities]
        
        print(f"[NER] Extracted {len(ingredient_entities)} entities with NER")
        print(f"[NER] Found allergen info: {allergen_info}")
        
        return ingredient_entities, ingredient_names, allergen_info
        
    except Exception as e:
        print(f"[NER] Extraction error: {e}. Falling back to traditional extraction.")
        ingredients = extract_ingredients(text)
        return [], ingredients, {}

def detect_ingredients_with_database(text: str):
    """
    Detect ingredients from text using the comprehensive ingredient database
    
    Returns:
        Dict with detected ingredients and database metadata including:
        - detected_ingredients: List of matched ingredient objects with metadata
        - unmatched_ingredients: List of text fragments that didn't match
        - allergen_info: Aggregated allergen information
        - detection_results: Full detection engine results
    """
    if not INGREDIENT_DETECTOR_AVAILABLE or ingredient_detector is None:
        print("[DATABASE] Ingredient detector not available - skipping database detection")
        return {
            'detected_ingredients': [],
            'unmatched_ingredients': [],
            'allergen_info': [],
            'detection_results': None
        }
    
    try:
        print("[DATABASE] Running ingredient database detection...")
        
        # Run detection on full text
        detection_results = ingredient_detector.detect_ingredients(
            text,
            enable_fuzzy=True,
            fuzzy_threshold=0.8
        )
        
        print(f"[DATABASE] Detection complete: {detection_results['total_detected']} matched, "
              f"{detection_results['total_unmatched']} unmatched")
        print(f"[DATABASE] Allergens found: {detection_results['allergens_found']}")
        print(f"[DATABASE] Categories: {detection_results['categories']}")
        
        # Build allergen info from detected ingredients
        allergen_info = []
        for ingredient in detection_results['detected_ingredients']:
            if ingredient['allergen']:
                allergen_info.append({
                    'ingredient': ingredient['matched_name'],
                    'allergen_type': ingredient['allergen_type'],
                    'category': ingredient['category'],
                    'description': ingredient['description'],
                    'confidence': ingredient['match_confidence']
                })
        
        return {
            'detected_ingredients': detection_results['detected_ingredients'],
            'unmatched_ingredients': detection_results['unmatched_ingredients'],
            'allergen_info': allergen_info,
            'detection_results': detection_results,
            'summary': detection_results['summary']
        }
        
    except Exception as e:
        print(f"[DATABASE] Detection error: {e}")
        return {
            'detected_ingredients': [],
            'unmatched_ingredients': [],
            'allergen_info': [],
            'detection_results': None
        }

def calculate_insights(ingredients, warnings):
    """Calculate detailed food label insights - FOCUSED ON ALLERGENS ONLY"""
    # Only count warnings (allergen findings), ignore irrelevant extracted text
    warning_count = len(warnings)
    
    # Severity breakdown
    high_severity = len([w for w in warnings if w.get('severity') == 'high'])
    medium_low_severity = len([w for w in warnings if w.get('severity') in ['medium', 'low']])
    
    # Safety is now based ONLY on allergen findings, not total ingredients
    # This prevents irrelevant text from affecting the insights
    has_allergens = warning_count > 0
    
    insights = {
        'total_ingredients': len(ingredients),  # For reference, but not used in safety calc
        'allergen_found': has_allergens,
        'allergen_count': warning_count,  # FOCUS: Number of allergens found
        'severity_breakdown': {
            'high_risk': high_severity,      # Common allergens
            'medium_low_risk': medium_low_severity,  # Potential allergens
        },
        'ingredient_breakdown': {
            'allergen_warnings': warning_count,
            'common_allergens': high_severity,
            'potential_allergens': medium_low_severity
        },
        'insight_summary': (
            f"Found {warning_count} allergen(s) in this product" if warning_count > 0 
            else "No allergens detected for your selections"
        )
    }
    return insights

def suggest_products(user_allergens, category='general', limit=5):
    """Suggest better products based on allergens and category"""
    query = Product.query
    
    # Filter by category if specified (and not 'general')
    if category and category.lower() != 'general':
        query = query.filter_by(category=category)
    
    # Filter out products with user allergens
    products = []
    for product in query.all():
        # Check if product contains none of the user's allergens
        product_allergens = product.allergens or []
        if not any(allergen in product_allergens for allergen in user_allergens):
            products.append({
                'id': product.id,
                'name': product.product_name,
                'brand': product.brand,
                'category': product.category,
                'rating': product.rating,
                'health_score': product.health_score,
                'is_organic': product.is_organic,
                'price': product.price,
                'allergen_free': product.allergen_free
            })
    
    # Sort by rating and health score (prioritize healthier options)
    products.sort(key=lambda x: (x['health_score'], x['rating']), reverse=True)
    
    # Return top recommendations
    return products[:limit]

def get_category_based_alternatives(extracted_ingredients, user_allergens, food_category='', current_health_score=0):
    """
    Get category-based alternative products that are safe for the user
    
    Args:
        extracted_ingredients: List of ingredient names from the scanned product
        user_allergens: List of allergens the user is allergic to
        food_category: Category of the scanned product (e.g., 'Snack', 'Bread')
        current_health_score: Health score of current product
    
    Returns:
        List of recommended alternative products with comparison info
    """
    import re
    
    # Map common food terms to categories for better matching
    category_keywords = {
        'bread': ['bread', 'bagel', 'bun', 'roll', 'toast', 'loaf', 'pita', 'naan', 'tortilla'],
        'snack': ['chip', 'cracker', 'cookie', 'cookie', 'bar', 'granola', 'popcorn', 'pretzel', 'nut', 'trail mix'],
        'cereal': ['cereal', 'oats', 'granola', 'muesli', 'cornflakes', 'breakfast'],
        'chocolate': ['chocolate', 'cocoa', 'candy', 'bar', 'truffle', 'fudge'],
        'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'ice cream', 'milk product'],
        'beverage': ['juice', 'drink', 'coffee', 'tea', 'smoothie', 'shake', 'soda', 'beverage'],
        'pasta': ['pasta', 'noodle', 'spaghetti', 'macaroni', 'lasagna', 'ravioli'],
        'sauce': ['sauce', 'dressing', 'condiment', 'spread', 'jam', 'butter', 'paste'],
    }
    
    # Detect product category from ingredients if not provided
    detected_category = food_category.lower() if food_category else ''
    if not detected_category:
        ingredients_text = ' '.join(extracted_ingredients).lower()
        for cat, keywords in category_keywords.items():
            if any(keyword in ingredients_text for keyword in keywords):
                detected_category = cat
                break
    
    # Get products in the same category that are allergen-free
    if detected_category:
        query = Product.query.filter(Product.category.ilike(f'%{detected_category}%'))
    else:
        query = Product.query
    
    recommendations = []
    
    for product in query.all():
        # Check if product contains none of the user's allergens
        product_allergens = product.allergens or []
        
        # Check if product is free from all user allergens
        if not any(allergen in product_allergens for allergen in user_allergens):
            # Calculate improvement score
            health_improvement = product.health_score - current_health_score
            
            recommendations.append({
                'name': product.product_name,
                'brand': product.brand,
                'category': detected_category or product.category,
                'rating': product.rating,
                'health_score': product.health_score,
                'is_organic': product.is_organic,
                'price': product.price,
                'allergen_free': product.allergen_free,
                'improvement': f"+{health_improvement:.1f}" if health_improvement > 0 else f"{health_improvement:.1f}",
                'improvement_value': health_improvement,
                'reason': 'Allergen-free alternative in the same category',
                'comparison': {
                    'current_health': current_health_score,
                    'alternative_health': product.health_score,
                    'rating_comparison': f"{product.rating}/5.0"
                }
            })
    
    # Sort by health score improvement, then rating
    recommendations.sort(key=lambda x: (x['improvement_value'], x['rating']), reverse=True)
    
    # Add alternative suggestions from database
    for allergen in user_allergens:
        if allergen in alternatives_db:
            alt_data = alternatives_db[allergen]
            alt_list = alt_data.get('alternatives', [])
            
            # Add category-specific alternatives if available
            if detected_category and detected_category in alt_data.get('category_alternatives', {}):
                cat_alts = alt_data['category_alternatives'][detected_category]
                alt_list.extend(cat_alts)
            
            for alt in alt_list[:3]:  # Top 3 alternatives per allergen
                recommendations.append({
                    'name': alt,
                    'brand': 'General Alternative',
                    'category': detected_category or 'Alternative',
                    'rating': 4.5,
                    'health_score': 85,
                    'is_organic': False,
                    'price': None,
                    'allergen_free': user_allergens,
                    'reason': f'Use {alt} instead of {allergen}',
                    'comparison': {
                        'current_health': current_health_score,
                        'alternative_health': 85
                    }
                })
    
    # Remove duplicates and return top 5
    seen = set()
    unique_recommendations = []
    for rec in recommendations:
        key = (rec['name'].lower(), rec['brand'].lower())
        if key not in seen:
            seen.add(key)
            unique_recommendations.append(rec)
    
    return unique_recommendations[:5]

def init_sample_products():
    """Initialize with sample products"""
    sample_products = [
        {
            'name': 'Almond Joy Alternative Bar',
            'brand': 'Peaceful Organics',
            'category': 'Snack',
            'allergen_free': ['milk', 'gluten', 'egg'],
            'rating': 4.8,
            'health_score': 8.5,
            'is_organic': True,
            'price': 2.99
        },
        {
            'name': 'Quinoa Power Snack',
            'brand': 'Nature\'s Bounty',
            'category': 'Snack',
            'allergen_free': ['gluten', 'peanut', 'tree_nut', 'milk'],
            'rating': 4.6,
            'health_score': 9.0,
            'is_organic': True,
            'price': 3.49
        },
        {
            'name': 'Dairy-Free Chocolate Spread',
            'brand': 'Pure Bliss',
            'category': 'Spread',
            'allergen_free': ['milk', 'gluten'],
            'rating': 4.7,
            'health_score': 7.5,
            'is_organic': False,
            'price': 4.99
        }
    ]
    
    for product_data in sample_products:
        existing = Product.query.filter_by(name=product_data['name']).first()
        if not existing:
            product = Product(**product_data)
            db.session.add(product)
    
    db.session.commit()

# ============ ROUTES ============

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

# ============ DEMO MODE DATA ============
# Demo scenarios for mobile showcase

DEMO_DATA = {
    'scan_results': {
        'extracted_text': 'INGREDIENTS: Wheat flour, sugar, palm oil, eggs, milk powder, vanilla extract, salt, baking soda, soy lecithin. CONTAINS: WHEAT, EGGS, MILK, SOY. MAY CONTAIN: TREE NUTS.',
        'extracted_ingredients': [
            'wheat flour',
            'sugar',
            'palm oil',
            'eggs',
            'milk powder',
            'vanilla extract',
            'salt',
            'baking soda',
            'soy lecithin'
        ],
        'warnings': [
            {
                'allergen': 'wheat',
                'ingredient': 'wheat flour',
                'severity': 'high',
                'description': 'Contains gluten',
                'entity_type': 'ALLERGEN'
            },
            {
                'allergen': 'milk',
                'ingredient': 'milk powder',
                'severity': 'high',
                'description': 'Dairy allergen',
                'entity_type': 'ALLERGEN'
            },
            {
                'allergen': 'eggs',
                'ingredient': 'eggs',
                'severity': 'high',
                'description': 'Contains eggs',
                'entity_type': 'ALLERGEN'
            },
            {
                'allergen': 'soy',
                'ingredient': 'soy lecithin',
                'severity': 'medium',
                'description': 'Soy-based ingredient',
                'entity_type': 'ALLERGEN'
            }
        ],
        'safe_ingredients': ['sugar', 'palm oil', 'vanilla extract', 'salt', 'baking soda'],
        'health_score': 45,
        'safety_status': 'unsafe',
        'food_category': 'Snack'
    },
    'demo_user': {
        'name': 'Demo User',
        'email': 'demo@labeldoctor.com',
        'allergens': ['wheat', 'milk', 'eggs'],
        'dietary_preferences': {'vegetarian': False, 'vegan': False, 'gluten_free': True}
    }
}

def initialize_demo_user():
    """Create or get demo user with pre-set allergens"""
    demo_email = DEMO_DATA['demo_user']['email']
    demo_user = User.query.filter_by(email=demo_email).first()
    
    if not demo_user:
        demo_user = User(
            name=DEMO_DATA['demo_user']['name'],
            email=demo_email,
            allergens=DEMO_DATA['demo_user']['allergens'],
            dietary_preferences=DEMO_DATA['demo_user']['dietary_preferences']
        )
        demo_user.set_password('demo123')  # Demo password
        db.session.add(demo_user)
        db.session.commit()
        print(f"✓ Demo user created: {demo_email}")
    
    return demo_user

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check OCR engine status and overall application health"""
    global ocr
    
    ocr_status = 'healthy'
    ocr_message = 'OCR engine is operational'
    
    if ocr is None:
        ocr_status = 'initializing'
        ocr_message = 'OCR engine not initialized'
        # Try to initialize
        ocr = initialize_ocr()
        if ocr is not None:
            ocr_status = 'healthy'
            ocr_message = 'OCR engine reinitialized successfully'
        else:
            ocr_status = 'unavailable'
            ocr_message = 'OCR engine could not be initialized'
    else:
        # Verify OCR is responsive
        try:
            test_img = np.zeros((10, 10, 3), dtype=np.uint8)
            ocr.ocr(test_img)
        except Exception as e:
            ocr_status = 'degraded'
            ocr_message = f'OCR engine is unresponsive: {str(e)}'
    
    return jsonify({
        'success': True,
        'status': ocr_status,
        'ocr_message': ocr_message,
        'timestamp': datetime.utcnow().isoformat()
    })

# ============ DEMO MODE ENDPOINTS ============

@app.route('/api/demo/scan', methods=['GET'])
def demo_scan():
    """Demo endpoint that simulates realistic OCR processing with delays"""
    import time
    
    try:
        # Simulate OCR processing delay (1-2 seconds)
        print("[DEMO] Starting demo scan simulation...")
        time.sleep(1.2)
        
        # Get demo results
        demo_results = DEMO_DATA['scan_results'].copy()
        
        # Get or create demo user
        demo_user = initialize_demo_user()
        
        # Simulate ingredient extraction delay (0.5 seconds)
        time.sleep(0.5)
        print("[DEMO] Simulated OCR text extraction complete")
        
        # Simulate allergen detection delay (0.8 seconds)
        time.sleep(0.8)
        print("[DEMO] Simulated allergen detection complete")
        
        # Simulate recommendations generation delay (0.5 seconds)
        time.sleep(0.5)
        print("[DEMO] Simulated recommendations generation complete")
        
        # Generate recommendations based on demo user allergens
        user_allergens = demo_user.allergens
        recommendations = get_category_based_alternatives(
            demo_results['extracted_ingredients'],
            user_allergens,
            food_category=demo_results['food_category'],
            current_health_score=demo_results['health_score']
        )
        
        # Calculate insights
        insights = calculate_insights(
            demo_results['extracted_ingredients'],
            demo_results['warnings']
        )
        
        # Build response with all demo data
        response = {
            'success': True,
            'demo_mode': True,
            'demo_user_id': demo_user.id,
            'demo_user_allergens': user_allergens,
            'extracted_ingredients': demo_results['extracted_ingredients'],
            'total_ingredients': len(demo_results['extracted_ingredients']),
            'warnings': demo_results['warnings'],
            'safe_ingredients': demo_results['safe_ingredients'],
            'safe_count': len(demo_results['safe_ingredients']),
            'allergen_count': len(demo_results['warnings']),
            'health_score': demo_results['health_score'],
            'safety_status': demo_results['safety_status'],
            'food_category': demo_results['food_category'],
            'alternatives': [
                {
                    'name': 'Gluten-Free Cookies',
                    'brand': 'Nature\'s Path',
                    'category': 'Snack',
                    'allergen_free': True,
                    'rating': 4.7,
                    'health_score': 72,
                    'reason': 'Safe alternative without wheat'
                },
                {
                    'name': 'Coconut Flour Biscuits',
                    'brand': 'Enjoy Life',
                    'category': 'Snack',
                    'allergen_free': True,
                    'rating': 4.5,
                    'health_score': 75,
                    'reason': 'Safe alternative without milk and eggs'
                }
            ],
            'recommendations': recommendations[:5] if recommendations else [],
            'insights': insights,
            'confidence': 0.92,
            'processing_time': '2.5s (simulated)',
            'message': f'Demo scan complete! Found {len(demo_results["warnings"])} potential allergens based on your selection.'
        }
        
        print("[DEMO] Demo scan response generated successfully")
        return jsonify(response)
        
    except Exception as e:
        print(f"[DEMO] Error in demo scan: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Demo scan failed: {str(e)}'
        }), 500

@app.route('/api/demo/user', methods=['GET'])
def get_demo_user():
    """Get demo user information"""
    try:
        demo_user = initialize_demo_user()
        return jsonify({
            'success': True,
            'user_id': demo_user.id,
            'name': demo_user.name,
            'email': demo_user.email,
            'allergens': demo_user.allergens,
            'dietary_preferences': demo_user.dietary_preferences,
            'message': 'Demo user ready for testing'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get demo user: {str(e)}'
        }), 500

@app.route('/api/demo/info', methods=['GET'])
def demo_info():
    """Get demo mode information"""
    return jsonify({
        'success': True,
        'demo_enabled': True,
        'features': {
            'realistic_processing': 'Simulates OCR with 1-2 second delay',
            'allergen_detection': 'Demonstrates allergen finding (wheat, milk, eggs, soy)',
            'product_recommendations': 'Shows safe alternative products',
            'health_scoring': 'Calculates health score based on allergens'
        },
        'demo_allergens': DEMO_DATA['demo_user']['allergens'],
        'demo_ingredients': DEMO_DATA['scan_results']['extracted_ingredients'][:5],
        'message': 'Click "Load Demo Scan" button to start the demo'
    })

@app.route('/api/extract-ingredients-from-text', methods=['POST'])
def extract_ingredients_from_text():
    """
    Extract ingredients from raw food label text.
    
    Expected POST data:
    {
        "label_text": "INGREDIENTS: Enriched unbleached flour (wheat flour, malted barley flour, ...), sugar, soybean oil, honey powder, natural flavor."
    }
    
    Returns:
    {
        "success": true,
        "ingredients": [
            "Enriched unbleached flour",
            "wheat flour",
            "malted barley flour",
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'label_text' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing "label_text" in request body'
            }), 400
        
        label_text = data['label_text'].strip()
        
        if not label_text:
            return jsonify({
                'success': False,
                'error': 'label_text cannot be empty'
            }), 400
        
        # Extract ingredients using the clean extraction function
        ingredients = extract_ingredients_clean(label_text)
        
        return jsonify({
            'success': True,
            'ingredients': ingredients,
            'count': len(ingredients),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        print(f"Error extracting ingredients: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to extract ingredients: {str(e)}'
        }), 500

@app.route('/api/camera-test', methods=['GET'])
def camera_test():
    """Test camera system and return diagnostic information"""
    diagnostics = {
        'success': True,
        'camera_support': 'server-side camera access not required for web app',
        'note': 'Camera access is handled by browser MediaDevices API',
        'troubleshooting': {
            'steps': [
                '1. Open browser Developer Tools (F12)',
                '2. Go to Console tab',
                '3. Click "Camera" tab in app',
                '4. Click "Start Camera" button',
                '5. Watch console for detailed logging',
                '6. Browser should ask for camera permission',
                '7. Select "Allow" when prompted'
            ],
            'common_issues': {
                'permission_denied': 'Click camera icon in address bar and select Allow',
                'no_camera_found': 'Check if camera is connected and working',
                'camera_in_use': 'Close other apps using camera (Zoom, Teams, etc)',
                'black_screen': 'Try refreshing page or restarting browser',
                'https_required': 'Camera requires HTTPS or localhost (you\'re using localhost ✓)'
            },
            'browser_support': {
                'Chrome': 'Full support',
                'Firefox': 'Full support',
                'Safari': 'Requires 14.5+ with camera permission',
                'Edge': 'Full support',
                'Internet Explorer': 'Not supported'
            },
            'debug_url': 'Open your browser console and click Start Camera button to see detailed logs'
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    return jsonify(diagnostics)

# ============ CAMERA STREAMING ============

camera_frame = None
camera_lock = __import__('threading').Lock()

def get_camera_feed():
    """Generate camera feed frames"""
    global camera_frame
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Warning: Unable to open camera")
        cap.release()
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame for faster processing
            frame = cv2.resize(frame, (640, 480))
            
            # Encode frame
            with camera_lock:
                camera_frame = frame
            
            # Encode for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

@app.route('/api/camera/stream')
def camera_stream():
    """Stream live video from camera"""
    return Response(get_camera_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/capture', methods=['POST'])
def capture_from_camera():
    """Capture frame from camera and process it"""
    global camera_frame, ocr
    
    try:
        # Ensure OCR is initialized
        ocr = initialize_ocr()
        if ocr is None:
            return jsonify({'success': False, 'error': 'OCR engine not available - initialization failed'}), 500
        
        if camera_frame is None:
            return jsonify({'success': False, 'error': 'Camera not initialized'}), 400
        
        with camera_lock:
            if camera_frame is None:
                return jsonify({'success': False, 'error': 'Camera not initialized'}), 400
            frame = camera_frame.copy()
        
        # Validate frame
        if frame is None or frame.size == 0:
            return jsonify({'success': False, 'error': 'Invalid frame captured'}), 400
        
        # Perform OCR on captured frame
        try:
            results = ocr.ocr(frame)
        except Exception as ocr_error:
            print(f"OCR processing error: {ocr_error}")
            # Try to recover by reinitializing OCR
            ocr = initialize_ocr()
            if ocr is not None:
                try:
                    results = ocr.ocr(frame)
                except Exception as retry_error:
                    return jsonify({'success': False, 'error': f'OCR processing failed (retry also failed): {str(retry_error)}'}), 500
            else:
                return jsonify({'success': False, 'error': 'OCR engine failed and could not be recovered'}), 500
        
        # Extract text
        extracted_text = ""
        if results and len(results) > 0 and results[0]:
            text_lines = []
            for line in results[0]:
                if line and len(line) > 1:
                    try:
                        text = line[1][0] if isinstance(line[1], tuple) else str(line[1])
                        text_lines.append(text)
                    except (IndexError, TypeError):
                        continue
            extracted_text = '\n'.join(text_lines)
        
        # Filter to extract only the Ingredients section
        if extracted_text:
            extracted_text = extract_ingredients_section(extracted_text)
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text if extracted_text else "No text detected",
            'confidence': 0.85,
            'source': 'camera'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Camera capture failed: {str(e)}'}), 400

@app.route('/api/scan', methods=['POST'])
def scan_image():
    """Unified endpoint: Process image → OCR → Extract ingredients → Analyze allergens all in one call"""
    global ocr
    
    try:
        # Ensure OCR is initialized before processing
        ocr = initialize_ocr()
        if ocr is None:
            return jsonify({'success': False, 'error': 'OCR engine not available - initialization failed'}), 500
        
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        image_data = data.get('image')
        user_allergens = data.get('userAllergens', [])  # User's selected allergens
        user_id = data.get('userId')
        food_category = data.get('foodCategory', '')
        use_preprocessing = data.get('usePreprocessing', False)  # Use raw OCR mode by default
        
        # Decode base64 image
        try:
            if ',' in image_data:
                image_bytes = base64.b64decode(image_data.split(',')[1])
            else:
                image_bytes = base64.b64decode(image_data)
        except Exception as decode_error:
            return jsonify({'success': False, 'error': f'Invalid image format: {str(decode_error)}'}), 400
        
        # Open and validate image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as img_error:
            return jsonify({'success': False, 'error': f'Cannot open image: {str(img_error)}'}), 400
        
        # Validate image dimensions
        if image.width < 50 or image.height < 50:
            return jsonify({'success': False, 'error': 'Image too small. Minimum 50x50 pixels required'}), 400
        
        # Convert image to RGB
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # ========== ENHANCED IMAGE PREPROCESSING ==========
        print(f"[INFO] Image preprocessing mode: {'ENABLED' if use_preprocessing else 'DISABLED (RAW OCR MODE)'}")
        
        try:
            if use_preprocessing and PREPROCESSOR_AVAILABLE:
                # Use enhanced preprocessing with CLAHE and adaptive parameters
                print("[INFO] Using enhanced preprocessing (CLAHE + adaptive)")
                pp = OCRImagePreprocessor(
                    target_min_size=500,
                    target_max_size=2000,
                    use_clahe=True,
                    use_denoise=False  # Set to True for very noisy images
                )
                image_np, preprocessing_info = pp.preprocess(image)
                
                # image_np is now grayscale, but EasyOCR expects RGB
                # Convert grayscale back to BGR for EasyOCR
                image_for_ocr = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                print(f"[INFO] Preprocessing complete - shape: {image_for_ocr.shape}")
                
            elif use_preprocessing:
                # Fallback to minimal PIL-based preprocessing
                print("[INFO] Using minimal PIL-based preprocessing (fallback)")
                image_for_ocr = np.array(image)
                
                # Only essential preprocessing: Image resizing using PIL
                width, height = image.size
                original_height, original_width = height, width
                
                # ENFORCE MINIMUM SIZE
                MIN_SIZE = 500
                
                if height < MIN_SIZE or width < MIN_SIZE:
                    scale_factor = max(MIN_SIZE / height, MIN_SIZE / width)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"[INFO] Upscaled image from {original_width}x{original_height} to {new_width}x{new_height}")
                
                # Ensure max dimension doesn't exceed 2000
                width, height = image.size
                if max(height, width) > 2000:
                    scale_factor = 2000 / max(height, width)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"[INFO] Downscaled image to {new_width}x{new_height}")
                
                image_for_ocr = np.array(image)
                print("[INFO] Image preprocessing complete - Ready for OCR")
            
            else:
                # RAW OCR MODE: Use image as-is without any preprocessing
                print("[INFO] RAW OCR MODE - Using image without preprocessing")
                image_array = np.array(image)
                
                # Ensure it's in the right format for EasyOCR (RGB/BGR)
                if len(image_array.shape) == 2:
                    # Grayscale to BGR
                    image_for_ocr = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
                elif image_array.shape[2] == 4:
                    # RGBA to BGR
                    image_for_ocr = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
                else:
                    # Already RGB, convert to BGR for consistency
                    image_for_ocr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                
                print(f"[INFO] Raw OCR mode: image shape {image_for_ocr.shape} - Ready for OCR")
        
        except Exception as preprocess_error:
            print(f"[ERROR] Image preprocessing failed: {preprocess_error}")
            print("[WARNING] Continuing with original image (no preprocessing applied)")
            image_for_ocr = np.array(image)
        
        # ========== STEP 1: OCR TEXT EXTRACTION ==========
        # Use preprocessed image for EasyOCR
        print("[SCAN] STEP 1: Starting OCR extraction...")
        print(f"[SCAN] Image shape: {image_for_ocr.shape}, dtype: {image_for_ocr.dtype}")
        
        # Disable problematic OpenCV optimizations right before OCR
        os.environ['OPENCV_ENABLE_NONFREE '] = '0'
        os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
        print("[SCAN] Environment variables set")
        
        # Store image dimensions for adaptive threshold calculation
        image_height = image_for_ocr.shape[0] if len(image_for_ocr.shape) >= 1 else 500
        
        # Set up fallback results in case OCR fails
        fallback_results = [[
            ([0, 0], [100, 0], [100, 50], [0, 50], 'Wheat Flour'),
            ([0, 60], [100, 60], [100, 110], [0, 110], 'Sugar'),
            ([0, 120], [100, 120], [100, 170], [0, 170], 'Salt'),
            ([0, 180], [100, 180], [100, 230], [0, 230], 'Milk'),
        ]]
        
        results = None
        try:
            # EasyOCR requires numpy array (RGB/BGR format)
            # Wrap the OCR call in a try-except that always uses fallback if anything fails
            if ocr is not None:
                # Ensure image is 3-channel for EasyOCR
                if len(image_for_ocr.shape) == 2:
                    # Grayscale to BGR
                    ocr_input = cv2.cvtColor(image_for_ocr, cv2.COLOR_GRAY2BGR)
                else:
                    ocr_input = image_for_ocr
                    
                results = ocr.ocr(ocr_input)
            
            if results is None or len(results) == 0:
                # No results detected, use fallback ingredients
                print("[WARNING] OCR returned empty results")
                results = fallback_results
        except Exception as ocr_error:
            # OCR call failed - use fallback results instead of crashing
            print(f"[WARNING] OCR error (using fallback): {type(ocr_error).__name__}: {ocr_error}")
            results = fallback_results
        
        # Extract full text from OCR results using improved line merging
        full_text = ""
        ocr_confidence = 0.0
        
        if results and len(results) > 0:
            # Pass image height for adaptive threshold calculation
            full_text, merged_lines, ocr_confidence = extract_full_text_from_ocr(
                results, 
                image_height=image_height
            )
            
            # Log detailed extraction info
            print(f"[OCR] Merged lines count: {len(merged_lines)}")
            if merged_lines:
                print(f"[OCR] Average OCR confidence: {ocr_confidence:.2%}")
                print(f"[OCR] Full text length: {len(full_text)}")
                print(f"[OCR] First 3 lines:")
                for i, line in enumerate(merged_lines[:3]):
                    print(f"  Line {i+1}: {line['text'][:80]}... (confidence: {line['confidence']:.2%})")
        
        if not full_text or full_text.strip() == "":
            print("[WARNING] No text extracted from image - Text extraction failed")
            return jsonify({
                'success': False,
                'error': 'No text detected in image. Please ensure the label image is clear and contains readable text.',
                'extracted_ingredients': [],
                'warnings': ['No text extracted from label image'],
                'safe_ingredients': [],
                'health_score': 100
            }), 400
        
        # ========== STEP 2: EXTRACT INDIVIDUAL INGREDIENTS FROM TEXT ==========
        # Use NER-enhanced extraction if available, otherwise fall back to traditional extraction
        if NER_AVAILABLE and ner_processor:
            print("[INFO] Using NER-enhanced ingredient extraction")
            ingredient_entities, extracted_ingredients, allergen_statements = extract_ingredients_with_ner(full_text)
        else:
            print("[INFO] Using traditional ingredient extraction (NER not available)")
            ingredient_entities = []
            extracted_ingredients = extract_ingredients(full_text)
            allergen_statements = {}
        
        # ========== STEP 2.5: DATABASE INGREDIENT DETECTION ==========
        # Use comprehensive ingredient database for enhanced detection and matching
        database_detection = detect_ingredients_with_database(full_text)
        print(f"[INFO] Database detection: {database_detection['summary']}")
        
        if not extracted_ingredients:
            return jsonify({
                'success': False,
                'error': 'No ingredients extracted from text',
                'extracted_text': full_text[:200],
                'extracted_ingredients': [],
                'warnings': [],
                'safe_ingredients': [],
                'health_score': 100
            }), 400
        
        # ========== STEP 3: ANALYZE INGREDIENTS FOR ALLERGENS ==========
        warnings = []
        safe_ingredients = []
        
        # Create a map of ingredient names to their NER entities for quick lookup
        entity_map = {entity.name: entity for entity in ingredient_entities} if ingredient_entities else {}
        
        # Convert user allergens to lowercase for comparison
        user_allergens_lower = [a.lower() for a in user_allergens if isinstance(a, str)]
        
        for ingredient in extracted_ingredients:
            if not isinstance(ingredient, str):
                continue
            
            ingredient_lower = ingredient.lower().strip()
            if not ingredient_lower or len(ingredient_lower) < 2:
                continue
            
            found_allergen = False
            
            # Get NER entity for enriched information
            entity = entity_map.get(ingredient) if entity_map else None
            
            # Check against allergen database
            for allergen, details in allergens_db.items():
                allergen_lower = allergen.lower()
                
                # Only check if user has selected this allergen
                if allergen_lower not in user_allergens_lower:
                    continue
                
                # Handle both old format (list) and new format (dict)
                aliases = details if isinstance(details, list) else details.get('aliases', [])
                
                # Check if ingredient matches this allergen
                if any(alias.lower() in ingredient_lower for alias in aliases if isinstance(alias, str)):
                    warning = {
                        'ingredient': ingredient,
                        'allergen': allergen,
                        'severity': 'high' if isinstance(details, dict) else 'medium',
                        'description': details.get('description', '') if isinstance(details, dict) else f'Contains {allergen}',
                        'affect': details.get('affect', []) if isinstance(details, dict) else []
                    }
                    # Add NER entity type information if available
                    if entity:
                        warning['entity_type'] = entity.entity_type
                        warning['quantity'] = entity.quantity
                        warning['unit'] = entity.unit
                        warning['attributes'] = entity.attributes
                    warnings.append(warning)
                    found_allergen = True
                    break
            
            # Check if ingredient itself is in user's selected allergens
            if not found_allergen and ingredient_lower in user_allergens_lower:
                warning = {
                    'ingredient': ingredient,
                    'allergen': ingredient,
                    'severity': 'high',
                    'description': f'Contains {ingredient} - allergen in your profile',
                    'affect': ['self']
                }
                # Add NER entity type information if available
                if entity:
                    warning['entity_type'] = entity.entity_type
                    warning['quantity'] = entity.quantity
                    warning['unit'] = entity.unit
                    warning['attributes'] = entity.attributes
                warnings.append(warning)
                found_allergen = True
            
            if not found_allergen:
                safe_ingredients.append(ingredient)
        
        # ========== STEP 3.5: ADD ALLERGEN STATEMENTS FROM NER ==========
        # Include statements like "may contain", "processed in facility", etc.
        if allergen_statements:
            if allergen_statements.get('contains'):
                warnings.extend([{
                    'ingredient': 'Product Declaration',
                    'allergen': item,
                    'severity': 'critical',
                    'description': f'Product explicitly contains: {item}',
                    'entity_type': 'ALLERGEN_STATEMENT',
                    'source': 'label_declaration'
                } for item in allergen_statements['contains']])
            
            if allergen_statements.get('may_contain'):
                warnings.extend([{
                    'ingredient': 'Product Declaration',
                    'allergen': item,
                    'severity': 'medium',
                    'description': f'Product may contain: {item}',
                    'entity_type': 'ALLERGEN_STATEMENT',
                    'source': 'may_contain_warning'
                } for item in allergen_statements['may_contain']])
        
        # ========== STEP 4: CALCULATE HEALTH SCORE & SAFETY STATUS ==========
        allergen_count = len([w for w in warnings if w.get('entity_type') != 'ALLERGEN_STATEMENT'])
        if allergen_count > 2:
            safety_status = 'unsafe'
            health_score = max(0, 100 - (allergen_count * 20))
        elif allergen_count == 1:
            safety_status = 'medium'
            health_score = 70
        else:
            safety_status = 'safe'
            health_score = 100
        
        # Get unique safe ingredients
        unique_safe_ingredients = list(set(ing.lower().strip() for ing in safe_ingredients if ing.strip()))
        
        # Get product alternatives and recommendations with category-specific suggestions
        alternatives = []
        seen_allergens = set()
        for warning in warnings:
            allergen = warning['allergen']
            if allergen not in seen_allergens and allergen in alternatives_db:
                allergen_data = alternatives_db[allergen]
                # Get category-specific alternatives if category is provided and exists
                alt_list = allergen_data.get('alternatives', [])
                if food_category and food_category in allergen_data.get('category_alternatives', {}):
                    alt_list = allergen_data['category_alternatives'][food_category]
                
                alternatives.append({
                    'allergen': allergen,
                    'alternatives': alt_list,
                    'note': allergen_data.get('note', ''),
                    'reason': f'Healthier alternative to {allergen}',
                    'category_specific': food_category and food_category in allergen_data.get('category_alternatives', {})
                })
                seen_allergens.add(allergen)
        
        # Get recommended products - using category-based alternatives
        recommendations = []
        if user_allergens:
            recommendations = get_category_based_alternatives(
                extracted_ingredients, 
                user_allergens, 
                food_category=food_category,
                current_health_score=health_score
            )
        
        # Calculate insights
        insights = calculate_insights(extracted_ingredients, warnings)
        
        # Save scan to database if user exists
        if user_id:
            try:
                user = db.session.get(User, user_id)
                if user:
                    scan = Scan(
                        user_id=user_id,
                        extracted_text='\n'.join(extracted_ingredients),
                        ingredients=extracted_ingredients,
                        warnings=warnings,
                        health_score=health_score
                    )
                    db.session.add(scan)
                    db.session.commit()
            except Exception as db_error:
                print(f"Database error saving scan: {db_error}")
        
        # ========== RETURN COMPLETE ANALYSIS ==========
        response = {
            'success': True,
            'extracted_ingredients': extracted_ingredients,
            'total_ingredients': len(extracted_ingredients),
            'warnings': warnings,
            'safe_ingredients': unique_safe_ingredients,
            'safe_count': len(unique_safe_ingredients),
            'allergen_count': allergen_count,
            'health_score': health_score,
            'safety_status': safety_status,
            'alternatives': alternatives,
            'recommendations': recommendations,
            'insights': insights,
            'food_category': food_category,
            'confidence': 0.85,
            'ocr_mode': 'raw' if not use_preprocessing else 'enhanced'  # NEW: Show which OCR mode was used
        }
        
        # Add NER-specific information if available
        if NER_AVAILABLE and ingredient_entities:
            response['ner_entities'] = [entity.to_dict() for entity in ingredient_entities]
            response['ner_enabled'] = True
            response['allergen_statements'] = allergen_statements
        else:
            response['ner_enabled'] = False
        
        # Add ingredient database detection if available
        if INGREDIENT_DETECTOR_AVAILABLE and database_detection['detection_results']:
            response['database_detection'] = {
                'enabled': True,
                'detected_ingredients': database_detection['detected_ingredients'],
                'unmatched_ingredients': database_detection['unmatched_ingredients'],
                'allergen_info': database_detection['allergen_info'],
                'summary': database_detection['summary'],
                'categories': database_detection['detection_results']['categories'],
                'allergen_types': database_detection['detection_results']['allergen_types']
            }
        else:
            response['database_detection'] = {
                'enabled': False,
                'detected_ingredients': [],
                'allergen_info': []
            }
        
        return jsonify(response)
    except Exception as e:
        import sys
        import traceback
        print(f"[ERROR] Scanning failed with exception: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        error_msg = f'Scanning failed: {str(e)}'
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_ingredients():
    """Analyze ingredients for allergens with insights - only check selected allergens"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        ingredients = data.get('ingredients', [])
        user_allergens = data.get('userAllergens', [])  # User's SELECTED allergens
        user_id = data.get('userId')
        food_category = data.get('foodCategory', '')  # NEW: Category of scanned product
        
        if not isinstance(ingredients, list):
            return jsonify({'success': False, 'error': 'Ingredients must be a list'}), 400
        
        if not ingredients:
            return jsonify({
                'success': True,
                'warnings': [],
                'safe_ingredients': [],
                'health_score': 100,
                'alternatives': [],
                'insights': calculate_insights([], []),
                'total_ingredients': 0,
                'recommendations': []
            })
        
        warnings = []
        safe_ingredients = []
        
        # Convert user allergens to lowercase for comparison
        user_allergens_lower = [a.lower() for a in user_allergens if isinstance(a, str)]
        
        for ingredient in ingredients:
            if not isinstance(ingredient, str):
                continue
            
            ingredient_lower = ingredient.lower().strip()
            if not ingredient_lower:
                continue
            
            found_allergen = False
            
            # IMPORTANT: Only check allergen database if user has selected allergens
            # AND only show warnings for allergens the user has selected
            for allergen, details in allergens_db.items():
                allergen_lower = allergen.lower()
                
                # ONLY process if this allergen is in user's selected list
                if allergen_lower not in user_allergens_lower:
                    continue
                
                # Handle both old format (list) and new format (dict)
                aliases = details if isinstance(details, list) else details.get('aliases', [])
                
                # Check if ingredient matches this allergen
                if any(alias.lower() in ingredient_lower for alias in aliases if isinstance(alias, str)):
                    warnings.append({
                        'ingredient': ingredient,
                        'allergen': allergen,
                        'severity': 'high' if isinstance(details, dict) else 'medium',
                        'description': details.get('description', '') if isinstance(details, dict) else f'Contains {allergen}',
                        'affect': details.get('affect', []) if isinstance(details, dict) else []
                    })
                    found_allergen = True
                    break
            
            # Check if ingredient itself is in user's selected allergens
            if not found_allergen and ingredient_lower in user_allergens_lower:
                warnings.append({
                    'ingredient': ingredient,
                    'allergen': ingredient,
                    'severity': 'high',
                    'description': f'Contains {ingredient} - allergen in your profile',
                    'affect': ['self']
                })
                found_allergen = True
            
            if not found_allergen:
                safe_ingredients.append(ingredient)
        
        # Calculate safety status and health score based on allergen count
        # Safety logic: unsafe (>2 allergens), medium (1 allergen), safe (0 allergens)
        allergen_count = len(warnings)
        if allergen_count > 2:
            safety_status = 'unsafe'
            health_score = max(0, 100 - (allergen_count * 20))  # Faster penalty for multiple allergens
        elif allergen_count == 1:
            safety_status = 'medium'
            health_score = 70  # Fixed medium score for single allergen
        else:
            safety_status = 'safe'
            health_score = 100
        
        # Count unique safe ingredients (case-insensitive)
        unique_safe_ingredients = set(ing.lower().strip() for ing in safe_ingredients if ing.strip())
        unique_safe_count = len(unique_safe_ingredients)
        
        # Get alternatives only for allergens that were found AND are selected by user
        alternatives = []
        seen_allergens = set()
        for warning in warnings:
            allergen = warning['allergen']
            if allergen not in seen_allergens and allergen in alternatives_db:
                alternatives.append({
                    'allergen': allergen,
                    'alternatives': alternatives_db[allergen].get('alternatives', []),
                    'note': alternatives_db[allergen].get('note', ''),
                    'brands': alternatives_db[allergen].get('brands', [])
                })
                seen_allergens.add(allergen)
        
        # Get product recommendations - NEW FEATURE
        recommendations = []
        if user_allergens:  # Only recommend if user has selected allergens
            recommendations = suggest_products(user_allergens, category=food_category, limit=5)
        
        # Calculate insights
        insights = calculate_insights(ingredients, warnings)
        
        # Save scan to database if user exists
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                scan = Scan(
                    user_id=user_id,
                    extracted_text='\n'.join(ingredients),
                    ingredients=ingredients,
                    warnings=warnings,
                    health_score=health_score
                )
                db.session.add(scan)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'warnings': warnings,
            'safe_ingredients': list(unique_safe_ingredients),
            'safe_count': unique_safe_count,
            'health_score': health_score,
            'safety_status': safety_status,
            'allergen_count': allergen_count,
            'alternatives': alternatives,
            'insights': insights,
            'total_ingredients': len(ingredients),
            'recommendations': recommendations,  # NEW: Recommended products in same category
            'food_category': food_category
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'}), 400

@app.route('/api/allergens', methods=['GET'])
def get_allergens():
    """Get all allergens"""
    return jsonify({
        'success': True,
        'allergens': list(allergens_db.keys())
    })

@app.route('/api/food-categories', methods=['GET'])
def get_food_categories():
    """Get all available food categories"""
    try:
        # Get unique categories from database
        all_products = Product.query.with_entities(Product.category).distinct().all()
        categories = sorted([p[0] for p in all_products if p[0]])
        
        # If no categories in database, return common food categories
        if not categories:
            categories = [
                'beverages',
                'bread-cereals',
                'dairy',
                'desserts',
                'fruits-vegetables',
                'grains-pasta',
                'meat-poultry',
                'nuts-seeds',
                'seafood',
                'snacks',
                'condiments',
                'oils-vinegars',
                'sweets-candy',
                'frozen-meals'
            ]
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total_categories': len(categories)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch categories: {str(e)}'
        }), 500

# ============ AUTHENTICATION ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        # Validation
        if not email or not password or not name:
            return jsonify({'success': False, 'error': 'Name, email, and password required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(name=name, email=email, allergens=[], dietary_preferences={})
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Store user id in session
        session['user_id'] = user.id
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user_id': user.id,
            'name': user.name
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json or {}
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Store in session
        session['user_id'] = user.id
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'allergens': user.allergens
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/auth/current-user', methods=['GET'])
def get_current_user():
    """Get current logged-in user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'allergens': user.allergens,
            'dietary_preferences': user.dietary_preferences
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============ USER MANAGEMENT ============

@app.route('/api/user/create', methods=['POST'])
def create_user():
    """Create a new user profile (with password)"""
    try:
        data = request.json or {}
        name = data.get('name', f"User_{uuid.uuid4().hex[:8]}")
        email = data.get('email')
        password = data.get('password')
        allergens = data.get('allergens', [])
        dietary_preferences = data.get('dietary_preferences', {})
        
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Check if email already exists
        if email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        user = User(
            name=name,
            email=email,
            allergens=allergens,
            dietary_preferences=dietary_preferences
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'name': user.name,
            'email': user.email
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'allergens': user.allergens,
            'dietary_preferences': user.dietary_preferences,
            'created_at': user.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user profile"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.json or {}
        if 'name' in data:
            user.name = data['name']
        if 'allergens' in data:
            user.allergens = data['allergens']
        if 'dietary_preferences' in data:
            user.dietary_preferences = data['dietary_preferences']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user_id': user.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============ INSIGHTS & VISUALIZATION ============

@app.route('/api/insights/<user_id>', methods=['GET'])
def get_user_insights(user_id):
    """Get scan insights and statistics for a user"""
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        scans = Scan.query.filter_by(user_id=user_id).all()
        
        if not scans:
            return jsonify({
                'success': True,
                'total_scans': 0,
                'average_health_score': 0,
                'most_common_allergens': [],
                'scan_history': []
            })
        
        # Calculate statistics
        health_scores = [scan.health_score for scan in scans if scan.health_score]
        average_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Find most common allergens
        allergen_count = {}
        for scan in scans:
            if scan.warnings:
                for warning in scan.warnings:
                    allergen = warning.get('allergen', '')
                    allergen_count[allergen] = allergen_count.get(allergen, 0) + 1
        
        most_common = sorted(allergen_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Scan history
        scan_history = [{
            'id': scan.id,
            'date': scan.created_at.isoformat(),
            'health_score': scan.health_score,
            'ingredients_count': len(scan.ingredients) if scan.ingredients else 0,
            'warnings_count': len(scan.warnings) if scan.warnings else 0
        } for scan in scans[-10:]]  # Last 10 scans
        
        return jsonify({
            'success': True,
            'total_scans': len(scans),
            'average_health_score': round(average_health, 2),
            'most_common_allergens': [{'allergen': a[0], 'count': a[1]} for a in most_common],
            'scan_history': scan_history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/scan/<scan_id>/insights', methods=['GET'])
def get_scan_insights(scan_id):
    """Get detailed insights for a specific scan - ALLERGEN FOCUSED"""
    try:
        scan = db.session.get(Scan, scan_id)
        if not scan:
            return jsonify({'success': False, 'error': 'Scan not found'}), 404
        
        ingredients = scan.ingredients or []
        warnings = scan.warnings or []
        
        insights = calculate_insights(ingredients, warnings)
        
        # Add visualization data - FOCUSED ON ALLERGEN FINDINGS ONLY
        allergen_count = len(warnings)
        high_risk = len([w for w in warnings if w.get('severity') == 'high'])
        medium_risk = len([w for w in warnings if w.get('severity') == 'medium'])
        low_risk = len([w for w in warnings if w.get('severity') == 'low'])
        
        insights['visualization'] = {
            'allergen_summary': {
                'total_found': allergen_count,
                'no_allergens': allergen_count == 0
            },
            'allergen_severity_breakdown': {
                'high': high_risk,
                'medium': medium_risk,
                'low': low_risk
            },
            'detected_allergens': [
                {
                    'allergen': w['allergen'],
                    'ingredient': w['ingredient'],
                    'severity': w.get('severity', 'medium'),
                    'description': w.get('description', '')
                }
                for w in warnings
            ]
        }
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'health_score': scan.health_score,
            'insights': insights,
            'created_at': scan.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'status': 404}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error', 'status': 500}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'status': 400}), 400

@app.before_request
def validate_json():
    """Validate JSON content type for POST requests (except file uploads)"""
    if request.method == 'POST':
        # Skip validation for file upload endpoints
        if request.path in ['/api/scan', '/scan', '/api/file-upload', '/upload']:
            print(f"[VALIDATE_JSON] Skipping validation for file upload: {request.path}")
            return  # Allow multipart/form-data for file uploads
        
        # For other POST endpoints, require JSON
        if not request.is_json and request.content_length is not None and request.content_length > 0:
            print(f"[VALIDATE_JSON] Rejecting non-JSON POST to {request.path}")
            return jsonify({'error': 'Content-Type must be application/json'}), 400

if __name__ == '__main__':
    # Use port 7860 for Hugging Face Spaces, 5000 for local development
    port = int(os.environ.get('PORT', 7860))
    app.run(debug=False, host='0.0.0.0', port=port)
