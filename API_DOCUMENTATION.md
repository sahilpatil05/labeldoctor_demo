# LabelDoctor Backend API Documentation

## Overview
The enhanced LabelDoctor backend now includes a complete REST API with database support, camera streaming, food insights visualization, and intelligent product recommendations.

---

## 🚀 NEW FEATURES

### 1. **Camera Streaming & Capture**
Real-time camera access for scanning food labels directly.

**Endpoints:**
- `GET /api/camera/stream` - Stream live video feed (motion JPEG)
- `POST /api/camera/capture` - Capture and process single frame

**Example:**
```bash
# Stream video
curl http://localhost:5000/api/camera/stream

# Capture frame
curl -X POST http://localhost:5000/api/camera/capture
```

---

### 2. **User Profile Management** 
Create and manage user profiles with personalized allergen lists.

**Endpoints:**
- `POST /api/user/create` - Create new user profile
- `GET /api/user/<user_id>` - Get user profile
- `PUT /api/user/<user_id>` - Update user profile

**Example:**
```bash
# Create user
curl -X POST http://localhost:5000/api/user/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "allergens": ["milk", "gluten"],
    "dietary_preferences": {"vegan": false, "vegetarian": true}
  }'

# Get user
curl http://localhost:5000/api/user/<user_id>

# Update user
curl -X PUT http://localhost:5000/api/user/<user_id> \
  -H "Content-Type: application/json" \
  -d '{"allergens": ["milk", "gluten", "peanut"]}'
```

---

### 3. **Food Label Insights & Visualization**
Detailed analysis and visualization of ingredient safety.

**Endpoints:**
- `GET /api/insights/<user_id>` - User scan history and statistics
- `GET /api/scan/<scan_id>/insights` - Detailed scan insights with visualization

**Response Example:**
```json
{
  "success": true,
  "total_scans": 5,
  "average_health_score": 78.5,
  "most_common_allergens": [
    {"allergen": "milk", "count": 3},
    {"allergen": "gluten", "count": 2}
  ],
  "scan_history": [
    {
      "id": "scan-123",
      "date": "2026-03-18T20:15:00",
      "health_score": 82.0,
      "ingredients_count": 12,
      "warnings_count": 2
    }
  ]
}
```

**Insights Data Structure:**
```json
{
  "insights": {
    "total_ingredients": 15,
    "safe_ingredients": 12,
    "risky_ingredients": 3,
    "safety_percentage": 80.0,
    "ingredient_breakdown": {
      "safe": 12,
      "warning": 3,
      "common_allergens": 1,
      "potential_allergens": 2
    },
    "visualization": {
      "ingredient_categories": {
        "safe": 12,
        "risky": 3
      },
      "allergen_severity_breakdown": {
        "high": 1,
        "medium": 1,
        "low": 1
      }
    }
  }
}
```

---

### 4. **Smart Product Recommendations**
Get personalized product recommendations based on allergens and dietary preferences.

**Endpoints:**
- `POST /api/products/recommend` - Get recommended products
- `GET /api/products` - List all products with filtering
- `GET /api/products/<product_id>` - Get product details

**Example:**
```bash
# Get recommendations
curl -X POST http://localhost:5000/api/products/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "allergens": ["milk", "gluten"],
    "category": "snack"
  }'

# List products (filter by allergen-free)
curl "http://localhost:5000/api/products?allergen_free=milk&category=snack"

# Get product details
curl http://localhost:5000/api/products/<product_id>
```

**Product Response:**
```json
{
  "recommendations": [
    {
      "id": "prod-123",
      "name": "Almond Joy Alternative Bar",
      "brand": "Peaceful Organics",
      "category": "Snack",
      "rating": 4.8,
      "health_score": 8.5,
      "is_organic": true,
      "price": 2.99,
      "allergen_free": ["milk", "gluten", "egg"]
    }
  ]
}
```

---

## 📊 DATABASE SCHEMA

### User Model
```python
{
  "id": "uuid",
  "name": "string",
  "email": "string (unique)",
  "allergens": ["list of allergen IDs"],
  "dietary_preferences": {
    "vegan": "boolean",
    "vegetarian": "boolean",
    "glutenfree": "boolean",
    "dairyfree": "boolean"
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Scan Model
```python
{
  "id": "uuid",
  "user_id": "uuid (foreign key)",
  "extracted_text": "string",
  "ingredients": ["list"],
  "warnings": ["list of warning objects"],
  "health_score": "float (0-100)",
  "created_at": "timestamp"
}
```

### Product Model
```python
{
  "id": "uuid",
  "name": "string",
  "brand": "string",
  "category": "string",
  "allergen_free": ["list"],
  "ingredients_list": "json",
  "rating": "float (0-5)",
  "health_score": "float (0-10)",
  "price": "float",
  "is_organic": "boolean",
  "created_at": "timestamp"
}
```

---

## 🔄 COMPLETE WORKFLOW EXAMPLE

### Step 1: Create User Profile
```bash
curl -X POST http://localhost:5000/api/user/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah",
    "email": "sarah@example.com",
    "allergens": ["milk", "eggs"],
    "dietary_preferences": {"vegan": false, "vegetarian": true}
  }'
# Returns: {"user_id": "abc123xyz"}
```

### Step 2: Scan Food Label
```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
# Returns: {"extracted_text": "milk, sugar, vanilla, ...")
```

### Step 3: Analyze Ingredients
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["milk", "sugar", "vanilla"],
    "userAllergens": ["milk", "eggs"],
    "userId": "abc123xyz"
  }'
# Returns analysis with health score and warnings
```

### Step 4: Get Insights
```bash
curl http://localhost:5000/api/insights/abc123xyz
# Returns scan history and statistics
```

### Step 5: Get Recommendations
```bash
curl -X POST http://localhost:5000/api/products/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "allergens": ["milk", "eggs"],
    "category": "snack"
  }'
# Returns list of safe products
```

---

## 🛠️ TECHNICAL DETAILS

### Database
- **Type:** SQLite
- **Location:** `./labeldoctor.db`
- **ORM:** SQLAlchemy 3.0.5

### Dependencies (New)
```
Flask-SQLAlchemy==3.0.5
```

### Camera Integration
- **Library:** OpenCV (cv2)
- **Format:** Motion JPEG streaming
- **Frame Size:** 640x480 (resized for performance)
- **Processing:** Gaussian blur applied for clarity

### OCR Pipeline
- **Engine:** PaddleOCR
- **Language:** English
- **Support:** Text extraction with line-by-line confidence

---

## 📋 ALL AVAILABLE ENDPOINTS

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Serve homepage |
| GET | `/api/health` | Health check |
| **CAMERA** | | |
| GET | `/api/camera/stream` | Live video stream |
| POST | `/api/camera/capture` | Capture frame |
| **SCANNING** | | |
| POST | `/api/scan` | Upload image scan |
| POST | `/api/analyze` | Analyze ingredients |
| **USER** | | |
| POST | `/api/user/create` | Create user |
| GET | `/api/user/<id>` | Get user profile |
| PUT | `/api/user/<id>` | Update user |
| **ALLERGENS** | | |
| GET | `/api/allergens` | List allergens |
| GET | `/api/alternatives/<allergen>` | Get alternatives |
| **INSIGHTS** | | |
| GET | `/api/insights/<user_id>` | User statistics |
| GET | `/api/scan/<scan_id>/insights` | Scan details |
| **PRODUCTS** | | |
| POST | `/api/products/recommend` | Get recommendations |
| GET | `/api/products` | List products |
| GET | `/api/products/<id>` | Product details |

---

## ✅ TESTING

Run the comprehensive test suite:
```bash
python test_api.py
```

This validates:
- ✅ All imports and dependencies
- ✅ Database models and operations
- ✅ Helper functions
- ✅ All API routes registered
- ✅ Data persistence

---

## 🚀 STARTING THE SERVER

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run server
python app_api.py
```

Server runs on: `http://localhost:5000`

---

## 📝 NOTES

- All IDs are UUIDs for security
- Timestamps are UTC
- Health score ranges 0-100
- Product ratings range 0-5.0
- All POST endpoints require `Content-Type: application/json`
- Database is auto-created on first run
- Camera requires device with webcam support

---

## 🔐 FUTURE ENHANCEMENTS

- [ ] JWT authentication
- [ ] Product barcode scanning
- [ ] Nutritional data integration
- [ ] Mobile app support
- [ ] AWS/Cloud database migration
- [ ] Advanced ML-based recommendations
- [ ] Multi-language OCR support
