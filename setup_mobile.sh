#!/bin/bash
# Quick setup script for mobile deployment

echo "================================"
echo "Ingredient Scanner - Mobile Setup"
echo "================================"
echo ""

# Check if HF_API_TOKEN is set
if [ -z "$HF_API_TOKEN" ]; then
    echo "⚠️  HF_API_TOKEN not found!"
    echo ""
    echo "Steps to get your token:"
    echo "1. Go to: https://huggingface.co/settings/tokens"
    echo "2. Create a new token with 'read' access"
    echo "3. Copy the token"
    echo ""
    echo "Then set it:"
    echo ""
    echo "On Mac/Linux:"
    echo '  export HF_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"'
    echo ""
    echo "On Windows (PowerShell):"
    echo '  $env:HF_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"'
    echo ""
    echo "On Windows (Command Prompt):"
    echo '  set HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx'
    echo ""
    exit 1
fi

echo "✓ HF_API_TOKEN is set"
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Install requirements
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Test locally: python app_api.py"
echo "2. Deploy to Hugging Face Spaces"
echo "3. Open on mobile: https://your-space.hf.space"
echo ""
echo "For detailed instructions, see: MOBILE_DEPLOYMENT.md"
