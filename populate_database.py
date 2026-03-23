"""
Database Population Script - Populate with sample products, users, and scans
Run this script to initialize the database with test data
"""

from app_api import app, db, User, Scan, Product
from datetime import datetime, timedelta
import uuid

def populate_products():
    """Populate the database with diverse product samples"""
    
    sample_products = [
        # Snacks
        {
            'name': 'Almond Joy Alternative Bar',
            'brand': 'Peaceful Organics',
            'category': 'Snack',
            'allergen_free': ['milk', 'gluten', 'egg'],
            'ingredients_list': ['coconut', 'almonds', 'cocoa', 'coconut oil'],
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
            'ingredients_list': ['quinoa', 'sunflower seeds', 'dried cranberries'],
            'rating': 4.6,
            'health_score': 9.0,
            'is_organic': True,
            'price': 3.49
        },
        {
            'name': 'Crispy Vegan Chips',
            'brand': 'Green Valley',
            'category': 'Snack',
            'allergen_free': ['gluten', 'peanut', 'milk', 'soy'],
            'ingredients_list': ['potatoes', 'sunflower oil', 'sea salt'],
            'rating': 4.4,
            'health_score': 6.5,
            'is_organic': False,
            'price': 1.99
        },
        
        # Spreads
        {
            'name': 'Dairy-Free Chocolate Spread',
            'brand': 'Pure Bliss',
            'category': 'Spread',
            'allergen_free': ['milk', 'gluten'],
            'ingredients_list': ['cocoa', 'coconut oil', 'agave syrup'],
            'rating': 4.7,
            'health_score': 7.5,
            'is_organic': False,
            'price': 4.99
        },
        {
            'name': 'Almond Butter Organic',
            'brand': 'Nature\'s Pure',
            'category': 'Spread',
            'allergen_free': ['gluten', 'milk', 'soy'],
            'ingredients_list': ['almonds', 'sea salt'],
            'rating': 4.9,
            'health_score': 8.8,
            'is_organic': True,
            'price': 5.49
        },
        {
            'name': 'Tahini Hummus',
            'brand': 'Mediterranean Gold',
            'category': 'Spread',
            'allergen_free': ['gluten', 'milk', 'egg'],
            'ingredients_list': ['sesame seeds', 'chickpeas', 'lemon juice', 'garlic'],
            'rating': 4.5,
            'health_score': 8.0,
            'is_organic': False,
            'price': 3.99
        },
        
        # Breakfast
        {
            'name': 'Gluten-Free Oat Cereal',
            'brand': 'Healthy Start',
            'category': 'Breakfast',
            'allergen_free': ['gluten', 'milk', 'peanut'],
            'ingredients_list': ['rolled oats', 'honey', 'cinnamon'],
            'rating': 4.3,
            'health_score': 8.2,
            'is_organic': True,
            'price': 4.49
        },
        {
            'name': 'Vegan Granola',
            'brand': 'Nutty Harvest',
            'category': 'Breakfast',
            'allergen_free': ['milk', 'gluten', 'egg'],
            'ingredients_list': ['oats', 'almonds', 'coconut', 'maple syrup'],
            'rating': 4.7,
            'health_score': 8.6,
            'is_organic': True,
            'price': 5.99
        },
        {
            'name': 'Protein Pancake Mix',
            'brand': 'FitMix',
            'category': 'Breakfast',
            'allergen_free': ['soy', 'peanut'],
            'ingredients_list': ['wheat flour', 'whey protein', 'baking powder'],
            'rating': 4.2,
            'health_score': 7.8,
            'is_organic': False,
            'price': 6.99
        },
        
        # Beverages
        {
            'name': 'Almond Milk Original',
            'brand': 'Plant Bliss',
            'category': 'Beverage',
            'allergen_free': ['milk', 'gluten', 'soy'],
            'ingredients_list': ['almonds', 'water', 'calcium'],
            'rating': 4.4,
            'health_score': 7.5,
            'is_organic': False,
            'price': 2.49
        },
        {
            'name': 'Coconut Water',
            'brand': 'Tropical Fresh',
            'category': 'Beverage',
            'allergen_free': ['gluten', 'milk', 'soy', 'peanut'],
            'ingredients_list': ['coconut water'],
            'rating': 4.6,
            'health_score': 8.5,
            'is_organic': True,
            'price': 2.99
        },
        {
            'name': 'Green Matcha Tea',
            'brand': 'Zen Tea',
            'category': 'Beverage',
            'allergen_free': ['gluten', 'milk', 'soy', 'tree_nut'],
            'ingredients_list': ['matcha powder'],
            'rating': 4.8,
            'health_score': 9.2,
            'is_organic': True,
            'price': 7.99
        },
        
        # Baked Goods
        {
            'name': 'Gluten-Free Bread',
            'brand': 'Pure Rise',
            'category': 'Baked Goods',
            'allergen_free': ['gluten', 'egg'],
            'ingredients_list': ['rice flour', 'tapioca starch', 'water', 'yeast'],
            'rating': 4.1,
            'health_score': 7.0,
            'is_organic': False,
            'price': 4.49
        },
        {
            'name': 'Vegan Chocolate Cookies',
            'brand': 'Sweet Bites',
            'category': 'Baked Goods',
            'allergen_free': ['milk', 'egg'],
            'ingredients_list': ['flour', 'coconut oil', 'chocolate chips', 'sugar'],
            'rating': 4.5,
            'health_score': 6.8,
            'is_organic': False,
            'price': 3.99
        },
    ]
    
    with app.app_context():
        for product_data in sample_products:
            existing = Product.query.filter_by(name=product_data['name']).first()
            if not existing:
                product = Product(**product_data)
                db.session.add(product)
                print(f"✓ Added product: {product_data['name']}")
        
        db.session.commit()
        print(f"\n✓ Total products in database: {Product.query.count()}")


def populate_users():
    """Populate the database with sample users"""
    
    sample_users = [
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'allergens': ['peanut', 'tree_nut', 'shellfish'],
            'dietary_preferences': {'vegan': False, 'vegetarian': False, 'gluten_free': False}
        },
        {
            'name': 'Sarah Smith',
            'email': 'sarah@example.com',
            'password': 'password456',
            'allergens': ['milk', 'gluten', 'egg'],
            'dietary_preferences': {'vegan': True, 'vegetarian': True, 'gluten_free': True}
        },
        {
            'name': 'Mike Johnson',
            'email': 'mike@example.com',
            'password': 'password789',
            'allergens': ['soy', 'sesame'],
            'dietary_preferences': {'vegan': False, 'vegetarian': True, 'gluten_free': False}
        },
        {
            'name': 'Emma Wilson',
            'email': 'emma@example.com',
            'password': 'password101',
            'allergens': ['gluten', 'milk'],
            'dietary_preferences': {'vegan': False, 'vegetarian': False, 'gluten_free': True}
        },
        {
            'name': 'Alex Brown',
            'email': 'alex@example.com',
            'password': 'password202',
            'allergens': ['peanut', 'milk', 'egg'],
            'dietary_preferences': {'vegan': True, 'vegetarian': True, 'gluten_free': False}
        },
    ]
    
    with app.app_context():
        for user_data in sample_users:
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(
                    name=user_data['name'],
                    email=user_data['email'],
                    allergens=user_data['allergens'],
                    dietary_preferences=user_data['dietary_preferences']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"✓ Added user: {user_data['name']} ({user_data['email']})")
        
        db.session.commit()
        print(f"\n✓ Total users in database: {User.query.count()}")


def populate_scans():
    """Populate the database with sample scan history"""
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("⚠ No users found. Please run populate_users() first.")
            return
        
        sample_scans = [
            {
                'user_idx': 0,
                'image_path': '/uploads/scan_001.jpg',
                'extracted_text': 'Ingredients: Wheat Flour, Sugar, Butter, Eggs, Vanilla',
                'ingredients': ['wheat flour', 'sugar', 'butter', 'eggs', 'vanilla'],
                'warnings': [
                    {'ingredient': 'wheat flour', 'severity': 'high', 'reason': 'Contains gluten'},
                    {'ingredient': 'eggs', 'severity': 'high', 'reason': 'Egg allergen'}
                ],
                'health_score': 5.2,
                'days_ago': 5
            },
            {
                'user_idx': 0,
                'image_path': '/uploads/scan_002.jpg',
                'extracted_text': 'Almonds, Sea Salt, Sunflower Oil',
                'ingredients': ['almonds', 'sea salt', 'sunflower oil'],
                'warnings': [
                    {'ingredient': 'almonds', 'severity': 'high', 'reason': 'Tree nut allergen'}
                ],
                'health_score': 8.5,
                'days_ago': 3
            },
            {
                'user_idx': 1,
                'image_path': '/uploads/scan_003.jpg',
                'extracted_text': 'Coconut Oil, Agave, Cocoa Powder',
                'ingredients': ['coconut oil', 'agave', 'cocoa powder'],
                'warnings': [],
                'health_score': 8.8,
                'days_ago': 2
            },
            {
                'user_idx': 1,
                'image_path': '/uploads/scan_004.jpg',
                'extracted_text': 'Quinoa, Sunflower Seeds, Dried Cranberries, Salt',
                'ingredients': ['quinoa', 'sunflower seeds', 'dried cranberries', 'salt'],
                'warnings': [],
                'health_score': 9.0,
                'days_ago': 1
            },
            {
                'user_idx': 2,
                'image_path': '/uploads/scan_005.jpg',
                'extracted_text': 'Chickpeas, Tahini, Lemon Juice, Garlic, Olive Oil',
                'ingredients': ['chickpeas', 'tahini', 'lemon juice', 'garlic', 'olive oil'],
                'warnings': [
                    {'ingredient': 'tahini', 'severity': 'medium', 'reason': 'Contains sesame'}
                ],
                'health_score': 8.2,
                'days_ago': 4
            },
            {
                'user_idx': 3,
                'image_path': '/uploads/scan_006.jpg',
                'extracted_text': 'Rice Flour, Water, Yeast, Salt',
                'ingredients': ['rice flour', 'water', 'yeast', 'salt'],
                'warnings': [],
                'health_score': 7.5,
                'days_ago': 6
            },
            {
                'user_idx': 4,
                'image_path': '/uploads/scan_007.jpg',
                'extracted_text': 'Rolled Oats, Honey, Cinnamon, Water',
                'ingredients': ['rolled oats', 'honey', 'cinnamon', 'water'],
                'warnings': [],
                'health_score': 8.6,
                'days_ago': 7
            },
        ]
        
        for scan_data in sample_scans:
            user = users[scan_data['user_idx']]
            created_at = datetime.utcnow() - timedelta(days=scan_data['days_ago'])
            
            scan = Scan(
                user_id=user.id,
                image_path=scan_data['image_path'],
                extracted_text=scan_data['extracted_text'],
                ingredients=scan_data['ingredients'],
                warnings=scan_data['warnings'],
                health_score=scan_data['health_score'],
                created_at=created_at
            )
            db.session.add(scan)
            print(f"✓ Added scan for user: {user.name}")
        
        db.session.commit()
        print(f"\n✓ Total scans in database: {Scan.query.count()}")


def clear_database():
    """Clear all data from database (use with caution!)"""
    with app.app_context():
        # Delete in correct order (foreign keys)
        Scan.query.delete()
        User.query.delete()
        Product.query.delete()
        db.session.commit()
        print("✓ Database cleared")


def main():
    """Main function to populate database"""
    print("\n" + "=" * 60)
    print("DATABASE POPULATION SCRIPT")
    print("=" * 60 + "\n")
    
    with app.app_context():
        # Show current state
        print("Current Database State:")
        print(f"  Users: {User.query.count()}")
        print(f"  Scans: {Scan.query.count()}")
        print(f"  Products: {Product.query.count()}\n")
    
    try:
        print("Populating Products...")
        print("-" * 60)
        populate_products()
        
        print("\n\nPopulating Users...")
        print("-" * 60)
        populate_users()
        
        print("\n\nPopulating Scans...")
        print("-" * 60)
        populate_scans()
        
        print("\n" + "=" * 60)
        print("DATABASE POPULATION COMPLETE!")
        print("=" * 60)
        
        # Show final state
        with app.app_context():
            print("\nFinal Database State:")
            print(f"  Users: {User.query.count()}")
            print(f"  Scans: {Scan.query.count()}")
            print(f"  Products: {Product.query.count()}\n")
            
            # Show sample user credentials
            print("Sample User Credentials:")
            print("-" * 60)
            users = User.query.all()
            for user in users:
                print(f"  Email: {user.email} | Password: password (see populate_database.py)")
        
    except Exception as e:
        print(f"\n❌ Error during population: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
