"""
Simplified Label Doctor App - Demo Version
With OCR support for real image processing
Perfect for Hugging Face Spaces deployment
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
import base64
import io
from PIL import Image
import pytesseract

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'labeldoctor_demo_2026'

CORS(app, supports_credentials=True)

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

@app.route('/api/allergens', methods=['GET'])
def get_allergens():
    """Get all available allergens"""
    return jsonify({
        'success': True,
        'allergens': list(ALLERGEN_DATABASE.keys())
    })

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

@app.route('/api/scan', methods=['POST'])
def scan_image():
    """Scan image for ingredients using OCR"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        image_data = data.get('image', '')
        user_allergens = data.get('userAllergens', [])
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        # Decode base64 image
        try:
            # Remove data URI prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Optimize image for OCR
            # Resize to larger size for better OCR accuracy
            width, height = image.size
            if width < 800:
                scale = 800 / width
                new_width = 800
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Extract text using Tesseract OCR
            extracted_text = pytesseract.image_to_string(image)
            
            if not extracted_text or extracted_text.strip() == '':
                return jsonify({
                    'success': False,
                    'error': 'No text detected in image. Please use a clearer image of a food label.'
                }), 400
            
            # Extract ingredients from the OCR text
            ingredients = extract_ingredients(extracted_text)
            
            if not ingredients:
                return jsonify({
                    'success': False,
                    'error': 'Could not parse ingredients from image. Please ensure the label is clearly visible.'
                }), 400
            
            # Analyze the extracted ingredients
            warnings, safe_ingredients = detect_allergens(ingredients, user_allergens)
            
            # Calculate health score
            allergen_count = len(warnings)
            if allergen_count > 2:
                health_score = 30
                safety_status = 'unsafe'
            elif allergen_count > 0:
                health_score = 50
                safety_status = 'medium'
            else:
                health_score = 75
                safety_status = 'safe'
            
            return jsonify({
                'success': True,
                'extracted_text': extracted_text[:500],  # First 500 chars of OCR output
                'extracted_ingredients': ingredients,
                'total_ingredients': len(ingredients),
                'warnings': warnings,
                'allergen_count': len(warnings),
                'safe_ingredients': safe_ingredients,
                'safe_count': len(safe_ingredients),
                'health_score': health_score,
                'safety_status': safety_status,
                'product_name': 'Scanned Product',
                'message': f"Successfully extracted {len(ingredients)} ingredient(s). Found {len(warnings)} allergen(s)."
            })
        
        except (ValueError, OSError) as e:
            return jsonify({'success': False, 'error': f'Invalid image format: {str(e)}'}), 400
    
    except Exception as e:
        print(f'Scan error: {str(e)}')
        return jsonify({'success': False, 'error': f'Error processing image: {str(e)}'}), 500

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
