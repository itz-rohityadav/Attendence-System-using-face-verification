import cv2
import numpy as np
import os
import pickle
from sklearn.neighbors import KNeighborsClassifier
from .detector import detect_face, extract_face, preprocess_face

class FaceRecognizer:
    def __init__(self, model_path=None):
        """
        Initialize the face recognizer
        
        Args:
            model_path: Path to a saved model file (optional)
        """
        if model_path and os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model = KNeighborsClassifier(n_neighbors=5)
            
        self.is_trained = model_path is not None and os.path.exists(model_path)
        
    def train(self, dataset_path, save_path=None):
        """
        Train the face recognizer on a dataset of face images
        
        Args:
            dataset_path: Path to the dataset directory
            save_path: Path to save the trained model (optional)
            
        Returns:
            True if training was successful, False otherwise
        """
        X = []  # Face features
        y = []  # Labels (student IDs)
        
        # Iterate through each student directory
        for student_id in os.listdir(dataset_path):
            student_dir = os.path.join(dataset_path, student_id)
            
            if not os.path.isdir(student_dir):
                continue
                
            # Process each photo for this student
            for photo_file in os.listdir(student_dir):
                if not photo_file.endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                photo_path = os.path.join(student_dir, photo_file)
                image = cv2.imread(photo_path)
                
                if image is None:
                    continue
                
                # Detect face in the photo
                faces = detect_face(image)
                
                if len(faces) == 0:
                    continue
                
                # Use the first detected face
                face = extract_face(image, faces[0])
                
                # Preprocess the face
                processed_face = preprocess_face(face)
                
                # Flatten the face image to a feature vector
                face_vector = processed_face.flatten()
                
                # Add to training data
                X.append(face_vector)
                y.append(student_id)
        
        if len(X) == 0:
            return False
        
        # Train the model
        self.model.fit(X, y)
        self.is_trained = True
        
        # Save the model if requested
        if save_path:
            with open(save_path, 'wb') as f:
                pickle.dump(self.model, f)
        
        return True
    
    def recognize_face(self, image):
        """
        Recognize a face in an image
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            Tuple of (student_id, confidence) or (None, 0) if no face is detected
            or the model is not trained
        """
        if not self.is_trained:
            return None, 0
        
        # Detect face in the image
        faces = detect_face(image)
        
        if len(faces) == 0:
            return None, 0
        
        # Use the first detected face
        face = extract_face(image, faces[0])
        
        # Preprocess the face
        processed_face = preprocess_face(face)
        
        # Flatten the face image to a feature vector
        face_vector = processed_face.flatten().reshape(1, -1)
        
        # Predict the student ID
        student_id = self.model.predict(face_vector)[0]
        
                # Get the confidence score (using distances to neighbors)
        distances, _ = self.model.kneighbors(face_vector)
        confidence = 1.0 / (1.0 + np.mean(distances))
        
        return student_id, confidence

def recognize_face(image, model_path=None):
    """
    Convenience function to recognize a face in an image
    
    Args:
        image: Input image (numpy array)
        model_path: Path to a saved model file (optional)
        
    Returns:
        Tuple of (student_id, confidence) or (None, 0) if no face is detected
        or the model is not trained
    """
    recognizer = FaceRecognizer(model_path)
    return recognizer.recognize_face(image)