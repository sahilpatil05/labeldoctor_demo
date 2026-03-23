const API_BASE_URL = 'http://localhost:5000/api';

// ============ STATE MANAGEMENT ============
const state = {
    currentImage: null,
    extractedText: [],
    analysisResults: null,
    userId: null,
    userName: null,
    userEmail: null,
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

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
});

// ============ AUTHENTICATION ============
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/current-user`);
        const data = await response.json();
        
        if (data.success) {
            // User is logged in
            state.userId = data.user_id;
            state.userName = data.name;
            state.userEmail = data.email;
            state.userProfile.allergens = data.allergens;
            state.userProfile.dietary = data.dietary_preferences;
            showMainApp();
        } else {
            // User is not logged in
            showAuthForms();
        }
    } catch (error) {
        showAuthForms();
    }
}

function showAuthForms() {
    document.getElementById('authContainer').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

function showMainApp() {
    document.getElementById('authContainer').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
    setupEventListeners();
    fetchAllergensList();
}

function toggleAuth() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm.classList.contains('hidden-form')) {
        loginForm.classList.remove('hidden-form');
        registerForm.classList.add('hidden-form');
    } else {
        loginForm.classList.add('hidden-form');
        registerForm.classList.remove('hidden-form');
    }
    
    // Clear error messages
    document.querySelectorAll('.error-message').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });
}

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showErrorMessage('loginError', 'Please enter email and password');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.userId = data.user_id;
            state.userName = data.name;
            state.userEmail = data.email;
            state.userProfile.allergens = data.allergens;
            showMainApp();
            document.getElementById('loginForm').reset();
        } else {
            showErrorMessage('loginError', data.error || 'Login failed');
        }
    } catch (error) {
        showErrorMessage('loginError', error.message);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    
    // Validation
    if (!name || !email || !password) {
        showErrorMessage('registerError', 'Please fill all fields');
        return;
    }
    
    if (password.length < 6) {
        showErrorMessage('registerError', 'Password must be at least 6 characters');
        return;
    }
    
    if (password !== confirmPassword) {
        showErrorMessage('registerError', 'Passwords do not match');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            state.userId = data.user_id;
            state.userName = data.name;
            showMainApp();
            document.getElementById('registerForm').reset();
        } else {
            showErrorMessage('registerError', data.error || 'Registration failed');
        }
    } catch (error) {
        showErrorMessage('registerError', error.message);
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST'
        });
        state.userId = null;
        state.userName = null;
        checkAuthStatus();
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

function showErrorMessage(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
    }
}

// ============ EVENT LISTENERS ============
function setupEventListeners() {
    // Drag and Drop
    const dragDropZone = document.getElementById('dragDropZone');
    dragDropZone.addEventListener('click', () => document.getElementById('imageInput').click());
    dragDropZone.addEventListener('dragover', handleDragOver);
    dragDropZone.addEventListener('drop', handleDrop);

    document.getElementById('imageInput').addEventListener('change', handleImageSelect);

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavClick);
    });

    // Hamburger menu
    const hamburger = document.querySelector('.hamburger');
    if (hamburger) {
        hamburger.addEventListener('click', toggleMobileMenu);
    }

    // Load food categories dropdown
    loadFoodCategories();
}

// ============ FOOD CATEGORIES ============
async function loadFoodCategories() {
    try {
        const response = await fetch(`${API_BASE_URL}/food-categories`);
        const data = await response.json();

        if (data.success && data.categories) {
            const dropdown = document.getElementById('foodCategory');
            if (dropdown) {
                // Clear all options except the default one
                while (dropdown.options.length > 1) {
                    dropdown.remove(1);
                }
                
                // Add category options
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category.charAt(0).toUpperCase() + category.slice(1).replace('-', ' ');
                    dropdown.appendChild(option);
                });

                console.log('Food categories loaded:', data.categories);
            }
        }
    } catch (error) {
        console.error('Failed to load food categories:', error);
    }
}

// ============ IMAGE HANDLING ============
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    document.getElementById('dragDropZone').style.borderColor = '#10B981';
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleImageFile(files[0]);
    }
}

function handleImageSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleImageFile(files[0]);
    }
}

function handleImageFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please select a valid image file', 'error');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        state.currentImage = e.target.result;
        showPreview(e.target.result);
    };
    reader.readAsDataURL(file);
}

function showPreview(imageSrc) {
    document.getElementById('dragDropZone').classList.add('hidden');
    const previewContainer = document.getElementById('previewContainer');
    previewContainer.classList.remove('hidden');
    document.getElementById('previewImage').src = imageSrc;
    document.getElementById('extractedText').innerHTML = '<p class="placeholder">Image will be scanned...</p>';
}

function clearImage() {
    state.currentImage = null;
    document.getElementById('previewContainer').classList.add('hidden');
    document.getElementById('dragDropZone').classList.remove('hidden');
    document.getElementById('imageInput').value = '';
    document.getElementById('extractedText').innerHTML = '<p class="placeholder">Image will appear here after scanning</p>';
}

// ============ SCANNER TABS & CAMERA ============
let cameraStream = null;
let cameraActive = false;

function switchScannerTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const tabElement = document.getElementById(tabName + 'Tab');
    if (tabElement) {
        tabElement.classList.add('active');
    }

    // Set active button - find button by data attribute or by text content
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        if (tabName === 'upload' && btn.textContent.includes('Upload')) {
            btn.classList.add('active');
        } else if (tabName === 'camera' && btn.textContent.includes('Camera')) {
            btn.classList.add('active');
        }
    });

    // Stop camera if switching away from camera tab
    if (tabName !== 'camera' && cameraActive) {
        stopCamera();
    }

    console.log('Switched to tab:', tabName);
}

async function startCamera() {
    try {
        console.log('=== CAMERA START INITIATED ===');
        console.log('Browser:', navigator.userAgent);
        
        // Step 1: Check browser support
        if (!navigator.mediaDevices) {
            throw new Error('mediaDevices not supported - ensure you are using HTTPS or localhost');
        }
        
        // Check for different browser-specific implementations
        const getUserMedia = navigator.mediaDevices.getUserMedia 
            || navigator.webkitGetUserMedia 
            || navigator.mozGetUserMedia;
        
        if (!getUserMedia) {
            throw new Error('getUserMedia not supported in your browser. Try Chrome, Firefox, Safari 14.5+, or Edge.');
        }

        console.log('✓ Browser camera API supported');

        // Step 2: Request camera permission with fallback constraints
        let constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment'
            },
            audio: false
        };

        console.log('📷 Requesting camera access with constraints...');
        
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        } catch (initialError) {
            console.warn('Initial constraints failed, trying simpler constraints...');
            // Try with simpler constraints
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
        
        console.log('✓ Camera stream obtained');
        console.log('Camera tracks:', cameraStream.getTracks());
        cameraStream.getTracks().forEach(track => {
            console.log(`  - ${track.kind}: ${track.label} (enabled: ${track.enabled})`);
        });
        
        // Step 3: Get video element
        const videoElement = document.getElementById('videoStream');
        if (!videoElement) {
            throw new Error('Video element #videoStream not found in DOM');
        }
        console.log('✓ Video element found');

        // Step 4: Ensure video element is in DOM and visible
        if (!document.body.contains(videoElement)) {
            throw new Error('Video element is not attached to the DOM');
        }

        // Step 5: Attach stream to video element
        console.log('Attaching stream to video element...');
        videoElement.srcObject = cameraStream;
        
        // Step 6: Wait for video metadata and playback
        console.log('Waiting for video to load...');
        
        // Create a race condition - whichever event fires first
        const loadPromise = new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error('Video loading timeout - Camera may not be responding'));
            }, 10000);  // 10 second timeout
            
            const handleLoadedMetadata = () => {
                console.log('✓ Video metadata loaded');
                console.log('Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
                clearTimeout(timeoutId);
                cleanup();
                resolve();
            };
            
            const handleCanPlayThrough = () => {
                console.log('✓ Video can play through');
                clearTimeout(timeoutId);
                cleanup();
                resolve();
            };
            
            const cleanup = () => {
                videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
                videoElement.removeEventListener('canplaythrough', handleCanPlayThrough);
            };
            
            videoElement.addEventListener('loadedmetadata', handleLoadedMetadata, { once: true });
            videoElement.addEventListener('canplaythrough', handleCanPlayThrough, { once: true });
        });

        // Step 7: Try to play
        console.log('Attempting to play video...');
        try {
            await videoElement.play();
            console.log('✓ Video play() resolved');
        } catch (playError) {
            console.warn('play() method failed temporarily (may be due to auto-play policy):', playError.message);
            // Don't fail here - continue, as autoplay will kick in
        }
        
        // Wait for metadata/canplay
        try {
            await loadPromise;
        } catch (loadError) {
            console.warn('Metadata load timeout, but continuing...', loadError.message);
        }

        // Verify video is actually playing
        setTimeout(() => {
            const videoElement = document.getElementById('videoStream');
            if (videoElement) {
                if (videoElement.videoWidth === 0 || videoElement.videoHeight === 0) {
                    console.warn('⚠️ Video dimensions still 0, possible stream issue');
                } else {
                    console.log('✓ Video dimensions confirmed:', videoElement.videoWidth, 'x', videoElement.videoHeight);
                }
                
                if (videoElement.paused) {
                    console.warn('⚠️ Video is paused, attempting resume...');
                    videoElement.play().catch(err => console.error('Resume failed:', err));
                } else {
                    console.log('✓ Video is playing');
                }
            }
        }, 500);
        
        cameraActive = true;
        console.log('✓✓✓ CAMERA FULLY ACTIVE AND READY ✓✓✓');

        // Update UI
        document.getElementById('startCameraBtn').classList.add('hidden');
        document.getElementById('captureCameraBtn').classList.remove('hidden');
        document.getElementById('stopCameraBtn').classList.remove('hidden');
        document.getElementById('cameraError').classList.add('hidden');

        showToast('✓ Camera started successfully!', 'success');
        console.log('=== CAMERA START COMPLETE ===\n');
        
    } catch (error) {
        console.error('❌ CAMERA ERROR:', error.name || 'Unknown', '-', error.message);
        console.error('Full error:', error);
        
        const errorMsg = document.getElementById('cameraErrorMsg');
        
        // Specific error messages
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMsg.innerHTML = '<strong>Camera permission denied</strong><br>Please:\n1. Click the lock/camera icon in your address bar\n2. Select "Allow" for camera access\n3. Refresh and try again';
        } else if (error.name === 'NotFoundError') {
            errorMsg.innerHTML = '<strong>No camera found</strong><br>Check if your camera is connected and not in use by another app.';
        } else if (error.name === 'NotReadableError') {
            errorMsg.innerHTML = '<strong>Camera is in use</strong><br>Another application is using your camera. Close it and try again.';
        } else if (error.message.includes('timeout') || error.message.includes('loading')) {
            errorMsg.innerHTML = '<strong>Camera not responding</strong><br>Try:\n1. Refreshing the page\n2. Restarting your browser\n3. Checking device permissions';
        } else if (error.message.includes('HTTPS')) {
            errorMsg.innerHTML = '<strong>Secure connection required</strong><br>Camera access requires HTTPS or localhost.';
        } else {
            errorMsg.innerHTML = '<strong>Error:</strong> ' + (error.message || 'Unable to access camera');
        }

        // Show error UI
        document.getElementById('cameraError').classList.remove('hidden');
        document.getElementById('startCameraBtn').classList.remove('hidden');
        document.getElementById('captureCameraBtn').classList.add('hidden');
        document.getElementById('stopCameraBtn').classList.add('hidden');
        showToast('❌ Camera error: ' + error.message, 'error');
        console.log('=== CAMERA START FAILED ===\n');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
        cameraActive = false;

        const videoElement = document.getElementById('videoStream');
        videoElement.srcObject = null;

        // Update button states
        document.getElementById('startCameraBtn').classList.remove('hidden');
        document.getElementById('captureCameraBtn').classList.add('hidden');
        document.getElementById('stopCameraBtn').classList.add('hidden');
    }
}

async function captureFromCamera() {
    if (!cameraActive) {
        showToast('Camera is not active. Start it first!', 'error');
        return;
    }

    try {
        console.log('=== CAPTURE IMAGE INITIATED ===');
        document.getElementById('cameraCaptureLoading').classList.remove('hidden');

        const videoElement = document.getElementById('videoStream');
        if (!videoElement) {
            throw new Error('Video element not found');
        }

        // Step 1: Verify video is playing
        console.log('Checking video state...');
        if (videoElement.paused) {
            console.warn('⚠️ Video is paused, attempting to resume...');
            await videoElement.play();
        }

        // Step 2: Wait for video to have dimensions
        let attempts = 0;
        while ((videoElement.videoWidth === 0 || videoElement.videoHeight === 0) && attempts < 10) {
            console.log('Waiting for video dimensions... Attempt', attempts + 1);
            await new Promise(resolve => setTimeout(resolve, 200));
            attempts++;
        }

        console.log('Video dimensions:', videoElement.videoWidth, 'x', videoElement.videoHeight);
        
        if (videoElement.videoWidth === 0 || videoElement.videoHeight === 0) {
            throw new Error('Video stream has no dimensions. Camera may not be active.');
        }

        // Step 3: Create canvas
        console.log('Creating canvas...');
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        console.log('Canvas size:', canvas.width, 'x', canvas.height);

        // Step 4: Draw frame
        const context = canvas.getContext('2d');
        if (!context) {
            throw new Error('Could not get 2D canvas context');
        }

        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        console.log('✓ Frame drawn to canvas');

        // Step 5: Convert to image data
        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.95);
        console.log('Image data URL length:', imageDataUrl.length);
        
        if (!imageDataUrl || imageDataUrl.length < 100) {
            throw new Error('Failed to generate image data. Canvas may be empty.');
        }

        console.log('✓ Image captured Successfully');

        // Store image
        state.currentImage = imageDataUrl;

        // Stop camera
        stopCamera();

        // Switch to preview
        switchTabToUpload();
        showPreview(imageDataUrl);

        document.getElementById('cameraCaptureLoading').classList.add('hidden');
        showToast('✓ Image captured successfully!', 'success');
        console.log('=== CAPTURE COMPLETE ===');
        
    } catch (error) {
        console.error('❌ CAPTURE ERROR:', error);
        document.getElementById('cameraCaptureLoading').classList.add('hidden');
        showToast('Error capturing image: ' + error.message, 'error');
    }
}

function switchTabToUpload() {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const uploadTab = document.getElementById('uploadTab');
    if (uploadTab) {
        uploadTab.classList.add('active');
    }

    // Set upload button as active
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length > 0) {
        tabBtns[0].classList.add('active');
    }
}

// ============ SCANNING ============
async function scanImage() {
    if (!state.currentImage) {
        showToast('Please select an image first', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: state.currentImage })
        });

        const data = await response.json();

        if (data.success) {
            state.extractedText = data.extracted_text.split('\n').filter(t => t.trim());
            displayExtractedText(state.extractedText);
            showToast('Image scanned successfully!', 'success');
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Failed to scan image: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayExtractedText(ingredients) {
    const container = document.getElementById('extractedText');
    if (ingredients.length === 0) {
        container.innerHTML = '<p class="placeholder">No ingredients detected</p>';
        return;
    }

    let html = '';
    ingredients.forEach((ingredient, index) => {
        html += `
            <div class="ingredient-item">
                <span>${ingredient}</span>
                <button class="remove-btn" onclick="removeIngredient(${index})" title="Remove">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    });
    container.innerHTML = html;

    // Auto-analyze
    analyzeIngredients();
}

function removeIngredient(index) {
    state.extractedText.splice(index, 1);
    displayExtractedText(state.extractedText);
    if (state.extractedText.length > 0) {
        analyzeIngredients();
    }
}

// ============ ANALYSIS ============
async function analyzeIngredients() {
    const ingredients = state.extractedText;
    if (ingredients.length === 0) {
        showToast('No ingredients to analyze', 'warning');
        return;
    }

    // Get selected food category
    const foodCategory = document.getElementById('foodCategory').value || '';

    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ingredients: ingredients,
                userAllergens: state.userProfile.allergens,
                foodCategory: foodCategory
            })
        });

        const data = await response.json();

        if (data.success) {
            state.analysisResults = data;
            displayResults(data);
            showResults();
        } else {
            showToast('Error: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Failed to analyze ingredients: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function analyzeManualIngredients() {
    const text = document.getElementById('manualIngredients').value;
    if (!text.trim()) {
        showToast('Please enter some ingredients', 'warning');
        return;
    }

    state.extractedText = text
        .split(/[,\n;]/)
        .map(i => i.trim())
        .filter(i => i.length > 0);

    displayExtractedText(state.extractedText);
}

function displayResults(data) {
    // Update statistics - FOCUS ON ALLERGENS ONLY
    document.getElementById('totalIngredients').textContent = data.total_ingredients;
    document.getElementById('warningCount').textContent = data.warnings.length;
    
    // Update safe count to show only actual validated ingredients
    const actualSafeCount = Math.max(0, data.total_ingredients - data.warnings.length);
    document.getElementById('safeCount').textContent = actualSafeCount;

    // Update health score
    const scoreValue = data.health_score;
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreLabel = document.getElementById('scoreLabel');
    const scoreValueEl = document.getElementById('scoreValue');

    scoreValueEl.textContent = scoreValue;
    scoreCircle.classList.remove('warning', 'danger');

    if (scoreValue < 40) {
        scoreCircle.classList.add('danger');
        scoreLabel.textContent = 'Poor - Many allergens detected';
    } else if (scoreValue < 70) {
        scoreCircle.classList.add('warning');
        scoreLabel.textContent = 'Fair - Some allergens detected';
    } else {
        scoreLabel.textContent = 'Good - Safe to consume (No allergens detected)';
    }

    // Display warnings
    const warningsContainer = document.getElementById('warningsContainer');
    const warningsList = document.getElementById('warningsList');

    if (data.warnings.length > 0) {
        warningsContainer.classList.remove('hidden');
        let warningsHTML = '';
        data.warnings.forEach(warning => {
            warningsHTML += `
                <div class="warning-item">
                    <h4>${warning.ingredient}</h4>
                    <span class="warning-severity ${warning.severity}">${warning.severity.toUpperCase()}</span>
                    <p><strong>Allergen:</strong> ${warning.allergen}</p>
                    <p>${warning.description}</p>
                </div>
            `;
        });
        warningsList.innerHTML = warningsHTML;
    } else {
        warningsContainer.classList.add('hidden');
    }

    // Display safe ingredients (only for reference - focus is on allergens)
    const safeContainer = document.getElementById('safeContainer');
    const safeList = document.getElementById('safeIngredientsList');

    // Calculate safe ingredients more accurately
    const allergenIngredients = new Set(data.warnings.map(w => w.ingredient.toLowerCase()));
    const validSafeIngredients = state.extractedText.filter(ing => 
        !allergenIngredients.has(ing.toLowerCase()) && ing.trim().length > 2
    );

    if (validSafeIngredients.length > 0) {
        safeContainer.classList.remove('hidden');
        let safeHTML = '';
        const displayCount = Math.min(validSafeIngredients.length, 8); // Limit display
        validSafeIngredients.slice(0, displayCount).forEach(ingredient => {
            safeHTML += `<div class="ingredient-tag">${ingredient}</div>`;
        });
        if (validSafeIngredients.length > 8) {
            safeHTML += `<div class="ingredient-tag" style="color: #666;">+${validSafeIngredients.length - 8} more</div>`;
        }
        safeList.innerHTML = safeHTML;
    } else {
        safeContainer.classList.add('hidden');
    }

    // Display alternatives
    const alternativesContainer = document.getElementById('alternativesContainer');
    const alternativesList = document.getElementById('alternativesList');

    if (data.alternatives.length > 0) {
        alternativesContainer.classList.remove('hidden');
        let alternativesHTML = '';
        data.alternatives.forEach(alt => {
            let optionsHTML = '';
            alt.alternatives.forEach(option => {
                optionsHTML += `<span class="alternative-tag">${option}</span>`;
            });
            alternativesHTML += `
                <div class="alternative-item">
                    <h4>Instead of: ${alt.allergen}</h4>
                    <p>${alt.reason}</p>
                    <div class="alternative-options">${optionsHTML}</div>
                </div>
            `;
        });
        alternativesList.innerHTML = alternativesHTML;
    } else {
        alternativesContainer.classList.add('hidden');
    }

    // Display category-based recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        let recommendationsHTML = `
            <div class="recommendations-container" id="recommendationsContainer">
                <h3 style="margin-bottom: 20px; color: #10B981; display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-star"></i> Healthier Alternatives in "${data.food_category || 'This Category'}"
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        `;

        data.recommendations.forEach(product => {
            const allergenFreeInfo = product.allergen_free && product.allergen_free.length > 0 
                ? `<p style="margin: 8px 0; color: #10B981;"><i class="fas fa-check-circle"></i> <strong>Allergen Free:</strong> ${product.allergen_free.join(', ')}</p>`
                : '';

            recommendationsHTML += `
                <div style="border: 2px solid #e0e0e0; border-radius: 8px; padding: 15px; background: #fafafa; transition: all 0.3s ease;">
                    <h4 style="margin: 0 0 5px 0; color: #333;">${product.name}</h4>
                    <p style="margin: 3px 0; font-size: 14px; color: #666;"><strong>Brand:</strong> ${product.brand}</p>
                    <p style="margin: 3px 0; font-size: 14px; color: #666;"><strong>Category:</strong> ${product.category || 'N/A'}</p>
                    ${allergenFreeInfo}
                    <p style="margin: 8px 0; font-size: 14px;">
                        <i class="fas fa-heart" style="color: #ef4444;"></i> <strong>Health Score:</strong> ${product.health_score}/100
                    </p>
                    <p style="margin: 8px 0; font-size: 14px;">
                        <i class="fas fa-star" style="color: #fbbf24;"></i> <strong>Rating:</strong> ${product.rating}/5.0
                    </p>
            `;

            if (product.is_organic) {
                recommendationsHTML += `<p style="margin: 8px 0; color: #10B981;"><i class="fas fa-leaf"></i> <strong>Organic Product</strong></p>`;
            }

            recommendationsHTML += `</div>`;
        });

        recommendationsHTML += `</div></div>`;
        
        // Insert recommendations after alternatives
        const resultsSection = document.getElementById('results');
        let recommendationsDiv = document.getElementById('recommendationsContainer');
        if (recommendationsDiv) {
            recommendationsDiv.outerHTML = recommendationsHTML;
        } else {
            // If it doesn't exist, append it
            const newDiv = document.createElement('div');
            newDiv.innerHTML = recommendationsHTML;
            resultsSection.appendChild(newDiv.firstElementChild);
        }
    } else {
        // Hide recommendations if none available
        const recommendationsDiv = document.getElementById('recommendationsContainer');
        if (recommendationsDiv) {
            recommendationsDiv.style.display = 'none';
        }
    }

    // Create visualizations - ALLERGEN FOCUSED
    const allergenCount = data.warnings ? data.warnings.length : 0;
    const highRisk = data.warnings ? data.warnings.filter(w => w.severity === 'high').length : 0;
    const mediumLowRisk = allergenCount - highRisk;
    
    createAllergenSummaryChart(allergenCount, highRisk, mediumLowRisk);
    
    if (data.warnings && data.warnings.length > 0) {
        createAllergenChart(data.warnings);
    }
    
    // Get health scores from recommendations
    const recommendedScores = data.recommendations && data.recommendations.length > 0
        ? data.recommendations.map(r => r.health_score || 0)
        : [];
    
    createHealthScoreChart(data.health_score, recommendedScores);
    
    // Create allergen severity breakdown chart
    const insights = data.insights || {
        allergen_count: allergenCount,
        high_risk: highRisk,
        medium_low_risk: mediumLowRisk
    };
    createRiskChart(insights);
}

function showResults() {
    document.getElementById('scanner').scrollIntoView({ behavior: 'smooth' });
    document.getElementById('results').classList.remove('hidden');
}

function goBackToScanner() {
    document.getElementById('results').classList.add('hidden');
    clearImage();
    document.getElementById('manualIngredients').value = '';
    scrollToScanner();
}

// ============ PROFILE MANAGEMENT ============
let availableAllergens = [];

async function fetchAllergensList() {
    try {
        const response = await fetch(`${API_BASE_URL}/allergens`);
        const data = await response.json();
        if (data.success) {
            availableAllergens = data.allergens;
            renderAllergenSelector();
        }
    } catch (error) {
        console.error('Failed to fetch allergens:', error);
    }
}

function renderAllergenSelector() {
    const selector = document.getElementById('allergenSelector');
    let html = '';
    availableAllergens.forEach(allergen => {
        const isSelected = state.userProfile.allergens.includes(allergen);
        html += `
            <button class="allergen-btn ${isSelected ? 'selected' : ''}" 
                    onclick="toggleAllergen('${allergen}')">
                ${allergen}
            </button>
        `;
    });
    selector.innerHTML = html;
}

function toggleAllergen(allergen) {
    const index = state.userProfile.allergens.indexOf(allergen);
    if (index > -1) {
        state.userProfile.allergens.splice(index, 1);
    } else {
        state.userProfile.allergens.push(allergen);
    }
    renderAllergenSelector();
}

function openProfile() {
    document.getElementById('profileModal').classList.remove('hidden');
    
    // Display user info
    document.getElementById('profileName').textContent = state.userName || '-';
    document.getElementById('profileEmail').textContent = state.userEmail || '-';
    
    // Load dietary preferences
    document.getElementById('vegan').checked = state.userProfile.dietary.vegan;
    document.getElementById('vegetarian').checked = state.userProfile.dietary.vegetarian;
    document.getElementById('glutenfree').checked = state.userProfile.dietary.glutenfree;
    document.getElementById('dairyfree').checked = state.userProfile.dietary.dairyfree;
    
    // Load user statistics and scan history
    loadUserStatistics();
    loadScanHistory();
}

function closeProfile() {
    document.getElementById('profileModal').classList.add('hidden');
}

async function saveProfile() {
    state.userProfile.dietary = {
        vegan: document.getElementById('vegan').checked,
        vegetarian: document.getElementById('vegetarian').checked,
        glutenfree: document.getElementById('glutenfree').checked,
        dairyfree: document.getElementById('dairyfree').checked
    };
    
    // Save to backend
    try {
        const response = await fetch(`${API_BASE_URL}/user/${state.userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                allergens: state.userProfile.allergens,
                dietary_preferences: state.userProfile.dietary
            })
        });
        
        const data = await response.json();
        if (data.success) {
            closeProfile();
            showToast('Profile saved successfully!');
        } else {
            showToast('Error saving profile: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error saving profile: ' + error.message, 'error');
    }
}

function loadUserProfile() {
    const saved = localStorage.getItem('userProfile');
    if (saved) {
        state.userProfile = JSON.parse(saved);
    }
}

// ============ UTILITIES ============
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function showLoading(show) {
    const loading = document.getElementById('loadingSpinner');
    const dragZone = document.getElementById('dragDropZone');
    if (show) {
        loading.classList.remove('hidden');
        dragZone.classList.add('hidden');
    } else {
        loading.classList.add('hidden');
        dragZone.classList.add('hidden');
    }
}

function scrollToScanner() {
    document.getElementById('scanner').scrollIntoView({ behavior: 'smooth' });
}

function saveResults() {
    if (!state.analysisResults) return;

    const resultsData = {
        timestamp: new Date().toISOString(),
        ingredients: state.extractedText,
        results: state.analysisResults
    };

    const dataStr = JSON.stringify(resultsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scan-results-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);

    showToast('Results saved successfully!');
}

function handleNavClick(e) {
    const href = e.currentTarget.getAttribute('href');
    if (href && href.startsWith('#')) {
        document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
        e.currentTarget.classList.add('active');
    }
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
    }
}

// ============ WINDOW EVENTS ============
window.addEventListener('scroll', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section[id]');

    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
});

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + S to save results
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (!document.getElementById('results').classList.contains('hidden')) {
            saveResults();
        }
    }

    // Escape to close modal
    if (e.key === 'Escape') {
        const modal = document.getElementById('profileModal');
        if (!modal.classList.contains('hidden')) {
            closeProfile();
        }
    }
});

// ============ USER STATISTICS & SCAN HISTORY ============
async function loadUserStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/insights/${state.userId}`);
        const data = await response.json();

        if (data.success) {
            document.getElementById('totalScansCount').textContent = data.total_scans || 0;
            const avgScore = data.average_health_score ? Math.round(data.average_health_score * 10) / 10 : 0;
            document.getElementById('avgHealthScoreCount').textContent = avgScore;
        }
    } catch (error) {
        console.error('Failed to load user statistics:', error);
    }
}

async function loadScanHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/insights/${state.userId}`);
        const data = await response.json();

        if (data.success && data.scan_history && data.scan_history.length > 0) {
            let historyHTML = '';
            // Show last 5 scans
            const recentScans = data.scan_history.slice(0, 5);
            recentScans.forEach(scan => {
                const date = new Date(scan.created_at).toLocaleDateString();
                const ingredients = scan.ingredients || [];
                historyHTML += `
                    <div style="padding: 10px; border-bottom: 1px solid #eee; font-size: 14px;">
                        <p style="margin: 5px 0; font-weight: 600; color: #333;">${date}</p>
                        <p style="margin: 5px 0; color: #666;">Ingredients: ${ingredients.length}</p>
                        <p style="margin: 5px 0; color: #667eea; font-weight: 600;">Score: ${scan.health_score}/100</p>
                    </div>
                `;
            });
            document.getElementById('scanHistoryList').innerHTML = historyHTML;
        } else {
            document.getElementById('scanHistoryList').innerHTML = '<p style="color: #999; text-align: center;">No scans yet</p>';
        }
    } catch (error) {
        console.error('Failed to load scan history:', error);
    }
}

// ============ VISUALIZATION FUNCTIONS ============
function createAllergenSummaryChart(total, highRisk, mediumLowRisk) {
    const ctx = document.getElementById('safetyChart');
    if (!ctx) return;

    if (window.safetyChartInstance) {
        window.safetyChartInstance.destroy();
    }

    const labels = total === 0 
        ? ['No Allergens Found']
        : ['High Risk', 'Medium/Low Risk'];
    
    const data = total === 0 
        ? [1]
        : [highRisk, mediumLowRisk];
    
    const bgColors = total === 0 
        ? ['#10B981']
        : ['#EF4444', '#F59E0B'];

    window.safetyChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderColor: ['#fff', '#fff', '#fff'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

function createAllergenChart(warnings) {
    const ctx = document.getElementById('allergenChart');
    if (!ctx) return;

    // Count allergen occurrences
    const allergenCounts = {};
    warnings.forEach(w => {
        allergenCounts[w.allergen] = (allergenCounts[w.allergen] || 0) + 1;
    });

    const labels = Object.keys(allergenCounts).slice(0, 8); // Top 8
    const data = labels.map(label => allergenCounts[label]);

    if (window.allergenChartInstance) {
        window.allergenChartInstance.destroy();
    }

    window.allergenChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequency',
                data: data,
                backgroundColor: '#667eea',
                borderColor: '#667eea',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: labels.length > 4 ? 'y' : 'x',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createHealthScoreChart(currentScore, recommendedScores) {
    const ctx = document.getElementById('healthScoreChart');
    if (!ctx) return;

    if (window.healthScoreChartInstance) {
        window.healthScoreChartInstance.destroy();
    }

    // Calculate average of recommended scores
    const avgRecommendedScore = recommendedScores.length > 0 
        ? (recommendedScores.reduce((a, b) => a + b, 0) / recommendedScores.length)
        : 0;

    window.healthScoreChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Your Score', 'Avg Recommended'],
            datasets: [{
                label: 'Health Score',
                data: [currentScore, Math.round(avgRecommendedScore * 10) / 10],
                backgroundColor: ['#EF4444', '#10B981'],
                borderColor: ['#EF4444', '#10B981'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function createRiskChart(insights) {
    const ctx = document.getElementById('riskChart');
    if (!ctx) return;

    if (window.riskChartInstance) {
        window.riskChartInstance.destroy();
    }

    // Use new allergen-focused insights
    const allergenCount = insights.allergen_count || 0;
    const highRisk = insights.high_risk || 0;
    const mediumLowRisk = insights.medium_low_risk || 0;

    window.riskChartInstance = new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: allergenCount === 0 
                ? ['No Allergens Detected']
                : ['High Risk Allergens', 'Medium/Low Risk Allergens'],
            datasets: [{
                label: 'Allergen Severity Breakdown',
                data: allergenCount === 0 
                    ? [1]
                    : [highRisk, mediumLowRisk],
                backgroundColor: allergenCount === 0
                    ? ['#10B98199']
                    : ['#EF444499', '#F59E0B99'],
                borderColor: allergenCount === 0
                    ? ['#10B981']
                    : ['#EF4444', '#F59E0B'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// ============ POLYFILLS ============
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(search, pos) {
        return this.substr(!pos || pos < 0 ? 0 : +pos, search.length) === search;
    };
}
