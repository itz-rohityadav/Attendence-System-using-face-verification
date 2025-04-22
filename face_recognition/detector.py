import cv2
import numpy as np
import os

# Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_face(image):
    """
    Detect faces in an image and return the face regions
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        List of face regions (x, y, w, h)
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    return faces

def extract_face(image, face_region, target_size=(224, 224)):
    """
    Extract a face from an image and resize to target size
    
    Args:
        image: Input image (numpy array)
        face_region: Face region (x, y, w, h)
        target_size: Target size for the extracted face
        
    Returns:
        Extracted and resized face image
    """
    x, y, w, h = face_region
    face = image[y:y+h, x:x+w]
    face = cv2.resize(face, target_size)
    return face

def preprocess_face(face):
    """
    Preprocess a face image for recognition
    
    Args:
        face: Face image (numpy array)
        
    Returns:
        Preprocessed face image
    """
    # Convert to grayscale
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization
    equalized = cv2.equalizeHist(gray)
    
    # Normalize pixel values
    normalized = equalized / 255.0
    
    return normalized