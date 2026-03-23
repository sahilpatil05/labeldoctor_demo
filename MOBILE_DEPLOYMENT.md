# 📱 Mobile Deployment Guide - Ingredient Scanner with Hugging Face

## Quick Start

### 1. Get Hugging Face API Token
```bash
# Go to: https://huggingface.co/settings/tokens
# Create a new token with "read" access
# Copy the token
```

### 2. Set Environment Variable (Local Testing)

**Windows (PowerShell):**
```powershell
$env:HF_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
python app_api.py
```

**Windows (Command Prompt):**
```cmd
set HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
python app_api.py
```

**Mac/Linux:**
```bash
export HF_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
python app_api.py
```

### 3. Install Updated Dependencies
```bash
pip install -r requirements.txt
python app_api.py
```

---

## 🌐 Deployment Options

### Option A: Hugging Face Spaces ⭐ (EASIEST FOR MOBILE)

Free hosting + free API usage!

**Steps:**
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose "Docker" runtime
4. Upload your code
5. Add HF_API_TOKEN as secret
6. Your app gets: `https://<username>-<space-name>.hf.space`

**Pros:**
- ✅ Free
- ✅ Auto-HTTPS (required for camera access on mobile)
- ✅ Auto-HTTPS (required for camera access on mobile)
- ✅ Already integrated with Hugging Face models
- ✅ Responsive design works great on mobile

---

### Option B: Railway.app

**Steps:**
1. Go to https://railway.app
2. Connect GitHub repo
3. Add `HF_API_TOKEN` environment variable
4. Deploy
5. Get public URL

**Cost:** Free tier available (limited usage)

---

### Option C: Heroku (Paid Alternative)

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variable
heroku config:set HF_API_TOKEN=hf_xxxx

# Deploy
git push heroku main
```

---

## 📱 Mobile Optimization

Your app is already responsive! For mobile:

### 1. Add Mobile Meta Tags (Already in index.html)
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
```

### 2. Mobile Features to Enable
- Camera access (already implemented)
- Touch-friendly buttons (already styled)
- Fast load times (Hugging Face models are fast)

### 3. Test on Mobile
1. Deploy to Railway/Heroku/Spaces
2. Open `https://your-domain.com` on phone
3. Allow camera access when prompted
4. Use normally!

---

## 🚀 Production Deployment Checklist

- [ ] Create `.env` file with `HF_API_TOKEN`
- [ ] Add `.env` to `.gitignore` (never commit secrets!)
- [ ] Update `requirements.txt` with new dependencies
- [ ] Test locally with Hugging Face models
- [ ] Deploy to Hugging Face Spaces or Railway
- [ ] Test on actual mobile device
- [ ] Monitor API usage on Hugging Face
- [ ] Set up error logging

---

## 💰 Cost Analysis

| Component | Cost |
|-----------|------|
| Hugging Face API (50k requests/month free) | FREE |
| Hugging Face Spaces hosting | FREE |
| Railway basic tier | FREE (limited) |
| Heroku | $5-50/month |
| **Total for free deployment** | **FREE** |

---

## 🔧 Troubleshooting

### "HF_API_TOKEN not found"
```bash
# Make sure env variable is set
echo $HF_API_TOKEN  # Mac/Linux
echo %HF_API_TOKEN% # Windows
```

### "Cannot read from Spaces"
- Check your token has "read" access
- Token should start with `hf_`
- Not expired

### App slow on mobile
- Hugging Face API has ~2-3s latency
- Show loading spinner while processing
- Consider caching results

### Camera not working
- Must use HTTPS (Spaces/Railway provide this)
- Allow camera permissions in browser
- Works best on Chrome mobile

---

## 📲 Share Your App

After deployment, you can share:
```
https://your-space.hf.space
```

Users can:
1. Open on any device (desktop, tablet, phone)
2. No installation needed
3. Scan labels in real-time
4. Get allergen warnings instantly

---

## 🆘 Support

- Hugging Face docs: https://huggingface.co/docs
- Railway docs: https://docs.railway.app
- HF Spaces: https://huggingface.co/docs/hub/spaces

---

## Next Steps

1. **Set HF_API_TOKEN environment variable**
2. **Test locally:** `python app_api.py`
3. **Deploy to Hugging Face Spaces** (recommended)
4. **Test on mobile device**
5. **Share URL with others!**

Your app is now ready for mobile! 🎉
