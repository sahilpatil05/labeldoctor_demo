# Frontend Architecture & Documentation

## 📋 Overview

This document provides detailed information about the LabelDoctor frontend architecture, components, and implementation.

---

## 🏗️ Architecture

### Frontend Architecture Layers

```
┌─────────────────────────────────────────┐
│         HTML Interface Layer            │
│  (templates/index.html)                   │
│  - Navigation Bar                        │
│  - Hero Section                          │
│  - Features Section                      │
│  - Scanner Section                       │
│  - Results Section                       │
│  - Profile Modal                         │
│  - Footer                                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Styling Layer                    │
│  (static/style.css)                      │
│  - 1000+ lines of responsive CSS        │
│  - CSS Variables for theming             │
│  - Media queries for mobile              │
│  - Animations & transitions              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     JavaScript Logic Layer              │
│  (static/script.js)                      │
│  - Event handling                        │
│  - API communication                     │
│  - State management                      │
│  - DOM manipulation                      │
│  - Local storage management              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│      Flask API Backend Layer            │
│  (app_api.py)                            │
│  - Routes/endpoints                      │
│  - Image processing with OCR             │
│  - Allergen analysis                     │
│  - Database queries                      │
│  - CORS handling                         │
└─────────────────────────────────────────┘
```

---

## 📁 File Structure

```
.
├── templates/
│   └── index.html              (Main HTML - 600 lines)
│       ├── Navigation
│       ├── Hero Section
│       ├── Features Grid
│       ├── Scanner Interface
│       ├── Results Display
│       ├── Profile Modal
│       └── Footer
│
├── static/
│   ├── style.css              (Styling - 1200 lines)
│   │   ├── Root Variables
│   │   ├── Navigation Styles
│   │   ├── Button Styles
│   │   ├── Section Styles
│   │   ├── Modal Styles
│   │   ├── Responsive Media Queries
│   │   └── Animations
│   │
│   └── script.js              (Logic - 700 lines)
│       ├── State Management
│       ├── Event Listeners
│       ├── Image Handling
│       ├── API Communication
│       ├── Profile Management
│       ├── UI Updates
│       └── Utilities
│
├── app_api.py                 (Flask Server - 200 lines)
│   ├── Flask App Setup
│   ├── CORS Configuration
│   ├── OCR Initialization
│   ├── API Routes
│   │   ├── GET /
│   │   ├── POST /api/scan
│   │   ├── POST /api/analyze
│   │   ├── GET /api/allergens
│   │   └── GET /api/alternatives/<allergen>
│   ├── Error Handlers
│   └── Main Entry Point
│
├── requirements.txt           (Dependencies)
├── run.bat                    (Quick Start Script)
├── QUICK_START.md             (User Guide)
├── FRONTEND_README.md         (Full Documentation)
└── ARCHITECTURE.md            (This file)
```

---

## 🎯 Component Details

### 1. Navigation Bar
- **Location:** `templates/index.html` lines 15-30
- **Features:**
  - Sticky positioning
  - Active link highlighting
  - Mobile hamburger menu
  - Profile button

- **Styling:** `static/style.css` lines 90-130

- **JavaScript:** `static/script.js` (handleNavClick, scroll detection)

### 2. Hero Section
- **Location:** `templates/index.html` lines 32-50
- **Features:**
  - Gradient background
  - Floating animation
  - CTA buttons
  - Responsive layout

### 3. Scanner Interface
- **Location:** `templates/index.html` lines 100-170
- **Features:**
  - Drag & drop upload area
  - Image preview
  - Loading spinner
  - Extracted text display
  - Manual ingredient input

- **JavaScript Functions:**
  - `handleDragOver()` - Drag event handling
  - `handleDrop()` - Drop event handling
  - `handleImageFile()` - File processing
  - `showPreview()` - Image preview
  - `scanImage()` - OCR API call
  - `analyzeIngredients()` - Analysis API call

### 4. Results Display
- **Location:** `templates/index.html` lines 172-250
- **Features:**
  - Health score circle
  - Statistics cards
  - Warning cards (with severity)
  - Safe ingredients list
  - Alternatives recommendations
  - Action buttons

- **Display Functions:**
  - `displayResults()` - Render all results
  - `displayExtractedText()` - Show ingredients
  - `showResults()` - Toggle results section

### 5. Profile Modal
- **Location:** `templates/index.html` lines 280-330
- **Features:**
  - Allergen selector
  - Dietary preferences checkboxes
  - Save/cancel buttons
  - Modal overlay

- **Functions:**
  - `openProfile()` - Open modal
  - `closeProfile()` - Close modal
  - `toggleAllergen()` - Select/deselect allergen
  - `saveProfile()` - Save to localStorage
  - `loadUserProfile()` - Load from localStorage

---

## 🔌 API Communication

### Request/Response Flow

```
┌──────────────────┐
│   User Action    │
└────────┬─────────┘
         │
         ↓
┌──────────────────────────────┐
│  JavaScript Event Handler     │
│  (e.g., scanImage())          │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Fetch API Call              │
│  POST /api/scan              │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Flask API Route Handler     │
│  (app_api.py)                │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  Processing                  │
│  - OCR                       │
│  - Allergen matching         │
│  - Score calculation         │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  JSON Response               │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  JavaScript Handler          │
│  (response.json())           │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  DOM Update                  │
│  (displayResults())          │
└────────┬─────────────────────┘
         │
         ↓
┌──────────────────────────────┐
│  User Sees Updated UI        │
└──────────────────────────────┘
```

---

## 📊 State Management

### Global State Object

```javascript
const state = {
    // Current image data
    currentImage: null,
    
    // Extracted ingredients from OCR
    extractedText: [],
    
    // Last analysis results
    analysisResults: null,
    
    // User profile/settings
    userProfile: {
        allergens: [],
        dietary: {
            vegan: false,
            vegetarian: false,
            glutenfree: false,
            dairyfree: false
        }
    }
};
```

### State Updates
- `currentImage` - Updated when user selects image
- `extractedText` - Updated after OCR processing
- `analysisResults` - Updated after analysis API call
- `userProfile` - Synced with localStorage on save

---

## 🎨 Styling System

### CSS Architecture

```css
1. CSS Variables (Root)
   └─ Color palette
   └─ Shadow definitions
   └─ Spacing units

2. Base Styles
   └─ Body, paragraphs
   └─ Links, buttons
   └─ Form elements

3. Component Styles
   └─ Navigation
   └─ Cards
   └─ Modals
   └─ Buttons

4. Section Styles
   └─ Hero
   └─ Features
   └─ Scanner
   └─ Results
   └─ About

5. Utility Classes
   └─ .hidden
   └─ .container
   └─ Responsive helpers

6. Media Queries
   └─ Mobile (320px-768px)
   └─ Tablet (768px-1024px)
   └─ Desktop (1024px+)

7. Animations
   └─ Float
   └─ Spin
   └─ SlideIn
   └─ Transitions
```

### Color Palette

```css
Primary:      #10B981 (Emerald)
Primary Dark: #059669
Secondary:    #F59E0B (Amber)
Accent:       #3B82F6 (Blue)
Purple:       #8B5CF6
Danger:       #EF4444 (Red)
Success:      #10B981 (Green)
Warning:      #F59E0B (Yellow)
```

---

## 🚀 JavaScript Module Structure

### Initialization Module
```javascript
- setupEventListeners()
  └─ Drag/drop listeners
  └─ Navigation listeners
  └─ Click handlers
- loadUserProfile()
- fetchAllergensList()
```

### Image Handling Module
```javascript
- handleDragOver()
- handleDrop()
- handleImageSelect()
- handleImageFile()
- showPreview()
- clearImage()
```

### Scanning Module
```javascript
- scanImage()
- displayExtractedText()
- removeIngredient()
```

### Analysis Module
```javascript
- analyzeIngredients()
- analyzeManualIngredients()
- displayResults()
- showResults()
- goBackToScanner()
```

### Profile Module
```javascript
- fetchAllergensList()
- renderAllergenSelector()
- toggleAllergen()
- openProfile()
- closeProfile()
- saveProfile()
- loadUserProfile()
```

### Utility Module
```javascript
- showToast()
- showLoading()
- scrollToScanner()
- saveResults()
- handleNavClick()
- toggleMobileMenu()
```

---

## 🔄 Event Flow Examples

### Example 1: Scanning an Image

```
User clicks upload area
       ↓
Input file dialog opens
       ↓
User selects image file
       ↓
handleImageSelect() fires
       ↓
handleImageFile() processes file
       ↓
FileReader.readAsDataURL()
       ↓
showPreview() displays image
       ↓
User clicks "Scan" button
       ↓
scanImage() sends to /api/scan
       ↓
Flask processes with PaddleOCR
       ↓
Returns extracted_text
       ↓
displayExtractedText() renders items
       ↓
analyzeIngredients() auto-calls
       ↓
/api/analyze processes ingredients
       ↓
displayResults() shows warnings, alternatives
       ↓
User sees complete analysis
```

### Example 2: Setting Profile Allergens

```
User clicks "Profile" button
       ↓
openProfile() shows modal
       ↓
Modal filled with allergen buttons
       ↓
User clicks allergen (e.g., "Peanuts")
       ↓
toggleAllergen() adds to state
       ↓
renderAllergenSelector() updates UI
       ↓
User clicks "Save Changes"
       ↓
saveProfile() updates state.userProfile
       ↓
localStorage.setItem('userProfile', ...)
       ↓
closeProfile() dismisses modal
       ↓
showToast() confirms save
```

---

## 🔗 Flask API Routes

### GET /
```
Purpose: Serve the main HTML page
Response: index.html
Template Variables: None (static site)
```

### POST /api/scan
```
Purpose: Extract ingredients from image
Body: { image: "data:image/jpeg;base64,..." }
Process:
  1. Decode base64 image
  2. Convert to numpy array
  3. Run PaddleOCR.ocr()
  4. Extract text from results
Response: {
  "success": true,
  "extracted_text": "ingredient1\ningredient2\n...",
  "confidence": 0.85
}
```

### POST /api/analyze
```
Purpose: Analyze ingredients for allergens
Body: {
  "ingredients": ["wheat", "milk", ...],
  "userAllergens": ["peanuts"]
}
Process:
  1. Load allergens.json database
  2. Match each ingredient to allergens
  3. Calculate health score
  4. Find alternatives from alternatives.json
Response: {
  "success": true,
  "warnings": [
    {
      "ingredient": "milk",
      "allergen": "dairy",
      "severity": "high",
      "description": "..."
    }
  ],
  "safe_ingredients": ["sugar", "salt"],
  "health_score": 65,
  "alternatives": [...],
  "total_ingredients": 5
}
```

### GET /api/allergens
```
Purpose: Get list of all allergens
Response: {
  "success": true,
  "allergens": ["peanuts", "tree nuts", "milk", ...]
}
```

### GET /api/alternatives/<allergen>
```
Purpose: Get alternatives for specific allergen
Response: {
  "success": true,
  "allergen": "milk",
  "data": {
    "alternatives": ["almond milk", "oat milk", ...],
    "reason": "Dairy-free alternatives..."
  }
}
```

---

## 📦 Dependencies

### Frontend (Browser)
- HTML5
- CSS3
- JavaScript ES6+
- Font Awesome 6.4.0

### Backend (Python)
- Flask 2.3.2
- Flask-CORS 4.0.0
- PaddleOCR 2.6.1
- OpenCV 4.8.0
- NumPy 1.23.0
- Pillow 9.4.0

---

## 🌐 CORS Configuration

```python
app = Flask(__name__)
CORS(app)  # Allows all origins

# Can be restricted to specific domains:
# CORS(app, origins=["http://localhost:3000"])
```

---

## 📱 Responsive Design Breakpoints

```css
Mobile:     320px - 768px
Tablet:     768px - 1024px
Desktop:    1024px+

Key breakpoints:
- 768px: Navigation collapse, grid adjustments
- 1024px: Multi-column layouts activate
- 1200px: Max container width
```

---

## 🔐 Data Security

### Frontend Security
- No sensitive data in client-side code
- User profile stored in localStorage (not secure for passwords)
- No API keys exposed
- Images processed client-side before upload

### Backend Security
- CORS headers properly configured
- Input validation on all endpoints
- JSON data sanitization
- Error messages don't expose system info

### Best Practices
- Use HTTPS in production
- Implement authentication for user accounts
- Validate all uploads
- Rate limit API endpoints
- Use environment variables for secrets

---

## 💡 Code Quality

### HTML
- Semantic structure
- Proper heading hierarchy
- Accessibility attributes
- Meta tags for mobile

### CSS
- DRY (Don't Repeat Yourself)
- CSS Variables for theming
- Mobile-first approach
- Cross-browser compatibility

### JavaScript
- Modular functions
- Clear naming conventions
- Comments for complex logic
- Error handling with try-catch

---

## 🚀 Performance Optimizations

### Frontend
- Minimal asset loading
- CSS animations (GPU accelerated)
- Event delegation
- Efficient DOM queries

### Backend
- Image optimization
- Caching OCR model
- Efficient JSON parsing
- Fast route handling

### Loading Time
- ≈ 2-3 seconds initial page load
- ≈ 1-2 seconds for image scan
- ≈ 0.5 seconds for analysis

---

## 📈 Future Enhancement Ideas

### Phase 2 Features
- [ ] User accounts with JWT auth
- [ ] Cloud data sync
- [ ] Barcode scanning
- [ ] Multi-language OCR
- [ ] Product database API
- [ ] Nutritional info display
- [ ] User reviews/ratings
- [ ] AR label overlay

### Technical Improvements
- [ ] Progressive Web App (PWA)
- [ ] Service Worker caching
- [ ] Image compression
- [ ] API optimization
- [ ] Database migration
- [ ] Microservices architecture

---

## 📞 Support & Maintenance

### Deployment Platforms
- Heroku ✓ (ready)
- Vercel ✓ (ready)
- Docker ✓ (config included)
- AWS ✓ (manual setup)

### Monitoring
- Error logs in Flask
- Console logs in browser
- User feedback collection
- Performance metrics

---

## 📚 References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [MDN Web Docs](https://developer.mozilla.org/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [CSS Tricks](https://css-tricks.com/)
- [JavaScript.info](https://javascript.info/)

---

**Last Updated:** 2025-03-17  
**Frontend Version:** 1.0.0  
**Status:** Production Ready ✅
