import tensorflow as tf
from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import GlobalAveragePooling2D, Dropout, Dense
from tensorflow.keras.models import Model
import cv2
import dlib
import numpy as np
import os

# Function to preprocess a single frame
def preprocess_frame(frame):
    detector = dlib.get_frontal_face_detector()
    faces = detector(frame)
    if len(faces) > 0:
        x, y, w, h = faces[0].left(), faces[0].top(), faces[0].width(), faces[0].height()
        frame = frame[y:y+h, x:x+w]  # Crop the face
    frame = cv2.resize(frame, (299, 299))  # Resize to 299x299
    frame = frame.astype('float32') / 255.0  # Normalize pixel values
    return frame

# Function to load and preprocess a video
def load_and_preprocess_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    original_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        original_frames.append(frame)
        frame = preprocess_frame(frame)
        frames.append(frame)
    cap.release()
    return np.array(frames), original_frames

# Function to build the model
def build_model():
    base_model = Xception(weights='imagenet', include_top=False, input_shape=(299, 299, 3))
    x = GlobalAveragePooling2D()(base_model.output)
    x = Dropout(0.5)(x)
    x = Dense(1024, activation='relu')(x)
    x = Dropout(0.5)(x)
    predictions = Dense(1, activation='sigmoid')(x)  # Binary classification (Real or Fake)
    model = Model(inputs=base_model.input, outputs=predictions)
    
    # Compile the model
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Function to save and display real and fake face images
def save_and_display_face_images(original_frames, predictions, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for i, (frame, prediction) in enumerate(zip(original_frames, predictions)):
        label = 'Fake' if prediction > 0.5 else 'Real'
        output_path = os.path.join(output_dir, f"{label}_frame_{i+1}.jpg")
        cv2.imwrite(output_path, frame)
        
        # Display the image
        cv2.imshow(f"{label}_frame_{i+1}", frame)
        cv2.waitKey(500)  # Display each image for 500ms (adjust as needed)
    
    # Close all OpenCV windows
    cv2.destroyAllWindows()
    print(f"Saved face images to {output_dir}")

# Function to display side-by-side videos if fake
def display_side_by_side(original_frames, predictions):
    for i, (frame, prediction) in enumerate(zip(original_frames, predictions)):
        if prediction > 0.5:  # If the frame is classified as fake
            # Create a side-by-side comparison
            comparison_frame = np.hstack((frame, frame))
            cv2.putText(comparison_frame, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(comparison_frame, "Fake", (frame.shape[1] + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.imshow(f"Comparison Frame {i+1}", comparison_frame)
            cv2.waitKey(500)  # Display each comparison for 500ms (adjust as needed)
    
    # Close all OpenCV windows
    cv2.destroyAllWindows()

# Function to detect if the video is real or fake
def detect_deepfake(video_path, model):
    frames, original_frames = load_and_preprocess_video(video_path)
    predictions = model.predict(frames)
    avg_prediction = np.mean(predictions)
    
    # Save and display face images
    output_dir = os.path.join("output_faces", os.path.basename(video_path).split('.')[0])
    save_and_display_face_images(original_frames, predictions, output_dir)
    
    # If the video is classified as fake, display side-by-side comparisons
    if avg_prediction > 0.5:
        display_side_by_side(original_frames, predictions)
        return "Fake"
    else:
        return "Real"

# Main workflow to load a video and detect if it's real or fake
if __name__ == "__main__":
    model = build_model()
    
    # Load your pre-trained weights here, for example:
    # model.load_weights('path_to_trained_model_weights.h5')

    while True:
        video_path = input("Enter the path to the video file (or 'exit' to quit): ")
        if video_path.lower() == 'exit':
            break
        try:
            result = detect_deepfake(video_path, model)
            print(f"The video is: {result}")
        except Exception as e:
            print(f"An error occurred: {e}. Please try again with a valid video file.")