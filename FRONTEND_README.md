# LabelDoctor - Ingredient Scanner Frontend

A modern, responsive web frontend for the LabelDoctor ingredient scanner application. This frontend allows users to scan food labels, detect allergens, and get personalized recommendations for safer alternatives.

---

## 📋 Features

### Core Features
- **📸 Image Scanning** - Upload food labels and extract ingredients using OCR
- **⚠️ Allergen Detection** - Identify dangerous allergens in products
- **💚 Safe Ingredient Display** - See which ingredients are safe for you
- **💡 Smart Alternatives** - Get healthy product alternatives
- **👤 Personal Profile** - Set up your allergens and dietary preferences
- **📊 Health Score** - Get a quick health assessment of the product
- **📈 Visual Analytics** - See ingredient breakdown and risk assessment

### User Interface
- Modern, responsive design (works on desktop, tablet, mobile)
- Smooth animations and transitions
- Intuitive drag-and-drop upload
- Real-time ingredient analysis
- Toast notifications for feedback
- Dark/Light theme support

### Data Management
- Local storage of user preferences
- Download scan results as JSON
- Persistent user profile settings
- Keyboard shortcuts (Ctrl+S to save, Esc to close)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- Flask 2.3.2+
- Flask-CORS 4.0.0+
- PaddleOCR and dependencies

### Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask API Server**
   ```bash
   python app_api.py
   ```
   The server will start at `http://localhost:5000`

3. **Access the Frontend**
   Open your browser and go to:
   ```
   http://localhost:5000/
   ```

---

## 📁 Project Structure

```
ingredient-scanner-main/
├── app.py                          # Original Streamlit app (legacy)
├── app_api.py                      # New Flask API server
├── requirements.txt                # Python dependencies
├── README.md                       # Main documentation
│
├── templates/
│   └── index.html                 # Main HTML frontend
│
├── static/
│   ├── style.css                  # Complete styling
│   └── script.js                  # Frontend logic
│
├── allergens.json                 # Allergen database
├── alternatives.json              # Alternative products database
│
└── Dockerfile                     # Docker configuration
```

---

## 🛠️ Technology Stack

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with Flexbox/Grid
- **JavaScript (ES6+)** - Interactive functionality
- **Font Awesome 6** - Icon library

### Backend
- **Flask 2.3** - Lightweight web framework
- **Flask-CORS** - Cross-origin resource sharing
- **PaddleOCR** - Optical character recognition
- **OpenCV** - Image processing
- **NumPy** - Numerical computing
- **Pillow** - Image handling

---

## 📖 Usage Guide

### Scanning Food Labels

1. **Upload an Image**
   - Click on the upload area or drag & drop a food label image
   - Supported formats: JPG, PNG, WebP, GIF

2. **Extract Ingredients**
   - Click the "Scan" button to process the image
   - The system extracts ingredients using OCR

3. **Analyze Results**
   - View extracted ingredients
   - See allergen warnings with severity levels
   - Check your health score
   - Review safe ingredients
   - Get alternative product recommendations

### Manual Entry

If OCR doesn't work perfectly:
1. Edit extracted ingredients or manually type them
2. Separate ingredients with commas or line breaks
3. Click "Analyze" to process

### Manage Your Profile

1. Click the "Profile" button in the top right
2. Select your allergens from the list
3. Choose your dietary preferences (Vegan, Vegetarian, etc.)
4. Click "Save Changes"

Your profile is saved locally in your browser.

---

## 🔌 API Endpoints

### Health Check
```
GET /api/health
```

### Scan Image for Ingredients
```
POST /api/scan
Content-Type: application/json

{
    "image": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
    "success": true,
    "extracted_text": "Wheat\nSugar\nEggs\n...",
    "confidence": 0.85
}
```

### Analyze Ingredients
```
POST /api/analyze
Content-Type: application/json

{
    "ingredients": ["wheat", "sugar", "eggs"],
    "userAllergens": ["peanuts"]
}
```

**Response:**
```json
{
    "success": true,
    "warnings": [...],
    "safe_ingredients": [...],
    "health_score": 75,
    "alternatives": [...],
    "total_ingredients": 3
}
```

### Get All Allergens
```
GET /api/allergens
```

### Get Alternatives for Allergen
```
GET /api/alternatives/<allergen_name>
```

---

## 🎨 Customization

### Colors
Edit the CSS variables in `static/style.css`:
```css
:root {
    --primary-color: #10B981;
    --secondary-color: #F59E0B;
    --accent-color: #3B82F6;
    --danger-color: #EF4444;
    /* ... more colors ... */
}
```

### Branding
- Update the app title in `templates/index.html`
- Replace the logo/icon in the navbar
- Customize the banner images and colors

### Database
- Modify `allergens.json` to add/remove allergens
- Update `alternatives.json` with new product alternatives

---

## 📱 Responsive Design

The frontend is fully responsive and tested on:
- Desktop (1920x1080 and larger)
- Tablet (768px to 1024px)
- Mobile (320px to 768px)

All features work seamlessly across devices.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + S` | Save scan results |
| `Esc` | Close profile modal |
| `Click nav links` | Jump to sections |

---

## 🔒 Privacy & Security

- User data (profile, preferences) is stored locally in browser storage
- No data is sent to external servers except for OCR processing
- Images are processed locally and not stored permanently
- Scan results can be downloaded as JSON for personal records

---

## 🐛 Troubleshooting

### Image Upload Not Working
- Check browser console for errors (F12)
- Ensure image file size is under 10MB
- Try a different image format (JPG instead of PNG)

### API Connection Failed
- Make sure Flask server is running on port 5000
- Check CORS configuration if using different domain
- Review Flask error logs

### Poor OCR Results
- Use high-quality, well-lit images
- Ensure label text is clear and readable
- Try cropping to show only the ingredient list
- Manually edit unrecognized ingredients

### Profile Not Saving
- Check if browser allows localStorage
- Clear browser cache and try again
- Disable privacy mode/incognito

---

## 🚀 Deployment

### Docker
```bash
docker build -t scan-shop .
docker run -p 5000:5000 scan-shop
```

### Heroku
```bash
heroku create your-app-name
git push heroku main
```

### Vercel
Configure `vercel.json` (already included) and deploy using Vercel CLI.

---

## 📊 Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

---

## 🤝 Contributing

To improve the frontend:
1. Create a new branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

---

## 📄 License

This project is part of the Label-Doctor/Ingredient-Scanner initiative.

---

## 📞 Support

For issues, questions, or feature requests, please create an issue in the repository.

---

## 🎯 Future Enhancements

- [ ] Barcode scanning support
- [ ] Multi-language OCR
- [ ] Product database integration
- [ ] User accounts and cloud sync
- [ ] Nutritional information display
- [ ] Speech recognition for ingredients
- [ ] AR label overlay
- [ ] Community reviews and ratings

---

**Made with ❤️ for your health**
