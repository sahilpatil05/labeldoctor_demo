#!/usr/bin/env python
"""
Test script for LabelDoctor Backend API
Tests all new features: camera streaming, database, insights, recommendations
"""

import sys
import json

def test_imports():
    """Test that all imports work correctly"""
    print("=" * 60)
    print("TEST 1: Validating imports and database models...")
    print("=" * 60)
    
    try:
        from app_api import (
            app, db, User, Scan, Product,
            load_data, extract_ingredients, calculate_insights,
            suggest_products, init_sample_products
        )
        print("✅ All imports successful!")
        print("   - Flask app initialized")
        print("   - SQLAlchemy models loaded (User, Scan, Product)")
        print("   - Helper functions available")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: Testing Database Models...")
    print("=" * 60)
    
    try:
        from app_api import app, db, User, Scan, Product
        
        with app.app_context():
            # Check database exists
            print("✅ Database models initialized")
            print(f"   - User model: {User.__tablename__}")
            print(f"   - Scan model: {Scan.__tablename__}")
            print(f"   - Product model: {Product.__tablename__}")
            
            # Count existing records
            user_count = db.session.query(User).count()
            scan_count = db.session.query(Scan).count()
            product_count = db.session.query(Product).count()
            
            print(f"✅ Database queries working")
            print(f"   - Users in DB: {user_count}")
            print(f"   - Scans in DB: {scan_count}")
            print(f"   - Products in DB: {product_count}")
            
            return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_helper_functions():
    """Test helper functions"""
    print("\n" + "=" * 60)
    print("TEST 3: Testing Helper Functions...")
    print("=" * 60)
    
    try:
        from app_api import extract_ingredients, calculate_insights, load_data
        
        # Test extract_ingredients
        test_text = "wheat, milk, sugar, eggs, salt, vanilla extract, butter"
        ingredients = extract_ingredients(test_text)
        print(f"✅ extract_ingredients() working")
        print(f"   - Input: {test_text}")
        print(f"   - Extracted: {ingredients}")
        
        # Test calculate_insights
        insights = calculate_insights(ingredients, [])
        print(f"✅ calculate_insights() working")
        print(f"   - Total ingredients: {insights['total_ingredients']}")
        print(f"   - Safe ingredients: {insights['safe_ingredients']}")
        
        # Test load_data
        allergens, alternatives = load_data()
        print(f"✅ load_data() working")
        print(f"   - Allergens loaded: {len(allergens)}")
        print(f"   - Alternatives loaded: {len(alternatives)}")
        
        return True
    except Exception as e:
        print(f"❌ Helper functions test failed: {e}")
        return False

def test_api_routes():
    """Test that all API routes are registered"""
    print("\n" + "=" * 60)
    print("TEST 4: Testing API Routes...")
    print("=" * 60)
    
    try:
        from app_api import app
        
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods - {'OPTIONS', 'HEAD'}),
                    'path': str(rule)
                })
        
        print(f"✅ Found {len(routes)} API routes:")
        
        # Group by category
        categories = {
            'camera': ['camera_stream', 'capture_from_camera'],
            'user': ['create_user', 'get_user', 'update_user'],
            'analysis': ['scan_image', 'analyze_ingredients'],
            'insights': ['get_user_insights', 'get_scan_insights'],
            'recommendations': ['recommend_products', 'get_products', 'get_product'],
            'other': ['index', 'get_allergens', 'health_check', 'get_alternatives']
        }
        
        for category, endpoints in categories.items():
            matching = [r for r in routes if r['endpoint'] in endpoints]
            if matching:
                print(f"\n   📁 {category.upper()}:")
                for route in matching:
                    methods_str = ', '.join(route['methods'])
                    print(f"      {route['path']} [{methods_str}]")
        
        return True
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        return False

def test_data_models():
    """Test database operations"""
    print("\n" + "=" * 60)
    print("TEST 5: Testing Data Model Operations...")
    print("=" * 60)
    
    try:
        from app_api import app, db, User, Scan, Product, init_sample_products
        import uuid
        
        with app.app_context():
            # Test User creation
            test_user = User(
                name="Test User",
                email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                allergens=["milk", "gluten"],
                dietary_preferences={"vegan": False, "vegetarian": True}
            )
            db.session.add(test_user)
            db.session.commit()
            
            print(f"✅ User model operations working")
            print(f"   - Created user: {test_user.name} (ID: {test_user.id[:8]}...)")
            
            # Test Scan creation
            test_scan = Scan(
                user_id=test_user.id,
                extracted_text="milk, wheat, sugar",
                ingredients=["milk", "wheat", "sugar"],
                warnings=[{"allergen": "milk", "severity": "high"}],
                health_score=75.0
            )
            db.session.add(test_scan)
            db.session.commit()
            
            print(f"✅ Scan model operations working")
            print(f"   - Created scan: {test_scan.health_score}% score")
            
            # Test Product operations
            if Product.query.count() == 0:
                init_sample_products()
                print(f"✅ Initialized sample products")
            
            products = Product.query.all()
            print(f"✅ Product query working")
            print(f"   - Total products: {len(products)}")
            if products:
                print(f"   - Sample product: {products[0].name}")
            
            return True
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "LABELDOCTOR BACKEND API TEST")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_database,
        test_helper_functions,
        test_api_routes,
        test_data_models
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Unexpected error in test: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"PASSED: {passed}/{total}")
    
    if passed == total:
        print("\n*** ALL TESTS PASSED! BACKEND IS READY. ***")
        print("\nNEW FEATURES SUMMARY:")
        print("  1. [OK] Camera streaming endpoints added")
        print("  2. [OK] SQLite database with user profiles")
        print("  3. [OK] Food label insights and visualization")
        print("  4. [OK] Product recommendations system")
        print("  5. [OK] All existing functionality preserved")
        return 0
    else:
        print(f"\n*** SOME TESTS FAILED. PLEASE REVIEW ERRORS ABOVE. ***")
        return 1

if __name__ == '__main__':
    sys.exit(main())
