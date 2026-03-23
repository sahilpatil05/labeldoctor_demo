"""
Populate database with comprehensive food snacks organized by category.
This enables category-based alternative recommendations.
"""

from app_api import app, db, Product
import uuid

# Comprehensive food snacks database organized by category
FOOD_SNACKS_BY_CATEGORY = {
    'Fast Food': [
        {
            'name': 'Classic Burger',
            'brand': 'McDonald\'s',
            'allergens_free': ['dairy', 'gluten'],
            'rating': 3.5,
            'health_score': 35,
            'price': 4.99,
            'is_organic': False,
            'ingredients': ['beef patty', 'bun', 'lettuce', 'tomato', 'pickles', 'onion', 'sauce']
        },
        {
            'name': 'Grilled Chicken Sandwich',
            'brand': 'Chick-fil-A',
            'allergens_free': ['peanut', 'tree_nut'],
            'rating': 4.2,
            'health_score': 55,
            'price': 5.99,
            'is_organic': False,
            'ingredients': ['chicken breast', 'bun', 'butter', 'pickles']
        },
        {
            'name': 'Fish Fillet',
            'brand': 'McDonald\'s',
            'allergens_free': ['egg', 'tree_nut'],
            'rating': 3.8,
            'health_score': 45,
            'price': 5.49,
            'is_organic': False,
            'ingredients': ['fish fillet', 'bun', 'tartar sauce', 'lettuce']
        },
        {
            'name': 'Spicy Chicken Wrap',
            'brand': 'Taco Bell',
            'allergens_free': ['shellfish'],
            'rating': 4.0,
            'health_score': 50,
            'price': 4.79,
            'is_organic': False,
            'ingredients': ['chicken', 'tortilla', 'spices', 'lettuce', 'tomato', 'cheese']
        }
    ],
    'Healthy Snack': [
        {
            'name': 'Organic Granola Bar',
            'brand': 'Nature\'s Path',
            'allergens_free': ['shellfish', 'egg'],
            'rating': 4.6,
            'health_score': 78,
            'price': 2.99,
            'is_organic': True,
            'ingredients': ['oats', 'honey', 'almonds', 'coconut', 'cinnamon']
        },
        {
            'name': 'Raw Almond Butter',
            'brand': 'Justin\'s',
            'allergens_free': ['dairy', 'egg', 'gluten'],
            'rating': 4.7,
            'health_score': 82,
            'price': 6.99,
            'is_organic': True,
            'ingredients': ['raw almonds', 'sea salt', 'coconut oil']
        },
        {
            'name': 'Mixed Berry Trail Mix',
            'brand': 'Nutcase',
            'allergens_free': ['dairy', 'gluten'],
            'rating': 4.5,
            'health_score': 75,
            'price': 4.49,
            'is_organic': True,
            'ingredients': ['almonds', 'cashews', 'dried berries', 'dark chocolate']
        },
        {
            'name': 'Protein Energy Ball',
            'brand': 'Quest',
            'allergens_free': ['shellfish'],
            'rating': 4.4,
            'health_score': 72,
            'price': 3.49,
            'is_organic': False,
            'ingredients': ['whey protein', 'peanut butter', 'oats', 'honey']
        },
        {
            'name': 'Organic Kale Chips',
            'brand': 'Rhythm Superfoods',
            'allergens_free': ['peanut', 'tree_nut', 'dairy', 'gluten'],
            'rating': 4.3,
            'health_score': 76,
            'price': 4.99,
            'is_organic': True,
            'ingredients': ['kale', 'coconut oil', 'sea salt', 'spices']
        }
    ],
    'Salty Snack': [
        {
            'name': 'Classic Potato Chips',
            'brand': 'Lay\'s',
            'allergens_free': ['dairy', 'egg'],
            'rating': 4.1,
            'health_score': 40,
            'price': 3.49,
            'is_organic': False,
            'ingredients': ['potatoes', 'vegetable oil', 'salt']
        },
        {
            'name': 'Tortilla Chips',
            'brand': 'Tostitos',
            'allergens_free': ['dairy', 'tree_nut'],
            'rating': 4.2,
            'health_score': 45,
            'price': 3.99,
            'is_organic': False,
            'ingredients': ['corn', 'vegetable oil', 'salt']
        },
        {
            'name': 'Organic Salted Popcorn',
            'brand': 'Pop Secret',
            'allergens_free': ['dairy', 'peanut', 'tree_nut', 'gluten'],
            'rating': 4.3,
            'health_score': 52,
            'price': 2.99,
            'is_organic': True,
            'ingredients': ['popcorn kernels', 'coconut oil', 'sea salt']
        },
        {
            'name': 'Cheese Crackers',
            'brand': 'Cheez-It',
            'allergens_free': ['tree_nut'],
            'rating': 4.0,
            'health_score': 38,
            'price': 3.29,
            'is_organic': False,
            'ingredients': ['wheat flour', 'cheese', 'vegetable oil', 'salt']
        }
    ],
    'Sweet Snack': [
        {
            'name': 'Dark Chocolate Bar',
            'brand': 'Lindt',
            'allergens_free': ['dairy', 'peanut'],
            'rating': 4.6,
            'health_score': 65,
            'price': 3.99,
            'is_organic': False,
            'ingredients': ['cocoa solids', 'cocoa butter', 'sugar', 'soya lecithin']
        },
        {
            'name': 'Oatmeal Cookie',
            'brand': 'Mrs. Fields',
            'allergens_free': ['shellfish'],
            'rating': 4.2,
            'health_score': 48,
            'price': 2.49,
            'is_organic': False,
            'ingredients': ['oats', 'butter', 'sugar', 'eggs', 'flour']
        },
        {
            'name': 'Organic Date Bar',
            'brand': 'Larabar',
            'allergens_free': ['dairy', 'gluten', 'peanut', 'tree_nut'],
            'rating': 4.5,
            'health_score': 70,
            'price': 1.99,
            'is_organic': True,
            'ingredients': ['dates', 'almonds', 'sea salt']
        },
        {
            'name': 'Honey Granola Granola',
            'brand': 'Bob\'s Red Mill',
            'allergens_free': ['dairy'],
            'rating': 4.4,
            'health_score': 68,
            'price': 4.49,
            'is_organic': True,
            'ingredients': ['oats', 'honey', 'canola oil', 'almonds', 'sunflower seeds']
        }
    ],
    'Beverage': [
        {
            'name': 'Fresh Orange Juice',
            'brand': 'Tropicana',
            'allergens_free': ['dairy', 'gluten', 'peanut', 'tree_nut', 'shellfish'],
            'rating': 4.3,
            'health_score': 72,
            'price': 3.99,
            'is_organic': False,
            'ingredients': ['orange juice', 'water', 'natural flavoring']
        },
        {
            'name': 'Green Tea',
            'brand': 'Lipton',
            'allergens_free': ['dairy', 'gluten', 'peanut', 'tree_nut', 'shellfish', 'egg'],
            'rating': 4.5,
            'health_score': 80,
            'price': 2.49,
            'is_organic': True,
            'ingredients': ['green tea leaves', 'water']
        },
        {
            'name': 'Almond Milk',
            'brand': 'Almond Breeze',
            'allergens_free': ['dairy', 'gluten', 'peanut', 'shellfish', 'egg'],
            'rating': 4.4,
            'health_score': 75,
            'price': 2.99,
            'is_organic': False,
            'ingredients': ['almond milk', 'water', 'sea salt', 'xanthan gum']
        },
        {
            'name': 'Coconut Water',
            'brand': 'Vita Coco',
            'allergens_free': ['dairy', 'gluten', 'peanut', 'tree_nut', 'shellfish', 'egg'],
            'rating': 4.6,
            'health_score': 78,
            'price': 3.29,
            'is_organic': False,
            'ingredients': ['coconut water', 'natural flavoring']
        }
    ],
    'Breakfast': [
        {
            'name': 'Fruit & Nut Cereal',
            'brand': 'Nature Valley',
            'allergens_free': ['shellfish'],
            'rating': 4.3,
            'health_score': 65,
            'price': 3.99,
            'is_organic': True,
            'ingredients': ['oats', 'almonds', 'dried fruit', 'honey', 'cinnamon']
        },
        {
            'name': 'Greek Yogurt Cup',
            'brand': 'Fage',
            'allergens_free': ['gluten', 'peanut', 'tree_nut', 'shellfish'],
            'rating': 4.7,
            'health_score': 80,
            'price': 4.99,
            'is_organic': False,
            'ingredients': ['greek yogurt', 'live cultures', 'honey', 'fruit']
        },
        {
            'name': 'Wheat Bread',
            'brand': 'Dave\'s Killer Bread',
            'allergens_free': ['dairy', 'peanut', 'tree_nut', 'shellfish', 'egg'],
            'rating': 4.4,
            'health_score': 72,
            'price': 4.49,
            'is_organic': True,
            'ingredients': ['whole wheat', 'water', 'yeast', 'sea salt']
        },
        {
            'name': 'Protein Pancake Mix',
            'brand': 'Orgain',
            'allergens_free': ['shellfish'],
            'rating': 4.2,
            'health_score': 68,
            'price': 5.99,
            'is_organic': True,
            'ingredients': ['organic oats', 'whey protein', 'baking powder', 'sea salt']
        }
    ]
}

def populate_snacks():
    """Populate database with categorized food snacks"""
    with app.app_context():
        # Clear existing products (optional)
        # Product.query.delete()
        
        count = 0
        for category, snacks in FOOD_SNACKS_BY_CATEGORY.items():
            for snack in snacks:
                # Check if product already exists
                existing = Product.query.filter_by(name=snack['name'], brand=snack['brand']).first()
                if existing:
                    print(f"ℹ️ Product '{snack['name']}' already exists, skipping...")
                    continue
                
                product = Product(
                    id=str(uuid.uuid4()),
                    name=snack['name'],
                    brand=snack['brand'],
                    category=category,
                    allergen_free=snack['allergens_free'],
                    ingredients_list=snack['ingredients'],
                    rating=snack['rating'],
                    health_score=snack['health_score'],
                    price=snack['price'],
                    is_organic=snack['is_organic']
                )
                db.session.add(product)
                count += 1
                print(f"✓ Added: {snack['name']} ({category})")
        
        db.session.commit()
        print(f"\n✅ Successfully added {count} food products to database!")
        print(f"Categories: {', '.join(FOOD_SNACKS_BY_CATEGORY.keys())}")

if __name__ == '__main__':
    populate_snacks()
