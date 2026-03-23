import streamlit as st
from paddleocr import PaddleOCR
import cv2
import numpy as np
import base64
import json
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="LabelDoctor", layout="wide")

# ---------- PROFESSIONAL STYLING ----------
def apply_professional_theme():
    css = """
    <style>
    :root {
        --primary-color: #10B981;
        --secondary-color: #059669;
        --accent-color: #F59E0B;
        --text-dark: #1F2937;
        --text-light: #F9FAFB;
        --border-color: #E5E7EB;
        --shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%);
        min-height: 100vh;
    }
    
    [data-testid="stMainBlockContainer"] {
        padding: 2rem;
    }
    
    * {
        color: #FFFFFF !important;
    }
    
    .banner {
        background: url('file:///c:/Users/mansi/Desktop/Label-Doctor/ingredient-scanner-main/bg1.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        padding: 0;
        border-radius: 16px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        margin: 20px 0 30px 0;
        text-align: center;
        position: relative;
        overflow: hidden;
        min-height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .banner .main-heading {
        position: relative;
        z-index: 2;
        padding: 0 20px;
    }
    
    .main-heading {
        font-size: 56px;
        font-weight: 900;
        text-align: center;
        margin: 0;
        color: #FFFFFF;
        letter-spacing: -1px;
        text-shadow: 0 4px 15px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 2;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        word-spacing: 100vw;
        padding: 20px;
    }
    
    .section-header {
        font-size: 24px;
        font-weight: 900;
        color: #FFFFFF;
        margin: 30px 0 20px 0;
        border-left: 6px solid #22C55E;
        padding-left: 18px;
        display: flex;
        align-items: center;
        text-transform: none;
        letter-spacing: 0.5px;
    }
    
    .info-banner {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.05) 100%);
        border-left: 5px solid #FFFFFF;
        border-radius: 8px;
        padding: 16px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #FFFFFF;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
        color: white !important;
        border-radius: 8px;
        font-weight: 700;
        border: none;
        padding: 12px 28px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 15px;
        letter-spacing: 0.3px;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #34D399 0%, #22C55E 100%);
        box-shadow: 0 8px 25px rgba(52, 211, 153, 0.5);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    input[type="text"], input[type="password"] {
        width: 100% !important;
        padding: 12px 14px !important;
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 8px !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        color: #1F2937 !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    input[type="text"]:focus, input[type="password"]:focus {
        border-color: #22C55E !important;
        box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2) !important;
        background-color: #FFFFFF !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    p, label, span, div {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(30, 90, 30, 0.8) 0%, rgba(20, 70, 20, 0.9) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 2px 0 15px rgba(0,0,0,0.3);
    }
    
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        gap: 10px;
        background: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-bottom: none !important;
    }
    
    .stTabs [role="tab"] {
        background: transparent !important;
        border: none !important;
        color: #FFFFFF !important;
        padding: 12px 20px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #22C55E !important;
        border-bottom: 3px solid #22C55E !important;
        background: transparent !important;
    }
    
    .stTabs [aria-selected="false"] {
        color: rgba(255, 255, 255, 0.7) !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
    }
    
    .stCheckbox {
        margin: 10px 0;
    }
    
    .stCheckbox>label {
        font-weight: 600;
        color: #FFFFFF !important;
        transition: all 0.2s ease;
    }
    
    .stCheckbox>label:hover {
        color: #22C55E !important;
    }
    
    .stExpander {
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        margin: 10px 0;
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .stExpander:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-color: #22C55E;
    }
    
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.15) !important;
        border: 2px solid #22C55E !important;
        border-radius: 8px !important;
        padding: 14px !important;
        color: #FFFFFF !important;
    }
    
    .stError {
        background-color: rgba(239, 68, 68, 0.15) !important;
        border: 2px solid #EF4444 !important;
        border-radius: 8px !important;
        padding: 14px !important;
        color: #FFFFFF !important;
    }
    
    .stWarning {
        background-color: rgba(245, 158, 11, 0.15) !important;
        border: 2px solid #F59E0B !important;
        border-radius: 8px !important;
        padding: 14px !important;
        color: #FFFFFF !important;
    }
    
    .stInfo {
        background-color: rgba(59, 130, 246, 0.15) !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 8px !important;
        padding: 14px !important;
        color: #FFFFFF !important;
    }
    
    hr {
        border: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        margin: 20px 0;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

apply_professional_theme()

# ---------- SESSION STATE ----------
if "users" not in st.session_state:
    st.session_state.users = {"demo@example.com": "1234"}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------- AUTH FUNCTIONS ----------
def login(email, password):
    users = st.session_state.users
    if email in users and users[email] == password:
        st.session_state.authenticated = True
        st.success("✅ Login successful!")
        st.experimental_rerun()
    else:
        st.error("❌ Invalid credentials.")

def signup(email, password):
    users = st.session_state.users
    if email in users:
        st.warning("⚠️ User already exists. Please log in.")
    else:
        users[email] = password
        st.success("✅ Signup successful! Please log in.")
        st.experimental_rerun()

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

# ---------- ALLERGEN DATA (MERGED JSON) ----------
allergen_data = {
    # Major Allergens (with hidden / alternative names)
    "milk": ["milk", "cow's milk", "whole milk", "skim milk", "lactose", "whey", "casein", "buttermilk", "butterfat", "cream", "cheese", "yogurt"],
    "egg": ["egg", "eggs", "egg white", "egg yolk", "albumin", "ovalbumin", "lysozyme", "egg protein"],
    "peanut": ["peanut", "peanuts", "groundnut", "arachis oil", "peanut butter", "peanut flour"],
    "tree_nut": ["almond", "walnut", "cashew", "hazelnut", "pecan", "pistachio", "brazil nut", "macadamia", "tree nuts", "nut oils"],
    "soy": ["soy", "soya", "soybean", "soy protein", "soy lecithin", "tofu", "edamame", "soya sauce"],
    "wheat_gluten": ["wheat", "barley", "rye", "malt", "malt extract", "triticale", "wheat starch", "hydrolyzed wheat protein", "gluten"],
    "fish": ["fish", "salmon", "tuna", "cod", "haddock", "anchovy", "bass", "trout", "fish oil"],
    "shellfish": ["shellfish", "shrimp", "prawn", "crab", "lobster", "scallop", "mollusc", "molluscs", "clam", "oyster"],
    "sesame": ["sesame", "sesame seed", "sesame oil", "tahini", "benne seed", "gingelly", "sesamol"],
    "mustard": ["mustard", "mustard seed", "mustard flour", "mustard greens", "prepared mustard"],
    "celery": ["celery", "celeriac", "celery seed", "celery salt"],
    "sulphite": ["sulphite", "sulfite", "sulfur dioxide", "metabisulphite", "potassium bisulphite", "E220", "E221", "E222", "E223", "E224", "E226"],

    # Intolerances / Sensitivities / Diet-types (with hidden names)
    "lactose_intolerant": ["lactose", "milk powder", "whey", "lactase deficient", "dairy", "milk solids"],
    "gluten_intolerant": ["wheat", "barley", "rye", "malt", "triticale", "gluten", "hydrolysed wheat", "bread crumbs"],
    "fructose_intolerant": ["fructose", "high fructose corn syrup", "corn syrup", "honey", "fruit juice concentrate", "invert sugar"],
    "histamine_intolerant": ["fermented", "aged cheese", "wine", "beer", "smoked", "cured meat", "pickled", "processed fish"],
    "sugar_intolerant": ["sugar", "sucrose", "glucose", "fructose", "corn syrup", "dextrose", "maltose", "evaporated cane juice", "brown rice syrup"],
    "maida_intolerant": ["refined flour", "maida", "white flour", "all-purpose flour", "enriched wheat flour"],
    "vegan": ["egg", "eggs", "milk", "butter", "cheese", "gelatin", "honey", "dairy", "lactose", "casein", "whey"],
    "vegetarian": ["gelatin", "fish", "meat", "chicken", "beef", "pork", "shellfish", "seafood"],
    "keto": ["sugar", "glucose", "dextrose", "maida", "rice", "potato", "corn", "bread", "pasta", "cereal"],
    "diabetic_friendly": ["sugar", "sucrose", "glucose", "fructose", "corn syrup", "dextrose", "high glucose syrup"],
    "low_sodium": ["salt", "sodium", "monosodium glutamate", "msg", "sodium nitrite", "sodium benzoate"],
    "heart_safe": ["trans fat", "partially hydrogenated oil", "hydrogenated oil", "palm oil", "shortening", "cholesterol", "saturated fat high"]
}


# ---------- LOGIN / SIGNUP ----------
if not st.session_state.authenticated:
    st.markdown("""
    <div class='banner'>
        <div class='main-heading'>🍏 LabelDoctor</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 16px; text-align: center; color: rgba(255,255,255,0.95); font-weight: 600; margin-bottom: 35px; letter-spacing: 0.3px;'>⚡ Find your perfect products instantly | AI-Powered Ingredient Detection</p>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown("<p class='section-header'>🔐 Account Access</p>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Login", "Sign Up"])

        with tab1:
            st.markdown("**Email Address**")
            email = st.text_input("Enter your email", key="login_email", label_visibility="collapsed")
            st.markdown("**Password**")
            password = st.text_input("Enter your password", type="password", key="login_password", label_visibility="collapsed")
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                if st.button("🔓 Login", use_container_width=True):
                    login(email, password)

        with tab2:
            st.markdown("**Email Address**")
            new_email = st.text_input("Create an email", key="signup_email", label_visibility="collapsed")
            st.markdown("**Password**")
            new_password = st.text_input("Create a password", type="password", key="signup_password", label_visibility="collapsed")
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                if st.button("✨ Sign Up", use_container_width=True):
                    signup(new_email, new_password)

        st.markdown("---")
        st.info("💡 **Demo Credentials**\n\nEmail: `demo@example.com`\n\nPassword: `1234`")

    with right_col:
        st.markdown("<p class='section-header'>📚 Health Tips</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 13px; color: #FFFFFF; margin-bottom: 15px;'>Learn about allergies and dietary preferences</p>", unsafe_allow_html=True)
        blogs = {
    "🍋 Benefits of Lemon Water": """
Lemon water is one of the simplest yet most powerful drinks for your health. It provides a great dose of vitamin C, which strengthens immunity and helps fight infections. 
Drinking it first thing in the morning kickstarts your metabolism and flushes out toxins. 
It also supports digestion by stimulating bile production and balancing stomach acids. 
For clear skin, the antioxidants in lemon water help reduce blemishes and promote a radiant glow. 
If you suffer from acidity, a diluted glass of lemon water can actually alkalize your body. 
Remember not to overdo it — always dilute it well and rinse your mouth afterward to protect your tooth enamel.
""",

    "🍎 Why Eat an Apple a Day": """
The old saying “An apple a day keeps the doctor away” is surprisingly true! 
Apples are rich in dietary fiber, which aids digestion and promotes gut health. 
They are also loaded with antioxidants like quercetin that protect cells from damage. 
Eating apples regularly can lower the risk of heart disease and improve cholesterol balance. 
Their natural sugars are slowly released, providing sustained energy without sugar spikes. 
Apples also contribute to hydration, as they contain nearly 85% water. 
For the best health benefits, eat apples with the skin — that’s where most nutrients are!
""",

    "🥗 Importance of a Balanced Diet": """
A balanced diet is the foundation of good health and well-being. 
It ensures that your body receives the right proportions of carbohydrates, proteins, fats, vitamins, and minerals. 
Eating a mix of colorful fruits, vegetables, grains, and proteins helps your body repair tissues, generate energy, and fight illness. 
Too much of one nutrient or too little of another can lead to deficiencies or lifestyle diseases. 
Whole foods should make up most of your plate, while processed items should be limited. 
Hydration is equally important — water aids nutrient absorption and detoxification. 
Balance is the key — moderation, variety, and mindful eating make a real difference.
""",

    "🥑 Good Fats vs Bad Fats": """
Not all fats are your enemies — in fact, good fats are essential for heart health, hormone balance, and brain function. 
Healthy fats include monounsaturated and polyunsaturated fats found in foods like avocados, nuts, seeds, and olive oil. 
These fats can lower bad cholesterol (LDL) and increase good cholesterol (HDL). 
Bad fats, on the other hand, include trans fats and hydrogenated oils found in fried and processed foods. 
These increase the risk of heart disease, stroke, and inflammation. 
Always cook with minimal oil and choose oils like olive, sunflower, or canola over butter or margarine. 
Remember — it’s about quality and quantity. A handful of nuts a day keeps your heart happy!
""",

    "🍞 Understanding Gluten": """
Gluten is a protein found in grains such as wheat, barley, and rye. 
It helps dough rise and gives bread its chewy texture. 
However, some people experience gluten intolerance or celiac disease — a condition where gluten damages the small intestine. 
Symptoms can include bloating, fatigue, and digestive distress. 
For those affected, gluten-free diets can significantly improve health. 
Alternatives like rice flour, almond flour, and millet can replace wheat in cooking and baking. 
Even for non-allergic individuals, reducing refined gluten sources may improve digestion and energy levels.
""",

    "🥛 Lactose Intolerance Fix": """
Lactose intolerance occurs when the body lacks the enzyme lactase, which digests lactose in milk. 
This can cause bloating, cramps, or diarrhea after consuming dairy. 
Fortunately, there are plenty of alternatives — lactose-free milk, almond milk, soy milk, and oat milk are delicious and nutritious. 
Yogurt and aged cheeses may also be easier to digest, as they contain less lactose. 
Reading food labels carefully can help avoid hidden lactose in processed foods. 
Calcium can still be obtained from non-dairy sources like leafy greens, tofu, and fortified cereals.
""",

    "🍫 Sugar Cravings & Healthy Fixes": """
Sugar cravings are natural — your brain craves quick energy! 
But processed sugar causes spikes in blood glucose, leading to fatigue and mood swings later. 
Instead of candy or desserts, try natural sweeteners like dates, figs, or jaggery in moderation. 
Dark chocolate (70% cocoa or higher) satisfies sweet cravings while providing antioxidants. 
Pairing protein or fiber-rich foods with a small sweet treat can help stabilize blood sugar. 
Over time, reducing sugar intake sharpens your taste buds, and even fruits begin to taste sweeter!
""",

    "🌾 Go Whole Grain": """
Whole grains like brown rice, oats, quinoa, and whole wheat are rich in fiber, B vitamins, and essential minerals. 
They improve digestion, promote satiety, and help control cholesterol. 
Unlike refined grains, they contain the bran, germ, and endosperm — the most nutritious parts of the grain. 
Regular consumption of whole grains can reduce the risk of heart disease, diabetes, and obesity. 
Start your day with oats or switch to brown rice for dinner — your gut will thank you!
""",

    "🍇 Antioxidant Power of Berries": """
Berries such as blueberries, strawberries, raspberries, and blackberries are nutrient powerhouses. 
They are packed with antioxidants like anthocyanins and vitamin C, which protect your cells from free radical damage. 
Eating berries regularly supports brain function, slows aging, and strengthens immunity. 
They are also low in calories but high in fiber, making them perfect for weight control. 
Add them to smoothies, oatmeal, or salads for a colorful, health-boosting treat.
""",

    "🥕 Eat the Rainbow": """
The phrase “Eat the Rainbow” reminds us to include colorful fruits and vegetables in our meals. 
Each color represents a unique set of nutrients — red foods like tomatoes boost heart health, orange foods like carrots improve vision, and green veggies support detoxification. 
Purple and blue foods like berries promote brain health, while white foods like garlic boost immunity. 
The more variety on your plate, the broader your nutrient intake. 
So next time you cook, aim to make your plate as colorful as a rainbow — your body will love you for it!
""",

    "🍵 Green Tea Benefits": """
Green tea has been celebrated for centuries as a wellness elixir. 
It’s rich in catechins, a type of antioxidant that supports fat metabolism and protects the heart. 
Regular consumption may aid weight loss by enhancing thermogenesis (fat burning). 
It also helps reduce stress, improve mental clarity, and lower the risk of chronic diseases. 
Replace your sugary beverages with 2–3 cups of green tea a day to stay fresh and focused.
""",

    "🍊 Vitamin C Foods": """
Vitamin C is a powerful antioxidant that boosts your immune system and enhances skin glow. 
It helps your body absorb iron and repair tissues. 
Foods rich in vitamin C include oranges, guava, kiwi, strawberries, and bell peppers. 
A deficiency can cause fatigue, slow healing, and gum problems. 
Since vitamin C isn’t stored in the body, you need it daily from fresh foods. 
Start your mornings with a fruit salad or citrus juice to meet your daily dose naturally.
"""
}

        for title, content in blogs.items():
            with st.expander(title):
                st.write(content)

# ---------- MAIN APP ----------
else:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col3:
        st.sidebar.button("🚪 Logout", on_click=logout, use_container_width=True)
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("❓ Allergy & Diet Guide", expanded=False):
        st.markdown(
            """
            <div style='max-height:400px; overflow-y:auto; padding-right:10px'>
            <b>🥛 Milk Allergy:</b> Reaction to milk proteins like casein and whey. Avoid dairy, cheese, butter, yogurt.<br><br>
            <b>🥚 Egg Allergy:</b> Caused by egg proteins. Found in cakes, mayonnaise, and baked foods.<br><br>
            <b>🥜 Peanut Allergy:</b> Common severe allergy. Avoid peanuts, peanut oil, and peanut butter.<br><br>
            <b>🌰 Tree Nut Allergy:</b> Includes almonds, walnuts, cashews, pistachios. Check for nut oils.<br><br>
            <b>🌾 Gluten Intolerance:</b> Found in wheat, barley, rye. Choose gluten-free grains like rice, quinoa.<br><br>
            <b>🍣 Fish Allergy:</b> Avoid all types of fish and fish sauce. Common in Asian cuisines.<br><br>
            <b>🦐 Shellfish Allergy:</b> Avoid prawns, crab, shrimp, lobster, clams, oysters.<br><br>
            <b>🌱 Soy Allergy:</b> Found in soy sauce, tofu, soy protein. Read labels carefully.<br><br>
            <b>🥯 Sesame Allergy:</b> Includes sesame seeds, tahini, sesame oil. Common in breads.<br><br>
            <b>🌿 Mustard Allergy:</b> Avoid mustard condiments, dressings, and mustard oil.<br><br>
            <b>🥬 Celery Allergy:</b> Common in soups, spice mixes, and seasonings.<br><br>
            <b>🧂 Sulphite Sensitivity:</b> Avoid dried fruits, wines, and processed foods with E220–E224.<br><br>
            <b>🥛 Lactose Intolerance:</b> Body lacks enzyme lactase. Use lactose-free milk or plant alternatives.<br><br>
            <b>🍞 Maida Intolerance:</b> Caused by refined white flour. Prefer whole-grain or millet alternatives.<br><br>
            <b>🍭 Sugar Intolerance:</b> Affects blood sugar balance. Choose fruits or natural sweeteners.<br><br>
            <b>🥑 Vegan:</b> Avoid all animal products including dairy, eggs, and honey.<br><br>
            <b>🥗 Vegetarian:</b> Avoid meat, fish, poultry. Eggs and dairy may be optional.<br><br>
            <b>🥩 Keto:</b> Low-carb, high-fat diet. Avoid sugar, grains, and starchy foods.<br><br>
            <b>🩸 Diabetic Friendly:</b> Low sugar, high fiber foods preferred. Avoid syrups and sweets.<br><br>
            <b>🧘 Low Sodium:</b> Minimize salt, processed snacks, and sodium preservatives.<br><br>
            <b>❤️ Heart Safe:</b> Avoid trans fats, processed meats, and fried foods.<br><br>
            </div>
            """, unsafe_allow_html=True
        )
    st.sidebar.markdown("---")

    st.markdown("""
    <div class='banner'>
        <div class='main-heading'>🌿 Smart Scanner</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='font-size: 16px; text-align: center; color: rgba(255,255,255,0.95); font-weight: 600; margin-bottom: 35px; letter-spacing: 0.3px;'>📸 Capture • 🔍 Analyze • ✅ Decide</p>", unsafe_allow_html=True)

    @st.cache_resource
    def initialize_ocr():
        """Initialize and cache PaddleOCR for optimal performance"""
        return PaddleOCR(
            lang=['en'], 
            use_gpu=False, 
            use_angle_cls=True
        )

    ocr = initialize_ocr()

    def perform_ocr(img):
        """Perform OCR with error handling"""
        try:
            if img is None or img.size == 0:
                return None
            result = ocr.ocr(img, cls=True)
            return result if result and len(result) > 0 else None
        except Exception as e:
            st.error(f"OCR Error: {str(e)}")
            return None

    def highlight_specific_words(image, boxes, texts, target_words, color=(255, 0, 0), thickness=2):
        for box, text in zip(boxes, texts):
            if any(word.lower() in text.lower() for word in target_words):
                pts = np.array([tuple(map(int, p)) for p in box])
                cv2.polylines(image, [pts], isClosed=True, color=color, thickness=thickness)
        return image

    def check_dietary_preferences(ingredients, preferences):
        bad_words = []
        for pref in preferences:
            if pref.lower().replace(" ", "_") in allergen_data:
                keywords = allergen_data[pref.lower().replace(" ", "_")]
                for kw in keywords:
                    if any(kw.lower() in i.lower() for i in ingredients):
                        bad_words.append(kw)
        return len(bad_words) == 0, list(set(bad_words))

    st.markdown("<p class='section-header'>Step 1️⃣ Select Your Preferences</p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #FFFFFF; margin-bottom: 15px; font-weight: 500;'>Choose all that apply to you</p>", unsafe_allow_html=True)

    cols = st.columns(4)
    preferences = []

    options = [
        'milk', 'egg', 'peanut', 'tree_nut', 'gluten', 'soy', 'fish', 'shellfish',
        'sesame', 'mustard', 'celery', 'sulphite', 'lactose_intolerant', 'gluten_intolerant',
        'fructose_intolerant', 'histamine_intolerant', 'sugar_intolerant', 'maida_intolerant',
        'vegan', 'vegetarian', 'keto', 'diabetic_friendly', 'low_sodium', 'heart_safe'
    ]

    # Dynamically distribute checkboxes across columns
    for i, opt in enumerate(options):
        with cols[i % 4]:
            if st.checkbox(opt.replace("_", " ").title()):
                preferences.append(opt)


    if preferences:
        st.markdown("---")
        st.markdown("<p class='section-header'>Step 2️⃣ Scan the Ingredient List</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #FFFFFF; margin-bottom: 15px; font-weight: 500;'>Take a clear photo of the ingredients</p>", unsafe_allow_html=True)
        
        camera_image = st.camera_input("📷 Capture ingredient list")

        if camera_image is not None:
            col_process, col_space = st.columns([1, 3])
            with col_process:
                if st.button("🔍 Analyze", use_container_width=True):
                    image = np.frombuffer(camera_image.read(), np.uint8)
                    img = cv2.imdecode(image, cv2.IMREAD_COLOR)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                    result = perform_ocr(img)
                    if not result or not result[0]:
                        st.error("❌ Please provide a clear image.")
                    else:
                        boxes = [res[0] for res in result[0]]
                        texts = [res[1][0] for res in result[0]]
                        is_ok, bad_words = check_dietary_preferences(texts, preferences)

                        highlighted = highlight_specific_words(img, boxes, texts, bad_words)
                        st.markdown("---")
                        st.markdown("<p class='section-header'>📊 Analysis Result</p>", unsafe_allow_html=True)
                        
                        col_img, col_result = st.columns([1.2, 1])
                        with col_img:
                            st.image(highlighted, caption="Highlighted Ingredients", use_column_width=True)
                        
                        with col_result:
                            if is_ok:
                                st.markdown("""
                                <div style='padding: 20px; background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(16, 163, 74, 0.15) 100%); 
                                border: 2px solid #22C55E; border-radius: 8px; text-align: center;'>
                                <p style='font-size: 24px; color: #86EFAC; font-weight: 700; margin: 0;'>✅ Safe to Consume!</p>
                                <p style='color: #FFFFFF; margin-top: 10px; font-weight: 500;'>This product matches your preferences</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style='padding: 20px; background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.15) 100%); 
                                border: 2px solid #EF4444; border-radius: 8px;'>
                                <p style='font-size: 20px; color: #FCA5A5; font-weight: 700; margin: 0; margin-bottom: 10px;'>⚠️ Not Suitable</p>
                                <p style='color: #FFFFFF; font-weight: 600; margin-bottom: 8px;'>Found ingredients:</p>
                                <p style='color: #FCA5A5; font-weight: 700; font-size: 16px; margin: 0;'>{', '.join(bad_words)}</p>
                                </div>
                                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='padding: 30px; background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.15) 100%); 
        border: 2px solid #F59E0B; border-radius: 8px; text-align: center;'>
        <p style='font-size: 18px; color: #FCD34D; font-weight: 700; margin: 0;'>👆 Select at least one preference above</p>
        <p style='color: #FFFFFF; margin-top: 8px; font-weight: 500;'>Choose your allergies or dietary needs to get started</p>
        </div>
        """, unsafe_allow_html=True)
# ✅ END OF FILE — DO NOT ADD app.run()
if __name__ == "__main__":
    st.warning("Please run this app using: streamlit run app.py")

