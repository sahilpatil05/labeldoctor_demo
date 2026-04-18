// Determine API base URL based on current location
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api'
    : `${window.location.protocol}//${window.location.host}/api`;

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
    console.log('DOMContentLoaded: Starting checkAuthStatus...');
    
    // Attach form submit listeners immediately
    const loginFormElement = document.querySelector('form:has(#loginEmail)');
    const registerFormElement = document.querySelector('form:has(#registerEmail)');
    
    if (loginFormElement) {
        console.log('DOMContentLoaded: Attaching login form listener');
        loginFormElement.addEventListener('submit', handleLogin);
    } else {
        console.warn('DOMContentLoaded: Login form not found');
    }
    
    if (registerFormElement) {
        console.log('DOMContentLoaded: Attaching register form listener');
        registerFormElement.addEventListener('submit', handleRegister);
    } else {
        console.warn('DOMContentLoaded: Register form not found');
    }
    
    checkAuthStatus();
});

// ============ AUTHENTICATION ============
async function checkAuthStatus() {
    console.log('checkAuthStatus: Starting...');
    try {
        console.log('checkAuthStatus: Fetching current-user from', `${API_BASE_URL}/auth/current-user`);
        const response = await fetch(`${API_BASE_URL}/auth/current-user`, {
            credentials: 'include'
        });
        console.log('checkAuthStatus: Response status:', response.status);
        const data = await response.json();
        console.log('checkAuthStatus: Response data:', data);
        
        if (data.success) {
            // User is logged in
            console.log('checkAuthStatus: User is logged in, showing main app');
            state.userId = data.user_id;
            state.userName = data.name;
            state.userEmail = data.email;
            state.userProfile.allergens = data.allergens;
            state.userProfile.dietary = data.dietary_preferences;
            showMainApp();
        } else {
            // User is not logged in
            console.log('checkAuthStatus: User is not logged in, showing auth forms');
            showAuthForms();
        }
    } catch (error) {
        console.log('checkAuthStatus: Caught error:', error);
        showAuthForms();
    }
}

function showAuthForms() {
    console.log('showAuthForms: Displaying auth forms');
    const authContainer = document.getElementById('authContainer');
    const mainApp = document.getElementById('mainApp');
    
    if (authContainer) {
        authContainer.style.display = 'flex';
        authContainer.style.visibility = 'visible';
    }
    
    if (mainApp) {
        mainApp.style.display = 'none';
        mainApp.style.visibility = 'hidden';
    }
}

function showMainApp() {
    console.log('showMainApp: Hiding auth, showing main app');
    const authContainer = document.getElementById('authContainer');
    const mainApp = document.getElementById('mainApp');
    
    if (!authContainer || !mainApp) {
        console.error('showMainApp: Required elements not found!');
        return;
    }
    
    // Hide auth container
    authContainer.style.display = 'none';
    authContainer.style.visibility = 'hidden';
    
    // Show main app with multiple approaches to ensure visibility
    mainApp.style.display = 'block';
    mainApp.style.display = 'grid';
    mainApp.style.visibility = 'visible';
    
    console.log('showMainApp: Main app display set, calling setupEventListeners after delay');
    
    // Use setTimeout to ensure DOM is updated before setting up listeners
    setTimeout(() => {
        try {
            console.log('showMainApp: Calling setupEventListeners');
            setupEventListeners();
        } catch (error) {
            console.error('showMainApp: Error in setupEventListeners:', error);
        }
        
        try {
            console.log('showMainApp: Calling fetchAllergensList');
            fetchAllergensList();
        } catch (error) {
            console.error('showMainApp: Error in fetchAllergensList:', error);
        }
        
        console.log('showMainApp: Completed successfully');
    }, 100);
}

function toggleAuth() {
    console.log('toggleAuth: Toggling between login and register forms');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm.classList.contains('hidden-form')) {
        console.log('toggleAuth: Showing login form, hiding register form');
        loginForm.classList.remove('hidden-form');
        loginForm.style.display = 'block';
        registerForm.classList.add('hidden-form');
        registerForm.style.display = 'none';
    } else {
        console.log('toggleAuth: Hiding login form, showing register form');
        loginForm.classList.add('hidden-form');
        loginForm.style.display = 'none';
        registerForm.classList.remove('hidden-form');
        registerForm.style.display = 'block';
    }
    
    // Clear error messages
    document.querySelectorAll('.error-message').forEach(el => {
        el.style.display = 'none';
        el.textContent = '';
    });
}

async function handleLogin(e) {
    console.log('handleLogin: Form submitted');
    console.log('handleLogin: Event object:', e);
    
    // Prevent default form submission
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    console.log('handleLogin: Email =', email, ', Password length =', password.length);
    
    if (!email || !password) {
        console.log('handleLogin: Missing email or password');
        showErrorMessage('loginError', 'Please enter email and password');
        return false;
    }
    
    try {
        console.log('handleLogin: Attempting to fetch /auth/login');
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        console.log('handleLogin: Response received', data);
        
        if (data.success) {
            console.log('handleLogin: Login successful, showing main app');
            state.userId = data.user_id;
            state.userName = data.name;
            state.userEmail = data.email;
            state.userProfile.allergens = data.allergens;
            showMainApp();
            document.getElementById('loginForm').reset();
        } else {
            console.log('handleLogin: Login failed with error:', data.error);
            showErrorMessage('loginError', data.error || 'Login failed');
        }
    } catch (error) {
        console.log('handleLogin: Caught error:', error);
        showErrorMessage('loginError', error.message);
    }
    
    return false;
}

async function handleRegister(e) {
    console.log('handleRegister: Form submitted');
    console.log('handleRegister: Event object:', e);
    
    // Prevent default form submission
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    const name = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    
    console.log('handleRegister: Name =', name, ', Email =', email);
    
    // Validation
    if (!name || !email || !password) {
        showErrorMessage('registerError', 'Please fill all fields');
        return false;
    }
    
    if (password.length < 6) {
        showErrorMessage('registerError', 'Password must be at least 6 characters');
        return false;
    }
    
    if (password !== confirmPassword) {
        showErrorMessage('registerError', 'Passwords do not match');
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        console.log('handleRegister: Response received', data);
        
        if (data.success) {
            state.userId = data.user_id;
            state.userName = data.name;
            showMainApp();
            document.getElementById('registerForm').reset();
        } else {
            showErrorMessage('registerError', data.error || 'Registration failed');
        }
    } catch (error) {
        console.log('handleRegister: Caught error:', error);
        showErrorMessage('registerError', error.message);
    }
    
    return false;
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
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
    try {
        // Drag and Drop
        const dragDropZone = document.getElementById('dragDropZone');
        if (dragDropZone) {
            dragDropZone.addEventListener('click', () => document.getElementById('imageInput').click());
            dragDropZone.addEventListener('dragover', handleDragOver);
            dragDropZone.addEventListener('drop', handleDrop);
        }

        const imageInput = document.getElementById('imageInput');
        if (imageInput) {
            imageInput.addEventListener('change', handleImageSelect);
        }

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
    } catch (error) {
        console.error('setupEventListeners: Error setting up listeners:', error);
    }
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
    const dragDropZone = document.getElementById('dragDropZone');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const extractedText = document.getElementById('extractedText');
    
    if (dragDropZone) dragDropZone.classList.add('hidden');
    if (previewContainer) previewContainer.classList.remove('hidden');
    if (previewImage) previewImage.src = imageSrc;
    if (extractedText) extractedText.innerHTML = '<p class="placeholder">Image will be scanned...</p>';
}

function clearImage() {
    state.currentImage = null;
    const previewContainer = document.getElementById('previewContainer');
    const dragDropZone = document.getElementById('dragDropZone');
    const imageInput = document.getElementById('imageInput');
    const extractedText = document.getElementById('extractedText');
    
    if (previewContainer) previewContainer.classList.add('hidden');
    if (dragDropZone) dragDropZone.classList.remove('hidden');
    if (imageInput) imageInput.value = '';
    if (extractedText) extractedText.innerHTML = '<p class="placeholder">Image will appear here after scanning</p>';
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
        } else if (tabName === 'text' && btn.textContent.includes('Text')) {
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

        // Update UI - with null checks
        const startBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureCameraBtn');
        const stopBtn = document.getElementById('stopCameraBtn');
        const cameraError = document.getElementById('cameraError');
        
        if (startBtn) startBtn.classList.add('hidden');
        if (captureBtn) captureBtn.classList.remove('hidden');
        if (stopBtn) stopBtn.classList.remove('hidden');
        if (cameraError) cameraError.classList.add('hidden');

        showToast('✓ Camera started successfully!', 'success');
        console.log('=== CAMERA START COMPLETE ===\n');
        
    } catch (error) {
        console.error('❌ CAMERA ERROR:', error.name || 'Unknown', '-', error.message);
        console.error('Full error:', error);
        
        const errorMsg = document.getElementById('cameraErrorMsg');
        const cameraError = document.getElementById('cameraError');
        
        if (!errorMsg || !cameraError) {
            console.error('Camera error UI elements not found!');
            showToast('❌ Camera error: ' + error.message, 'error');
            return;
        }
        
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
        cameraError.classList.remove('hidden');
        const startBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureCameraBtn');
        const stopBtn = document.getElementById('stopCameraBtn');
        
        if (startBtn) startBtn.classList.remove('hidden');
        if (captureBtn) captureBtn.classList.add('hidden');
        if (stopBtn) stopBtn.classList.add('hidden');
        
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
        if (videoElement) videoElement.srcObject = null;

        // Update button states
        const startBtn = document.getElementById('startCameraBtn');
        const captureBtn = document.getElementById('captureCameraBtn');
        const stopBtn = document.getElementById('stopCameraBtn');
        
        if (startBtn) startBtn.classList.remove('hidden');
        if (captureBtn) captureBtn.classList.add('hidden');
        if (stopBtn) stopBtn.classList.add('hidden');
    }
}

async function captureFromCamera() {
    if (!cameraActive) {
        showToast('Camera is not active. Start it first!', 'error');
        return;
    }

    try {
        console.log('=== CAPTURE IMAGE INITIATED ===');
        const cameraCaptureLoading = document.getElementById('cameraCaptureLoading');
        if (cameraCaptureLoading) cameraCaptureLoading.classList.remove('hidden');

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

        const cameraCaptureLoading2 = document.getElementById('cameraCaptureLoading');
        if (cameraCaptureLoading2) cameraCaptureLoading2.classList.add('hidden');
        showToast('✓ Image captured successfully!', 'success');
        console.log('=== CAPTURE COMPLETE ===');
        
    } catch (error) {
        console.error('❌ CAPTURE ERROR:', error);
        const cameraCaptureLoading3 = document.getElementById('cameraCaptureLoading');
        if (cameraCaptureLoading3) cameraCaptureLoading3.classList.add('hidden');
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
        // Get selected food category
        const foodCategoryEl = document.getElementById('foodCategory');
        const foodCategory = (foodCategoryEl && foodCategoryEl.value) ? foodCategoryEl.value : '';
        
        // Use raw OCR mode (no preprocessing)
        const usePreprocessing = false;

        // Unified endpoint - send image with user allergens and food category
        const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ 
                image: state.currentImage,
                userAllergens: state.userProfile.allergens || [],
                userId: state.userId,
                foodCategory: foodCategory,
                usePreprocessing: usePreprocessing
            })
        });

        const data = await response.json();

        if (data.success) {
            // Extract ingredients from unified response - with safety checks
            state.extractedText = data.extracted_ingredients || [];
            state.analysisResults = data;
            
            // Safety checks for data structure
            if (!Array.isArray(state.extractedText)) {
                state.extractedText = [];
            }
            
            displayExtractedText(state.extractedText);
            displayResults(data);
            showResults();
            
            // Confirm raw OCR mode
            showToast('Image scanned in RAW OCR mode - successfully analyzed!', 'success');
        } else {
            showToast('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Scan error:', error);
        showToast('Failed to scan image: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ============ DEMO MODE ============
async function loadDemoScan() {
    console.log('Loading demo scan...');
    showLoading(true);
    
    try {
        // Show a processing message
        showToast('Loading demo scan (simulating realistic processing delays)...', 'info');
        
        // Call the demo endpoint
        const response = await fetch(`${API_BASE_URL}/demo/scan`, {
            method: 'GET',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Demo scan loaded:', data);
            
            // Store the demo results in state
            state.extractedText = data.extracted_ingredients || [];
            state.analysisResults = data;
            
            // Update user allergens if different from demo user
            if (data.demo_user_allergens) {
                state.userProfile.allergens = data.demo_user_allergens;
            }
            
            // Display results
            displayExtractedText(state.extractedText);
            displayResults(data);
            showResults();
            
            // Show success message with demo info
            showToast(`✓ Demo scan complete! Allergens detected: ${data.allergen_count}. Processing time: ${data.processing_time}`, 'success');
            
            // Scroll to results
            setTimeout(() => {
                document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
            }, 500);
        } else {
            showToast('Error: ' + (data.error || 'Failed to load demo'), 'error');
        }
    } catch (error) {
        console.error('Demo scan error:', error);
        showToast('Failed to load demo: ' + error.message, 'error');
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

    // Create wrapper for flex display
    let html = '<div class="ingredients-flex-container">';
    
    ingredients.forEach((ingredient, index) => {
        // Clean up ingredient name
        const cleanedIngredient = ingredient.trim().toLowerCase().replace(/^\s+|\s+$/g, '');
        
        html += `
            <div class="ingredient-badge">
                <span class="badge-text" title="${cleanedIngredient}">${cleanedIngredient}</span>
                <button class="badge-remove-btn" onclick="removeIngredient(${index})" title="Remove this ingredient">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    });
    
    html += '</div>';
    html += `<div class="ingredients-count"><small>${ingredients.length} ingredient${ingredients.length !== 1 ? 's' : ''} detected</small></div>`;
    container.innerHTML = html;
}

function removeIngredient(index) {
    try {
        if (!state.extractedText || index < 0 || index >= state.extractedText.length) {
            console.warn('Invalid ingredient index:', index);
            return;
        }
        
        const removedIngredient = state.extractedText.splice(index, 1)[0];
        console.log('Removed ingredient:', removedIngredient);
        
        // Update display
        if (typeof displayExtractedText === 'function') {
            displayExtractedText(state.extractedText);
        }
        
        // Re-analyze if ingredients remain and results exist
        if (state.extractedText.length > 0 && state.analysisResults) {
            analyzeIngredients();
        } else if (state.extractedText.length === 0 && state.analysisResults) {
            // Clear results if no ingredients left
            state.analysisResults = null;
            displayResults(null);
        }
        
        showToast('Ingredient removed', 'success');
    } catch (error) {
        console.error('Error removing ingredient:', error);
        showToast('Error removing ingredient', 'error');
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
            credentials: 'include',
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
    // Now analyze the manually entered ingredients
    analyzeIngredients();
}

function displayResults(data) {
    // Safety checks - ensure all data fields exist before using them
    if (!data) {
        showToast('No data received from analysis', 'error');
        return;
    }

    // Provide defaults for all fields that might be undefined
    const totalIngredients = data.total_ingredients || 0;
    const warnings = data.warnings || [];
    const safeIngredients = data.safe_ingredients || [];
    const healthScore = data.health_score || 100;
    const safetyStatus = data.safety_status || 'safe';
    const allergenCount = data.allergen_count || 0;
    
    // Update statistics
    document.getElementById('totalIngredients').textContent = totalIngredients;
    document.getElementById('warningCount').textContent = warnings.length;
    document.getElementById('safeCount').textContent = safeIngredients.length;

    // Update health score
    const scoreValue = healthScore;
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreLabel = document.getElementById('scoreLabel');
    const scoreValueEl = document.getElementById('scoreValue');
    
    scoreValueEl.textContent = scoreValue;
    scoreCircle.classList.remove('safe', 'medium', 'unsafe');
    scoreCircle.classList.add(safetyStatus);

    // Set status text
    let statusIcon = '';
    let statusColor = '';
    let statusText = '';
    
    if (safetyStatus === 'unsafe') {
        statusIcon = '🚨';
        statusColor = '#EF4444';
        statusText = `UNSAFE - ${allergenCount} allergens detected`;
    } else if (safetyStatus === 'medium') {
        statusIcon = '⚠️';
        statusColor = '#F59E0B';
        statusText = `MEDIUM RISK - ${allergenCount} allergen detected`;
    } else {
        statusIcon = '✓';
        statusColor = '#10B981';
        statusText = `SAFE - No allergens, ${safeIngredients.length} safe ingredient(s)`;
    }
    
    scoreLabel.innerHTML = `<span style="color: ${statusColor}; font-weight: bold; font-size: 16px;">${statusIcon} ${statusText}</span>`;

    // Display recommendations section  
    const recommendations = data.recommendations || [];
    if (recommendations && recommendations.length > 0) {
        let recommendationsHTML = `
            <div class="recommendations-container" id="recommendationsContainer">
                <h3 style="margin-bottom: 20px; color: #10B981; display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-star"></i> Healthier Alternatives
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        `;

        recommendations.forEach(product => {
            recommendationsHTML += `
                <div style="border: 2px solid #e0e0e0; border-radius: 8px; padding: 15px; background: #fafafa;">
                    <h4 style="margin: 0 0 5px 0; color: #333;">${product.name || 'Product'}</h4>
                    <p style="margin: 3px 0; font-size: 14px; color: #666;"><strong>Brand:</strong> ${product.brand || 'N/A'}</p>
                    <p style="margin: 8px 0; font-size: 14px;"><i class="fas fa-heart" style="color: #ef4444;"></i> <strong>Score:</strong> ${product.health_score || 0}/100</p>
                </div>
            `;
        });

        recommendationsHTML += `</div></div>`;
        
        const resultsSection = document.getElementById('results');
        let recommendationsDiv = document.getElementById('recommendationsContainer');
        if (recommendationsDiv) {
            recommendationsDiv.outerHTML = recommendationsHTML;
        } else if (resultsSection) {
            const newDiv = document.createElement('div');
            newDiv.innerHTML = recommendationsHTML;
            resultsSection.appendChild(newDiv.firstElementChild);
        }
    }

    // Display warnings with severity indicator and deduplication
    const warningsContainer = document.getElementById('warningsContainer');
    const warningsList = document.getElementById('warningsList');

    if (warningsContainer && warningsList && data.warnings.length > 0) {
        warningsContainer.classList.remove('hidden');
        
        // Deduplicate warnings by ingredient (keep first occurrence)
        const uniqueWarnings = [];
        const seenIngredients = new Set();
        
        data.warnings.forEach(warning => {
            const ingredientLower = warning.ingredient.toLowerCase();
            if (!seenIngredients.has(ingredientLower)) {
                uniqueWarnings.push(warning);
                seenIngredients.add(ingredientLower);
            }
        });
        
        // Create safety badge based on allergen count
        let badgeColor = safetyStatus === 'unsafe' ? '#EF4444' : '#F59E0B';
        let badgeIcon = safetyStatus === 'unsafe' ? '🚨' : '⚠️';
        let badgeText = safetyStatus === 'unsafe' 
            ? `UNSAFE - Product contains ${uniqueWarnings.length} allergen(s)` 
            : `MEDIUM RISK - Product contains ${uniqueWarnings.length} allergen(s)`;
        
        let warningsHTML = `<div class="allergen-count-badge" style="background: ${badgeColor}; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; font-size: 16px;">
            ${badgeIcon} ${badgeText}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px;">`;
        
        uniqueWarnings.forEach(warning => {
            warningsHTML += `
                <div style="display: flex; align-items: flex-start; padding: 12px 15px; background: white; border-left: 5px solid ${badgeColor}; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <span style="color: ${badgeColor}; font-size: 18px; margin-right: 10px; flex-shrink: 0;">⚠️</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #333; margin-bottom: 4px;">${warning.ingredient}</div>
                        <div style="font-size: 13px; color: #666;">
                            <strong>Allergen:</strong> ${warning.allergen} 
                            <span style="background: ${badgeColor}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-left: 8px;">${warning.severity.toUpperCase()}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        warningsHTML += `</div>`;
        warningsList.innerHTML = warningsHTML;
    } else if (warningsContainer) {
        warningsContainer.classList.add('hidden');
    }

    // Display safe ingredients (only unique ones for clarity)
    const safeContainer = document.getElementById('safeContainer');
    const safeList = document.getElementById('safeIngredientsList');

    // Get unique safe ingredients from server response or calculate locally
    const uniqueSafeIngredients = data.safe_ingredients && data.safe_ingredients.length > 0 
        ? data.safe_ingredients 
        : (() => {
            const allergenIngredients = new Set(data.warnings.map(w => w.ingredient.toLowerCase()));
            return state.extractedText.filter(ing => 
                !allergenIngredients.has(ing.toLowerCase()) && ing.trim().length > 2
            );
        })();

    if (safeContainer && safeList && uniqueSafeIngredients.length > 0) {
        safeContainer.classList.remove('hidden');
        
        // Split ingredients into chunks for better readability
        const itemsPerRow = 3;
        const chunks = [];
        for (let i = 0; i < uniqueSafeIngredients.length; i += itemsPerRow) {
            chunks.push(uniqueSafeIngredients.slice(i, i + itemsPerRow));
        }
        let safeHTML = `<div style="background: #D1FAE5; border: 2px solid #6EE7B7; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <h4 style="color: #065F46; margin: 0 0 15px 0;">✓ Safe Ingredients (${uniqueSafeIngredients.length} total)</h4>`;
        
        // Add a grid layout for safe ingredients
        if (uniqueSafeIngredients.length > 10) {
            safeHTML += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px;">`;
            uniqueSafeIngredients.forEach(ingredient => {
                safeHTML += `<div style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; background: white; border-left: 3px solid #10B981; border-radius: 4px;">
                    <i class="fas fa-check-circle" style="color: #10B981; font-size: 14px; flex-shrink: 0;"></i>
                    <span style="color: #065F46; font-weight: 500; font-size: 14px;">${ingredient}</span>
                </div>`;
            });
            safeHTML += `</div>`;
        } else {
            safeHTML += `<div style="display: flex; flex-direction: column; gap: 8px;">`;
            uniqueSafeIngredients.forEach(ingredient => {
                safeHTML += `<div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 15px; background: white; border-left: 5px solid #10B981; border-radius: 4px;">
                    <span style="flex: 1; color: #065F46; font-weight: 500; font-size: 15px;">${ingredient}</span>
                    <i class="fas fa-check-circle" style="color: #10B981; font-size: 16px;"></i>
                </div>`;
            });
            safeHTML += `</div>`;
        }
        
        safeHTML += `</div>`;
        safeList.innerHTML = safeHTML;
    } else if (safeContainer) {
        safeContainer.classList.add('hidden');
    }

    // Display category-based recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        let recommendationsHTML = `
            <div class="recommendations-container" id="recommendationsContainer">
                <h3 style="margin-bottom: 20px; color: #10B981; display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-star"></i> Better Alternatives in "${data.food_category || 'Similar Category'}"
                </h3>
                <p style="color: #666; margin-bottom: 15px; font-size: 14px;">These alternatives are free from your allergens and may have better nutritional profiles.</p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
        `;

        data.recommendations.forEach(product => {
            // Determine improvement styling
            const healthImprovement = product.improvement_value !== undefined ? product.improvement_value : 0;
            const improvementColor = healthImprovement > 0 ? '#10B981' : healthImprovement < 0 ? '#EF4444' : '#666';
            const improvementIcon = healthImprovement > 0 ? '↑' : healthImprovement < 0 ? '↓' : '→';
            
            // Allergen free info
            const allergenFreeInfo = product.allergen_free && product.allergen_free.length > 0 
                ? `<p style="margin: 8px 0; padding: 8px 12px; background: #D1FAE5; border-left: 4px solid #10B981; color: #065F46; border-radius: 4px; font-size: 13px;"><i class="fas fa-check-circle"></i> Free from: ${product.allergen_free.join(', ')}</p>`
                : '';

            // Reason/comparison
            const reasonText = product.reason || `${healthImprovement > 0 ? 'Higher' : 'Similar'} quality alternative in category`;

            recommendationsHTML += `
                <div style="border: 2px solid #10B981; border-radius: 10px; padding: 18px; background: #f0fdf4; transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #065F46; font-size: 16px;">${product.name}</h4>
                            <p style="margin: 0; font-size: 13px; color: #059669;"><strong>${product.brand}</strong></p>
                        </div>
                        <span style="background: ${improvementColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                            ${improvementIcon} ${product.improvement || 'Similar'}
                        </span>
                    </div>
                    
                    <p style="margin: 8px 0; font-size: 13px; color: #666; padding: 8px; background: white; border-left: 3px solid #fbbf24; border-radius: 3px;">
                        <i class="fas fa-lightbulb"></i> ${reasonText}
                    </p>
                    
                    ${allergenFreeInfo}
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0;">
                        <div style="background: white; padding: 8px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 2px;">Your Score</div>
                            <div style="font-size: 18px; font-weight: bold; color: #EF4444;">${data.health_score || 'N/A'}</div>
                        </div>
                        <div style="background: white; padding: 8px; border-radius: 6px; text-align: center;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 2px;">Alternative</div>
                            <div style="font-size: 18px; font-weight: bold; color: #10B981;">${product.health_score || 'N/A'}</div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <p style="margin: 0; font-size: 13px; text-align: center;">
                            <i class="fas fa-star" style="color: #fbbf24;"></i> ${product.rating || 'N/A'}/5.0
                        </p>
                        <p style="margin: 0; font-size: 13px; text-align: center;">
                            ${product.is_organic ? '<i class="fas fa-leaf" style="color: #10B981;"></i> Organic' : '<i class="fas fa-check" style="color: #666;"></i> Verified'}
                        </p>
                    </div>
                </div>
            `;
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
    const warningsCount = data.warnings ? data.warnings.length : 0;
    const highRisk = data.warnings ? data.warnings.filter(w => w.severity === 'high').length : 0;
    const mediumLowRisk = warningsCount - highRisk;
    
    // Display all extracted ingredients (each individually in list format)
    const allIngredientsContainer = document.getElementById('allIngredientsContainer');
    const allIngredientsList = document.getElementById('allIngredientsList');
    
    if (allIngredientsContainer && allIngredientsList && state.extractedText && state.extractedText.length > 0) {
        allIngredientsContainer.classList.remove('hidden');
        
        // Create a map of warning ingredients for quick lookup
        const warningIngredientsSet = new Set(
            (data.warnings || []).map(w => w.ingredient.toLowerCase())
        );
        
        // Separate warning and safe ingredients
        const warningItems = [];
        const safeItems = [];
        
        state.extractedText.forEach((ingredient, index) => {
            const isWarning = warningIngredientsSet.has(ingredient.toLowerCase());
            if (isWarning) {
                warningItems.push({ ingredient, index });
            } else {
                safeItems.push({ ingredient, index });
            }
        });
        
        // Display warnings first, then safe ingredients
        let ingredientsHTML = '';
        
        // Warning ingredients section
        if (warningItems.length > 0) {
            ingredientsHTML += `<div style="margin-bottom: 15px;">
                <h5 style="color: #DC2626; margin: 10px 0; font-size: 14px;"><i class="fas fa-exclamation"></i> Ingredients with Allergens (${warningItems.length})</h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px;">`;
            
            warningItems.forEach(item => {
                ingredientsHTML += `<div style="border-left: 5px solid #DC2626; padding: 8px 12px; background: #FEE2E2; border-radius: 4px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="color: #7F1D1D; font-size: 14px;">${item.ingredient}</span>
                    <button onclick="removeIngredient(${item.index})" style="background: none; border: none; color: #DC2626; cursor: pointer; font-size: 16px; padding: 0; display: flex; align-items: center;">✕</button>
                </div>`;
            });
            
            ingredientsHTML += `</div></div>`;
        }
        
        // Safe ingredients section
        if (safeItems.length > 0) {
            ingredientsHTML += `<div>
                <h5 style="color: #10B981; margin: 10px 0; font-size: 14px;"><i class="fas fa-check"></i> Safe Ingredients (${safeItems.length})</h5>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px;">`;
            
            safeItems.forEach(item => {
                ingredientsHTML += `<div style="border-left: 5px solid #10B981; padding: 8px 12px; background: #F0FDF4; border-radius: 4px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="color: #166534; font-size: 14px;">${item.ingredient}</span>
                    <button onclick="removeIngredient(${item.index})" style="background: none; border: none; color: #10B981; cursor: pointer; font-size: 16px; padding: 0; display: flex; align-items: center;">✕</button>
                </div>`;
            });
            
            ingredientsHTML += `</div></div>`;
        }
        
        allIngredientsList.innerHTML = ingredientsHTML;
    } else if (allIngredientsContainer) {
        allIngredientsContainer.classList.add('hidden');
    }
    
    createAllergenSummaryChart(allergenCount, highRisk, mediumLowRisk);
    
    if (data.warnings && data.warnings.length > 0) {
        createAllergenChart(data.warnings);
    }
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
    if (!selector) {
        console.warn('renderAllergenSelector: allergenSelector element not found');
        return;
    }
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
            credentials: 'include',
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
        e.preventDefault();
        
        // Close profile section if open
        const profileSection = document.getElementById('profile');
        if (profileSection && !profileSection.classList.contains('hidden')) {
            hideProfileSection();
        }
        
        // Update active link
        document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
        e.currentTarget.classList.add('active');
        
        // Scroll to target
        const targetId = href.substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
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
        const response = await fetch(`${API_BASE_URL}/insights/${state.userId}`, {
            credentials: 'include'
        });
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
        const response = await fetch(`${API_BASE_URL}/insights/${state.userId}`, {
            credentials: 'include'
        });
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

// ============ PROFILE SECTION FUNCTIONS ============
function toggleEditMode(type) {
    if (type === 'allergens') {
        toggleEditAllergens();
    } else if (type === 'preferences') {
        toggleEditPreferences();
    }
}

function showProfileSection() {
    // Hide all main sections
    const mainSections = document.querySelectorAll('.hero, .scanner-section, .results-section, .about, #facts');
    mainSections.forEach(section => section.classList.add('hidden'));
    
    // Show profile section
    const profileSection = document.getElementById('profile');
    if (profileSection) {
        profileSection.classList.remove('hidden');
        profileSection.classList.add('active');
        loadProfileData();
        populateAllergenInfoGuide();
    }
    
    // Remove active state from nav links
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function hideProfileSection() {
    // Hide profile section
    const profileSection = document.getElementById('profile');
    if (profileSection) {
        profileSection.classList.add('hidden');
        profileSection.classList.remove('active');
    }
    
    // Show main sections
    const mainSections = document.querySelectorAll('.hero, .scanner-section, .results-section, .about, #facts');
    mainSections.forEach(section => section.classList.remove('hidden'));
    
    // Set home section as active
    const homeLink = document.querySelector('a[href="#home"]');
    if (homeLink) {
        homeLink.classList.add('active');
    }
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadProfileData() {
    try {
        // Display user info
        const nameElement = document.getElementById('profileName');
        const emailElement = document.getElementById('profileEmail');
        if (nameElement) nameElement.textContent = state.userName || 'User';
        if (emailElement) emailElement.textContent = state.userEmail || 'No email';
        
        // Display allergens
        displayAllergens();
        
        // Display dietary preferences
        displayDietaryPreferences();
        
    } catch (error) {
        console.error('Error loading profile data:', error);
        showToast('Error loading profile data', 'error');
    }
}

function displayAllergens() {
    const allergensList = document.getElementById('allergensList');
    if (!allergensList) return;
    
    if (!state.userProfile.allergens || state.userProfile.allergens.length === 0) {
        allergensList.innerHTML = '<p class="no-data-text">No allergens selected</p>';
    } else {
        let html = '';
        state.userProfile.allergens.forEach(allergen => {
            html += `<span class="allergen-badge">${allergen}</span>`;
        });
        allergensList.innerHTML = html;
    }
}

function displayDietaryPreferences() {
    const preferencesList = document.getElementById('preferencesList');
    if (!preferencesList) return;
    
    const prefs = state.userProfile.dietary || {};
    const selectedPrefs = Object.keys(prefs).filter(key => prefs[key]);
    
    if (selectedPrefs.length === 0) {
        preferencesList.innerHTML = '<p class="no-data-text">No dietary preferences selected</p>';
    } else {
        let html = '';
        selectedPrefs.forEach(pref => {
            const displayName = pref.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            html += `<span class="preference-badge">${displayName}</span>`;
        });
        preferencesList.innerHTML = html;
    }
}

function populateAllergenInfoGuide() {
    const container = document.getElementById('allergenInfoContainer');
    if (!container) return;

    const allergenInfo = [
        {
            name: 'Milk',
            icon: '🥛',
            description: 'Contains proteins (casein, whey) and lactose. Found in dairy products, cream sauces, some chocolates, and processed foods. Common alternatives: almond, soy, or oat milk.'
        },
        {
            name: 'Egg',
            icon: '🥚',
            description: 'Found in eggs and egg-based products. Also hidden in mayonnaise, some baked goods, and processed meats. Protein-rich alternative for cooking: aquafaba.'
        },
        {
            name: 'Fish',
            icon: '🐟',
            description: 'Includes all fish species and fish-derived ingredients (anchovies, fish sauce, Worcestershire sauce). Often found in Asian cuisines and seafood dishes.'
        },
        {
            name: 'Shellfish',
            icon: '🦐',
            description: 'Includes shrimp, crab, lobster, oysters, mussels, and clams. Cross-contamination risk in seafood restaurants. Common in Asian and Mediterranean cuisines.'
        },
        {
            name: 'Tree Nuts',
            icon: '🌰',
            description: 'Includes almonds, walnuts, cashews, pistachios, and pecans. Found in nut butters, baked goods, cereals, and some sauces. High cross-contamination risk.'
        },
        {
            name: 'Peanuts',
            icon: '🥜',
            description: 'Technically a legume, not a tree nut. Found in peanut butter, candy, baked goods, and Asian cuisines. Often processed in facilities with tree nuts.'
        },
        {
            name: 'Wheat',
            icon: '🌾',
            description: 'A common grain allergen. Found in breads, cereals, pasta, and many processed foods. Contains gluten protein. Alternatives: rice, corn, or gluten-free flour.'
        },
        {
            name: 'Soy',
            icon: '🫘',
            description: 'From soybean plant. Found in tofu, soy sauce, edamame, and many processed foods as soy lecithin. Common in Asian cuisine and vegetarian products.'
        },
        {
            name: 'Sesame',
            icon: '🪨',
            description: 'Found in tahini, sesame oil, and seeds. Common in Asian, Middle Eastern, and Mediterranean cuisines. Often in hummus, dressings, and baked goods.'
        },
        {
            name: 'Mustard',
            icon: '🌻',
            description: 'Includes mustard seeds, mustard powder, and mustard oil. Found in condiments, salad dressings, pickled foods, and spice mixes. Less common allergen.'
        },
        {
            name: 'Gluten',
            icon: '🌽',
            description: 'A protein in wheat, barley, and rye. Triggers celiac disease and gluten sensitivity. Hidden in sauces, gravies, processed foods, and some medications.'
        },
        {
            name: 'Sulphites',
            icon: '🍇',
            description: 'Preservatives in dried fruits, wines, juices, and some medications. Can cause respiratory issues in sensitive individuals. Look for "sulfite-free" labels.'
        },
        {
            name: 'Corn',
            icon: '🌽',
            description: 'Found in corn flour, corn syrup, cornstarch, and many processed foods. Common in baked goods, snacks, and as corn oil or corn derivatives.'
        },
        {
            name: 'Celery',
            icon: '🥬',
            description: 'Includes celery, celeriac, and celery seeds. Found in salads, soups, stocks, and spice mixes. Cross-reactivity with birch pollen common in some regions.'
        },
        {
            name: 'Lupin',
            icon: '🌿',
            description: 'A legume gaining popularity in gluten-free products. Found in lupin flour, lupini beans, and some European baked goods. Less common but growing allergen.'
        },
        {
            name: 'Molluscs',
            icon: '🦑',
            description: 'Includes squid, octopus, snails, and scallops. Found in Mediterranean and Asian cuisines. Often processed with shellfish in the same facilities.'
        },
        {
            name: 'MSG',
            icon: '🧂',
            description: 'Monosodium glutamate - a flavor enhancer. Found in processed foods, condiments, Asian seasonings, and some soups. Can trigger sensitivity reactions in some people.'
        }
    ];

    let html = '';
    allergenInfo.forEach(allergen => {
        const isSelected = state.userProfile.allergens && state.userProfile.allergens.includes(allergen.name);
        html += `
            <div style="padding: 15px; border: 2px solid ${isSelected ? '#667eea' : '#e5e7eb'}; border-radius: 8px; background: ${isSelected ? '#f0f4ff' : '#f9fafb'}; cursor: pointer;" onclick="toggleAllergenInfo('${allergen.name}')">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 24px; margin-right: 10px;">${allergen.icon}</span>
                    <h4 style="margin: 0; color: #1f2937;">${allergen.name}</h4>
                    ${isSelected ? '<i class="fas fa-check-circle" style="margin-left: auto; color: #667eea; font-size: 18px;"></i>' : ''}
                </div>
                <p style="margin: 0; font-size: 13px; color: #666; line-height: 1.4;">${allergen.description}</p>
            </div>
        `;
    });

    container.innerHTML = html;
}

function toggleAllergenInfo(allergenName) {
    const index = state.userProfile.allergens.indexOf(allergenName);
    if (index > -1) {
        state.userProfile.allergens.splice(index, 1);
    } else {
        state.userProfile.allergens.push(allergenName);
    }
    populateAllergenInfoGuide();
}

function toggleEditAllergens() {
    const viewMode = document.getElementById('allergenViewMode');
    const editMode = document.getElementById('allergenEditMode');
    const buttonGroup = document.querySelector('#allergenEditMode .button-group');
    
    if (viewMode.classList.contains('hidden')) {
        // Switch to view mode
        viewMode.classList.remove('hidden');
        editMode.classList.add('hidden');
        displayAllergens();
    } else {
        // Switch to edit mode
        viewMode.classList.add('hidden');
        editMode.classList.remove('hidden');
        populateAllergenCheckboxes();
    }
}

function toggleEditPreferences() {
    const viewMode = document.getElementById('preferencesViewMode');
    const editMode = document.getElementById('preferencesEditMode');
    
    if (viewMode.classList.contains('hidden')) {
        // Switch to view mode
        viewMode.classList.remove('hidden');
        editMode.classList.add('hidden');
        displayDietaryPreferences();
    } else {
        // Switch to edit mode
        viewMode.classList.add('hidden');
        editMode.classList.remove('hidden');
        populatePreferenceCheckboxes();
    }
}

function populateAllergenCheckboxes() {
    const container = document.getElementById('allergenCheckboxes');
    if (!container) return;
    
    const allergens = ['Milk', 'Egg', 'Fish', 'Shellfish', 'Tree Nut', 'Peanut', 'Wheat', 
                       'Soy', 'Sesame', 'Mustard', 'Gluten', 'Sulphite', 'Corn', 'Celery', 
                       'Lupin', 'Mollusc', 'MSG'];
    
    let html = '';
    allergens.forEach(allergen => {
        const isChecked = state.userProfile.allergens && 
                         state.userProfile.allergens.includes(allergen) ? 'checked' : '';
        const id = `allergen_${allergen.toLowerCase().replace(/\s+/g, '_')}`;
        html += `
            <label class="checkbox-group">
                <input type="checkbox" id="${id}" value="${allergen}" ${isChecked}>
                <label for="${id}">${allergen}</label>
            </label>
        `;
    });
    
    container.innerHTML = html;
}

function populatePreferenceCheckboxes() {
    const container = document.getElementById('preferencesCheckboxes');
    if (!container) return;
    
    const preferences = [
        { key: 'vegan', label: 'Vegan' },
        { key: 'vegetarian', label: 'Vegetarian' },
        { key: 'keto', label: 'Keto' },
        { key: 'diabetic_friendly', label: 'Diabetic Friendly' },
        { key: 'low_sodium', label: 'Low Sodium' },
        { key: 'heart_safe', label: 'Heart Safe' }
    ];
    
    let html = '';
    preferences.forEach(pref => {
        const isChecked = state.userProfile.dietary && 
                         state.userProfile.dietary[pref.key] ? 'checked' : '';
        const id = `pref_${pref.key}`;
        html += `
            <label class="checkbox-group">
                <input type="checkbox" id="${id}" value="${pref.key}" ${isChecked}>
                <label for="${id}">${pref.label}</label>
            </label>
        `;
    });
    
    container.innerHTML = html;
}

// ============ TEXT EXTRACTION FROM LABEL ============
async function extractIngredientsFromText() {
    const labelTextInput = document.getElementById('labelTextInput');
    const labelText = labelTextInput.value.trim();
    
    if (!labelText) {
        showToast('Please paste food label text', 'warning');
        return;
    }
    
    const loadingElement = document.getElementById('textExtractionLoading');
    const errorElement = document.getElementById('textExtractionError');
    
    loadingElement.classList.remove('hidden');
    errorElement.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE_URL}/extract-ingredients-from-text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                label_text: labelText
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Set extracted ingredients to state
            state.extractedText = data.ingredients || [];
            
            loadingElement.classList.add('hidden');
            showToast(`Successfully extracted ${state.extractedText.length} ingredients`, 'success');
            
            // Display the extracted ingredients
            displayExtractedIngredientsList(state.extractedText);
            
            // Scroll to results
            const resultsSection = document.getElementById('resultsSection');
            if (resultsSection) {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
            
        } else {
            loadingElement.classList.add('hidden');
            errorElement.style.display = 'block';
            errorElement.textContent = `Error: ${data.error || 'Failed to extract ingredients'}`;
            showToast('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Text extraction error:', error);
        loadingElement.classList.add('hidden');
        errorElement.style.display = 'block';
        errorElement.textContent = `Error: ${error.message}`;
        showToast('Failed to extract ingredients: ' + error.message, 'error');
    }
}

function displayExtractedIngredientsList(ingredients) {
    const container = document.getElementById('extractedText');
    if (!container) {
        console.warn('Extracted text container not found');
        return;
    }
    
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
}

function clearTextInput() {
    const labelTextInput = document.getElementById('labelTextInput');
    const errorElement = document.getElementById('textExtractionError');
    
    labelTextInput.value = '';
    errorElement.style.display = 'none';
    labelTextInput.focus();
    
    // Clear the extracted text display
    state.extractedText = [];
    const container = document.getElementById('extractedText');
    if (container) {
        container.innerHTML = '<p class="placeholder">Image will appear here after scanning</p>';
    }
}

async function saveAllergens() {
    const checkboxes = document.querySelectorAll('#allergenCheckboxes input[type="checkbox"]:checked');
    const selectedAllergens = Array.from(checkboxes).map(cb => cb.value);
    
    try {
        const response = await fetch(`${API_BASE_URL}/user/${state.userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                allergens: selectedAllergens
            })
        });
        
        const data = await response.json();
        if (data.success) {
            state.userProfile.allergens = selectedAllergens;
            showToast('Allergens saved successfully!');
            toggleEditAllergens();
        } else {
            showToast('Error saving allergens: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Error saving allergens: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

async function savePreferences() {
    const checkboxes = document.querySelectorAll('#preferencesCheckboxes input[type="checkbox"]:checked');
    const selectedPrefs = {};
    
    // Initialize all preferences to false
    const allPrefs = ['vegan', 'vegetarian', 'keto', 'diabetic_friendly', 'low_sodium', 'heart_safe'];
    allPrefs.forEach(pref => selectedPrefs[pref] = false);
    
    // Set selected ones to true
    Array.from(checkboxes).forEach(cb => {
        selectedPrefs[cb.value] = true;
    });
    
    try {
        const response = await fetch(`${API_BASE_URL}/user/${state.userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                dietary_preferences: selectedPrefs
            })
        });
        
        const data = await response.json();
        if (data.success) {
            state.userProfile.dietary = selectedPrefs;
            showToast('Preferences saved successfully!');
            toggleEditPreferences();
        } else {
            showToast('Error saving preferences: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('Error saving preferences: ' + error.message, 'error');
        console.error('Error:', error);
    }
}

function cancelEditAllergens() {
    toggleEditAllergens();
}

function cancelEditPreferences() {
    toggleEditPreferences();
}

// ============ POLYFILLS ============
if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(search, pos) {
        return this.substr(!pos || pos < 0 ? 0 : +pos, search.length) === search;
    };
}
