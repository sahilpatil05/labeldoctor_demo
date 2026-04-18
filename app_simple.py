"""
Simplified Label Doctor App - Demo Version
No heavy dependencies (no OpenCV, no EasyOCR)
Perfect for Hugging Face Spaces deployment
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from datetime import datetime
import json
import os
import hashlib

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'labeldoctor_demo_2026'

CORS(app, supports_credentials=True)

# ============ USER STORAGE (in-memory for demo) ============
USERS_DB = {}  # Format: {email: {name, password_hash, allergens, dietary_preferences}}
SESSIONS = {}  # Format: {session_id: {user_id, email, name}}

# ============ DEMO DATA ============

ALLERGEN_DATABASE = {
    'wheat': {'severity': 'high', 'description': 'Contains gluten'},
    'milk': {'severity': 'high', 'description': 'Dairy allergen'},
    'eggs': {'severity': 'high', 'description': 'Contains eggs'},
    'soy': {'severity': 'medium', 'description': 'Soy-based ingredient'},
    'peanut': {'severity': 'high', 'description': 'Tree nut allergen'},
    'tree nuts': {'severity': 'high', 'description': 'Tree nut allergen'},
    'sesame': {'severity': 'medium', 'description': 'Sesame allergen'},
}

DEMO_PRODUCTS = {
    'cookie': {
        'name': 'Chocolate Chip Cookie',
        'ingredients': ['wheat flour', 'sugar', 'butter', 'eggs', 'chocolate chips', 'salt', 'baking soda'],
        'allergens': ['wheat', 'milk', 'eggs'],
        'health_score': 35,
    },
    'bread': {
        'name': 'Whole Wheat Bread',
        'ingredients': ['wheat flour', 'water', 'yeast', 'salt', 'sugar'],
        'allergens': ['wheat'],
        'health_score': 65,
    },
    'snack': {
        'name': 'Peanut Butter Bar',
        'ingredients': ['peanut butter', 'oats', 'honey', 'chocolate'],
        'allergens': ['peanut'],
        'health_score': 45,
    },
    'cereal': {
        'name': 'Corn Flakes Cereal',
        'ingredients': ['corn', 'sugar', 'salt', 'malt flavoring'],
        'allergens': [],
        'health_score': 40,
    },
}

# ============ HELPER FUNCTIONS ============

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def get_current_user():
    """Get currently logged-in user from session"""
    user_id = session.get('user_id')
    if user_id and user_id in USERS_DB:
        user_data = USERS_DB[user_id]
        return {
            'user_id': user_id,
            'name': user_data.get('name'),
            'email': user_id,  # Using email as user_id
            'allergens': user_data.get('allergens', []),
            'dietary_preferences': user_data.get('dietary_preferences', {})
        }
    return None

def extract_ingredients(text):
    """Extract ingredients from text by splitting on commas/semicolons"""
    if not text:
        return []
    
    # Replace common delimiters with commas
    text = text.replace(';', ',').replace('\n', ',')
    
    # Split and clean
    ingredients = []
    for item in text.split(','):
        item = item.strip().lower()
        if item and len(item) > 2 and any(c.isalpha() for c in item):
            # Remove parenthetical info
            item = item.split('(')[0].strip()
            if item not in ingredients:
                ingredients.append(item)
    
    return ingredients

def detect_allergens(ingredients, user_allergens):
    """Check ingredients against user allergens"""
    warnings = []
    safe_ingredients = []
    
    user_allergens_lower = [a.lower() for a in user_allergens]
    
    for ingredient in ingredients:
        found_allergen = False
        for allergen in user_allergens_lower:
            if allergen in ingredient:
                if allergen in ALLERGEN_DATABASE:
                    warnings.append({
                        'allergen': allergen,
                        'ingredient': ingredient,
                        'severity': ALLERGEN_DATABASE[allergen]['severity'],
                        'description': ALLERGEN_DATABASE[allergen]['description'],
                    })
                found_allergen = True
                break
        
        if not found_allergen:
            safe_ingredients.append(ingredient)
    
    return warnings, safe_ingredients

# ============ ROUTES ============

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'Label Doctor Demo is running',
        'timestamp': datetime.utcnow().isoformat()
    })

# ============ AUTHENTICATION ROUTES ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not name or not email or not password:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        if email in USERS_DB:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Register user
        USERS_DB[email] = {
            'name': name,
            'password_hash': hash_password(password),
            'allergens': [],
            'dietary_preferences': {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Create session
        session['user_id'] = email
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user_id': email,
            'name': name,
            'email': email
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Missing email or password'}), 400
        
        if email not in USERS_DB:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        user_data = USERS_DB[email]
        if not verify_password(password, user_data['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Create session
        session['user_id'] = email
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user_id': email,
            'name': user_data['name'],
            'email': email,
            'allergens': user_data.get('allergens', []),
            'dietary_preferences': user_data.get('dietary_preferences', {})
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        session.pop('user_id', None)
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/current-user', methods=['GET'])
def current_user():
    """Get current logged-in user"""
    try:
        user = get_current_user()
        if user:
            return jsonify({'success': True, **user})
        else:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<user_id>', methods=['GET', 'POST'])
def user_profile(user_id):
    """Get or update user profile"""
    try:
        current = get_current_user()
        if not current or current['user_id'] != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        if request.method == 'POST':
            # Update user profile
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            user_data = USERS_DB[user_id]
            if 'allergens' in data:
                user_data['allergens'] = data['allergens']
            if 'dietary_preferences' in data:
                user_data['dietary_preferences'] = data['dietary_preferences']
            
            return jsonify({
                'success': True,
                'message': 'Profile updated',
                'allergens': user_data.get('allergens', []),
                'dietary_preferences': user_data.get('dietary_preferences', {})
            })
        else:
            # Get user profile
            user_data = USERS_DB[user_id]
            return jsonify({
                'success': True,
                'user_id': user_id,
                'name': user_data['name'],
                'email': user_id,
                'allergens': user_data.get('allergens', []),
                'dietary_preferences': user_data.get('dietary_preferences', {})
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/insights/<user_id>', methods=['GET', 'POST'])
def user_insights(user_id):
    """Get or save user scan insights"""
    try:
        current = get_current_user()
        if not current or current['user_id'] != user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
        if request.method == 'POST':
            # Save scan result
            data = request.json
            user_data = USERS_DB[user_id]
            if 'scan_history' not in user_data:
                user_data['scan_history'] = []
            user_data['scan_history'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'result': data
            })
            return jsonify({'success': True, 'message': 'Scan saved'})
        else:
            # Get insights
            user_data = USERS_DB[user_id]
            scan_history = user_data.get('scan_history', [])
            total_scans = len(scan_history)
            avg_health_score = 0
            
            if scan_history:
                health_scores = [s['result'].get('health_score', 50) for s in scan_history]
                avg_health_score = sum(health_scores) / len(health_scores)
            
            return jsonify({
                'success': True,
                'total_scans': total_scans,
                'avg_health_score': round(avg_health_score, 1),
                'scan_history': scan_history[-5:]  # Last 5 scans
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_ingredients():
    """Analyze text ingredients for allergens"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        ingredients_text = data.get('ingredientsText', '')
        user_allergens = data.get('userAllergens', [])
        
        if not ingredients_text:
            return jsonify({'success': False, 'error': 'No ingredients provided'}), 400
        
        # Extract and analyze
        ingredients = extract_ingredients(ingredients_text)
        warnings, safe_ingredients = detect_allergens(ingredients, user_allergens)
        
        # Calculate health score
        allergen_count = len(warnings)
        if allergen_count > 2:
            health_score = 30
            safety_status = 'unsafe'
        elif allergen_count == 1:
            health_score = 50
            safety_status = 'medium'
        else:
            health_score = 75
            safety_status = 'safe'
        
        return jsonify({
            'success': True,
            'ingredients': ingredients,
            'total_ingredients': len(ingredients),
            'warnings': warnings,
            'allergen_count': len(warnings),
            'safe_ingredients': safe_ingredients,
            'safe_count': len(safe_ingredients),
            'health_score': health_score,
            'safety_status': safety_status,
            'message': f"Found {len(warnings)} allergen(s)" if warnings else "No allergens detected"
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/demo/scan', methods=['GET'])
def demo_scan():
    """Get demo product for testing"""
    demo_type = request.args.get('type', 'cookie')
    product = DEMO_PRODUCTS.get(demo_type, DEMO_PRODUCTS['cookie'])
    
    demo_user_allergens = ['wheat', 'milk', 'eggs']
    warnings, safe_ingredients = detect_allergens(product['ingredients'], demo_user_allergens)
    
    return jsonify({
        'success': True,
        'demo_mode': True,
        'product_name': product['name'],
        'extracted_ingredients': product['ingredients'],
        'total_ingredients': len(product['ingredients']),
        'warnings': warnings,
        'allergen_count': len(warnings),
        'safe_ingredients': safe_ingredients,
        'safe_count': len(safe_ingredients),
        'health_score': product['health_score'],
        'safety_status': 'unsafe' if len(warnings) > 2 else ('medium' if len(warnings) > 0 else 'safe'),
        'demo_user_allergens': demo_user_allergens,
        'message': f"Demo: {product['name']} - Found {len(warnings)} allergen(s)"
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get list of demo products"""
    products = [
        {'id': k, 'name': v['name']} 
        for k, v in DEMO_PRODUCTS.items()
    ]
    return jsonify({'success': True, 'products': products})

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(debug=False, host='0.0.0.0', port=port)
