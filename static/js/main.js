// Global variables
let videoStream = null;
let captureInterval = null;
let recognitionInProgress = false;

// Initialize camera
async function initCamera(videoElement) {
    try {
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: "user"
            }
        };
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        videoElement.srcObject = stream;
        videoStream = stream;
        
        return true;
    } catch (err) {
        console.error("Error accessing camera:", err);
        return false;
    }
}

// Stop camera
function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
}

// Capture image from video
function captureImage(videoElement, canvasElement) {
    const context = canvasElement.getContext('2d');
    
    // Set canvas dimensions to match video
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    
    // Get image data as base64 string
    return canvasElement.toDataURL('image/jpeg');
}

// Start face recognition
function startFaceRecognition(videoElement, canvasElement, callback, interval = 1000) {
    // Stop any existing capture interval
    if (captureInterval) {
        clearInterval(captureInterval);
    }
    
    // Start new capture interval
    captureInterval = setInterval(() => {
        if (recognitionInProgress) {
            return;
        }
        
        recognitionInProgress = true;
        
        // Capture image
        const imageData = captureImage(videoElement, canvasElement);
        
        // Process image (send to server for recognition)
        processImage(imageData, (result) => {
            recognitionInProgress = false;
            
            if (callback) {
                callback(result);
            }
        });
    }, interval);
}

// Process image for face recognition
function processImage(imageData, callback) {
    // Send image to server for processing
    fetch('/process_image', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image_data: imageData }),
    })
    .then(response => response.json())
    .then(data => {
        if (callback) {
            callback(data);
        }
    })
    .catch((error) => {
        console.error('Error processing image:', error);
        if (callback) {
            callback({ success: false, error: 'Failed to process image' });
        }
    });
}

// Mark attendance
function markAttendance(studentId, section, method = 'face', reason = null, requiresAuth = false, adminPassword = null) {
    const data = {
        student_id: studentId,
        section: section,
        method: method,
        requires_auth: requiresAuth
    };
    
    if (reason) {
        data.reason = reason;
    }
    
    if (adminPassword) {
        data.admin_password = adminPassword;
    }
    
    // Determine which endpoint to use
    const endpoint = method === 'face' ? '/process_attendance' : '/process_manual_attendance';
    
    // Send attendance data to server
    return fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json());
}

// Format date and time
function formatDate(date) {
    return date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Add any initialization code here
    console.log('Attendance System initialized');
});