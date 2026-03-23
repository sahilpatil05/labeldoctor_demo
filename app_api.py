from flask import Flask, render_template, request, jsonify, Response, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import base64
import cv2
import numpy as np
import os
from PIL import Image
import io
import uuid
from datetime import datetime
from functools import wraps
import ssl
import urllib.request

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

# ========== OCR ENVIRONMENT SETUP ==========
# Set up PaddleOCR environment variables BEFORE importing
cache_dir = os.path.expanduser('~/.paddleocr')
os.environ['PADDLE_CACHE_DIR'] = cache_dir
os.environ['PADDLEOCR_MODEL_PATH'] = cache_dir
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['PADDLE_INFERENCE_MODEL_PATH'] = cache_dir

# Try to import OCR libraries
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'labeldoctor_secret_key_2026'  # Change this to a secure key
CORS(app)

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
# Use absolute path for database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labeldoctor.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path.replace(os.sep, "/")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Global OCR instance management
ocr = None
ocr_engine = None  # Track which engine is being used
ocr_lock = __import__('threading').Lock()

class EasyOCRWrapper:
    """Wrapper to make EasyOCR compatible with PaddleOCR API"""
    def __init__(self, reader):
        self.reader = reader
        self.engine_type = 'easyocr'
    
    def ocr(self, image, cls=False):
        """Process image with EasyOCR and return results in PaddleOCR format"""
        try:
            # EasyOCR expects images in PIL format or numpy array
            if isinstance(image, np.ndarray):
                # If BGR, convert to RGB
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Run OCR
            results = self.reader.readtext(image, detail=1)  # detail=1 for detailed output
            
            # Convert EasyOCR format to PaddleOCR format
            # PaddleOCR format: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]]
            formatted_results = []
            if results:
                formatted_line = []
                for detection in results:
                    bbox = detection[0]  # coordinates
                    text = detection[1]  # text
                    confidence = detection[2]  # confidence
                    formatted_line.append([bbox, (text, confidence)])
                formatted_results.append(formatted_line)
            
            return formatted_results if formatted_results else [[]]
        except Exception as e:
            print(f"EasyOCR processing error: {e}")
            return [[]]

def initialize_ocr():
    """Initialize OCR engine - tries EasyOCR first (default), then PaddleOCR as fallback"""
    global ocr, ocr_engine
    
    with ocr_lock:
        # Check if already initialized
        if ocr is not None:
            try:
                # Verify OCR is still responsive
                test_img = np.zeros((10, 10, 3), dtype=np.uint8)
                ocr.ocr(test_img, cls=False)
                print(f"✓ {ocr_engine} engine is healthy")
                return ocr
            except Exception as e:
                print(f"⚠ OCR engine degraded: {e}. Attempting reinitialization...")
                ocr = None
        
        # Try EasyOCR first (default)
        if EASYOCR_AVAILABLE:
            try:
                print("Initializing EasyOCR (default)...")
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                ocr = EasyOCRWrapper(reader)
                ocr_engine = 'EasyOCR'
                print("✓ EasyOCR initialized successfully (default)")
                return ocr
            except Exception as e:
                print(f"❌ EasyOCR initialization failed: {e}")
        
        # Try PaddleOCR as fallback
        if PADDLE_AVAILABLE:
            try:
                print("Initializing PaddleOCR (fallback)...")
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    # Try with explicit cache directory
                    ocr = PaddleOCR(
                        lang=['en'],
                        use_angle_cls=False,
                        cache_dir=cache_dir,
                        show_log=False
                    )
                ocr_engine = 'PaddleOCR'
                print("✓ PaddleOCR initialized successfully (fallback)")
                return ocr
            except Exception as e:
                print(f"❌ PaddleOCR initialization failed: {e}")
                print("   Models may need to be downloaded. Run: python fix_paddle_ocr.py")
        
        print("❌ No OCR engine available")
        ocr = None
        ocr_engine = None
        return None

# Initialize OCR on startup (non-blocking)
print("\n" + "="*50)
print("Starting OCR Engine Initialization...")
print("="*50)
print(f"PaddleOCR available: {PADDLE_AVAILABLE}")
print(f"EasyOCR available: {EASYOCR_AVAILABLE}")
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
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    category = db.Column(db.String(100))
    allergen_free = db.Column(db.JSON, default=list)  # List of allergens it's free from
    ingredients_list = db.Column(db.JSON)
    rating = db.Column(db.Float, default=0.0)
    health_score = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float)
    is_organic = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============ DATABASE INITIALIZATION ============
with app.app_context():
    db.create_all()

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
        user = User.query.get(user_id)
        if user:
            return user
    
    # Create new user
    new_user = User(name=f"User_{uuid.uuid4().hex[:8]}")
    db.session.add(new_user)
    db.session.commit()
    return new_user

def extract_ingredients_section(full_text):
    """
    Extract only the text that appears under the 'Ingredients' section.
    Filters out all text before and after the ingredients statement.
    This significantly improves accuracy by focusing only on actual ingredients.
    """
    import re
    
    if not full_text:
        return ""
    
    # Split text into lines for processing
    lines = full_text.split('\n')
    
    # Find the line with "Ingredients" header
    ingredient_start_idx = None
    for i, line in enumerate(lines):
        if re.search(r'ingredients\s*:?', line, re.IGNORECASE):
            ingredient_start_idx = i + 1  # Start from line after "Ingredients:"
            break
    
    # If no ingredients section found, return original text as fallback
    if ingredient_start_idx is None:
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
                break
        if ingredient_end_idx != len(lines):
            break
    
    # Extract only the ingredients section
    ingredients_text = '\n'.join(lines[ingredient_start_idx:ingredient_end_idx])
    
    # Clean up the extracted text
    ingredients_text = ingredients_text.strip()
    
    # If we got something useful, return it; otherwise return original text as fallback
    if ingredients_text and len(ingredients_text.strip()) > 5:
        return ingredients_text
    else:
        return full_text

def extract_ingredients(text):
    """Extract ingredients from OCR text with improved manufacturing text and gibberish removal"""
    import re
    
    # Step 1: Remove manufacturing-related text patterns
    manufacturing_patterns = [
        # Batch/Lot codes
        r'lot\s*#?\s*[\dA-Z]+',
        r'batch\s*#?\s*[\dA-Z]+',
        r'code\s*#?\s*[\dA-Z]+',
        
        # Facility and distribution info
        r'(?:manufactured|made|produced|packaged)\s+(?:by|in|at).*?(?=\n|$)',
        r'(?:distributed|packed)\s+(?:by|in).*?(?=\n|$)',
        r'facility.*?(?=\n|$)',
        r'plant\s+#?\d+',
        r'gmp\s+(?:certified|facility)',
        
        # Contact/Address info (with variations)
        r'\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',  # Phone numbers
        r'\b\d{5}(?:\-\d{4})?\b',  # ZIP codes
        r'(?:address|street|ave|road|blvd|st|ln|dr).*?(?=\n|$)',
        r'(?:city|state|zip|postal).*?(?=\n|$)',
        
        # Patent/Copyright
        r'(?:copyright|©|\(c\)|patent|®|™).*?(?=\n|$)',
        r'©\s*\d{4}.*?(?=\n|$)',
        
        # Website/Email
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'(?:www\.|https?://)[^\s]+',  # Website
        
        # UPC/Barcode codes
        r'upc\s*[:\-]?\s*[\d\s]{10,}',
        r'ean\s*[:\-]?\s*[\d\s]{10,}',
        
        # Additional sections to remove
        r'nutrition\s+facts.*?(?=\n|$)',
        r'serving\s+size.*?(?=\n|$)',
        r'ingredients:?',
        r'contains:?',
        r'may\s+contain:?',
        r'allergen.*?:',
        r'warning.*?:',
        r'storage.*?:',
        r'directions.*?:',
        r'instructions.*?:',
        r'preparation.*?:',
        r'product\s+identification',
        r'best\s+by.*?(?=\n|$)',
        r'use\s+by.*?(?=\n|$)',
        r'packed\s+on.*?(?=\n|$)',
        r'net\s+weight.*?(?=\n|$)',
        r'carbohydrates?',
        r'protein',
        r'fat',
        r'vitamins?',
        r'minerals?',
        r'\d+\s*(?:g|mg|oz|ml|%)',  # Remove quantities
        r'per\s+serving',
        r'daily\s+value',
        r'[\*†‡§]',  # Remove special footnote markers
    ]
    
    # Step 2: Clean OCR gibberish before processing
    cleaned_text = text
    for pattern in manufacturing_patterns:
        cleaned_text = re.sub(pattern, ' ', cleaned_text, flags=re.IGNORECASE)
    
    # Step 3: Remove OCR gibberish patterns
    def is_gibberish(text):
        """Detect and filter OCR gibberish"""
        # Empty or whitespace only
        if not text or not text.strip():
            return True
        
        # Too many consecutive special characters or numbers
        special_count = sum(1 for c in text if c in '!@#$%^&*()_+=[]{}|;:,<>?/~`')
        if special_count / len(text) > 0.3:
            return True
        
        # Repetitive characters (OCR misreading)
        if re.search(r'([a-z])\1{4,}', text.lower()):  # 5+ same consecutive letters
            return True
        
        # High density of mixed case (sign of corruption)
        case_changes = sum(1 for i in range(len(text)-1) if text[i].isupper() != text[i+1].isupper())
        if case_changes / len(text) > 0.4:
            return True
        
        # Very long words with no vowels (corrupted words)
        for word in text.split():
            if len(word) > 5 and not any(v in word.lower() for v in 'aeiou'):
                return True
        
        # Contains only numbers and symbols
        if not any(c.isalpha() for c in text):
            return True
        
        return False
    
    # Split by various delimiters
    ingredients = re.split(r'[,;/\n\-•·]', cleaned_text)
    
    # Clean and filter ingredients
    filtered = []
    common_noise = {'and', 'or', 'the', 'a', 'of', 'contains', 'may', 'ingredients', 
                    'color', 'flavor', 'flavour', 'for', 'in', 'as', 'is', 'with', 'to'}
    
    for ing in ingredients:
        # Clean whitespace
        ing = ing.strip()
        
        # Skip empty or too short
        if not ing or len(ing) < 2:
            continue
        
        # Skip gibberish
        if is_gibberish(ing):
            continue
        
        # Skip if entirely numeric
        if ing.replace('.', '').replace('%', '').replace('(', '').replace(')', '').isdigit():
            continue
        
        # Skip if mostly parenthetical info (e.g., "(contains: ...)")
        if ')' in ing and ing.count('(') > 0:
            # Extract content between parens and check if it's useful
            paren_content = re.findall(r'\(([^)]*)\)', ing)
            if paren_content and any(p.lower() in ['contains', 'may contain', 'allergen info'] for p in paren_content):
                continue
        
        # Skip all noise words
        ing_lower = ing.lower()
        if ing_lower in common_noise or any(noise in ing_lower for noise in ['%', '100%', 'daily value']):
            continue
        
        # Check if it looks like actual ingredient (not header text)
        # Ingredients usually start with lowercase or are proper nouns
        if not ing[0].isupper() or ing.count(' ') < 5:  # Headers usually have many words
            filtered.append(ing)
    
    # Remove duplicates while preserving order, limit to 30 ingredients
    seen = set()
    unique = []
    for ing in filtered:
        ing_lower = ing.lower()
        if ing_lower not in seen:
            seen.add(ing_lower)
            unique.append(ing)
    
    return unique[:30]

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
        allergen_free = product.allergen_free or []
        # Check if product is free from all user allergens
        if all(allergen in allergen_free for allergen in user_allergens):
            products.append({
                'id': product.id,
                'name': product.name,
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
    return products[:5]  # Return top 5

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
            ocr.ocr(test_img, cls=False)
        except Exception as e:
            ocr_status = 'degraded'
            ocr_message = f'OCR engine is unresponsive: {str(e)}'
    
    return jsonify({
        'success': True,
        'status': ocr_status,
        'ocr_message': ocr_message,
        'timestamp': datetime.utcnow().isoformat()
    })

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
            
            # Apply some processing for better visibility
            frame = cv2.GaussianBlur(frame, (5, 5), 0)
            
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
            results = ocr.ocr(frame, cls=True)
        except Exception as ocr_error:
            print(f"OCR processing error: {ocr_error}")
            # Try to recover by reinitializing OCR
            ocr = initialize_ocr()
            if ocr is not None:
                try:
                    results = ocr.ocr(frame, cls=True)
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
    """Process image and extract ingredients with robust error handling"""
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
        
        # Convert image to RGB (remove alpha channel if present)
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array and ensure uint8 type
        image_np = np.array(image, dtype=np.uint8)
        
        # Validate array
        if image_np is None or image_np.size == 0:
            return jsonify({'success': False, 'error': 'Invalid image data'}), 400
        
        # Convert RGB to BGR for OpenCV/PaddleOCR compatibility
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        # Perform OCR with error handling and recovery
        try:
            results = ocr.ocr(image_np, cls=False)
        except Exception as ocr_error:
            print(f"OCR processing error on image: {ocr_error}")
            # Try to recover by reinitializing OCR
            ocr = initialize_ocr()
            if ocr is not None:
                try:
                    print("Retrying OCR after reinitialization...")
                    results = ocr.ocr(image_np, cls=False)
                except Exception as retry_error:
                    return jsonify({'success': False, 'error': f'OCR processing failed (retry also failed): {str(retry_error)}'}), 500
            else:
                return jsonify({'success': False, 'error': 'OCR engine failed and could not be recovered'}), 500
        
        # Extract text safely
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
            'confidence': 0.85
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Scanning failed: {str(e)}'}), 500

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
        
        # Calculate health score based on warnings found in SELECTED allergens only
        health_score = max(0, min(100, 100 - (len(warnings) * 15)))
        
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
            user = User.query.get(user_id)
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
            'safe_ingredients': safe_ingredients,
            'health_score': health_score,
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
        
        user = User.query.get(user_id)
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
        user = User.query.get(user_id)
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
        user = User.query.get(user_id)
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
        user = User.query.get(user_id)
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
        scan = Scan.query.get(scan_id)
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

# ============ PRODUCT RECOMMENDATIONS ============

@app.route('/api/products/recommend', methods=['POST'])
def recommend_products():
    """Get product recommendations based on allergens"""
    try:
        data = request.json or {}
        user_allergens = data.get('allergens', [])
        category = data.get('category', 'general')
        
        # Initialize sample products on first call
        if Product.query.count() == 0:
            init_sample_products()
        
        recommendations = suggest_products(user_allergens, category)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with filtering"""
    try:
        # Initialize sample products on first call
        if Product.query.count() == 0:
            init_sample_products()
        
        allergen_filter = request.args.get('allergen_free')
        category = request.args.get('category')
        
        query = Product.query
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.all()
        
        # Filter by allergen if specified
        if allergen_filter:
            products = [p for p in products if allergen_filter in (p.allergen_free or [])]
        
        result = [{
            'id': p.id,
            'name': p.name,
            'brand': p.brand,
            'category': p.category,
            'rating': p.rating,
            'health_score': p.health_score,
            'is_organic': p.is_organic,
            'price': p.price,
            'allergen_free': p.allergen_free
        } for p in products]
        
        return jsonify({
            'success': True,
            'products': result,
            'count': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get detailed product information"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'brand': product.brand,
                'category': product.category,
                'rating': product.rating,
                'health_score': product.health_score,
                'is_organic': product.is_organic,
                'price': product.price,
                'allergen_free': product.allergen_free,
                'ingredients_list': product.ingredients_list
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/alternatives/<allergen>', methods=['GET'])
def get_alternatives(allergen):
    """Get alternatives for a specific allergen"""
    if allergen in alternatives_db:
        return jsonify({
            'success': True,
            'allergen': allergen,
            'data': alternatives_db[allergen]
        })
    return jsonify({'success': False, 'error': 'Allergen not found'}), 404

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
    """Validate JSON content type for POST requests"""
    if request.method == 'POST':
        if not request.is_json and request.content_length is not None and request.content_length > 0:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
