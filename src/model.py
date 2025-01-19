import tensorflow as tf
import numpy as np
from datetime import datetime
import os
from pathlib import Path
import logging

MODEL_PATH = Path("models/digit_classifier")

def load_and_preprocess_data():
    """Loads and preprocesses the MNIST dataset.

    Returns:
        tuple: A tuple containing the training data (x_train, y_train), the testing data (x_test, y_test)
    """
    # Load the MNIST dataset
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

    # Add channel dimension and normalize
    x_train = x_train.reshape((60000, 28, 28, 1)).astype('float32') / 255
    x_test = x_test.reshape((10000, 28, 28, 1)).astype('float32') / 255

    return x_train, y_train, x_test, y_test

def create_and_train_model(x_train, y_train, epochs=10, save_model=True):
    """Creates and trains a neural network model.

    Args:
        x_train (numpy.array): Training data
        y_train (numpy.array): Training labels
        epochs (int, optional): Number of epochs to train for. Defaults to 10.
        save_model (bool, optional): Whether to save the model after training. Defaults to True.

    Returns:
        tf.keras.Model: Trained neural network model.
    """
    # Set up TensorBoard logging with configurable directory
    log_dir = os.getenv('TENSORBOARD_LOG_DIR', 'logs/fit/') + datetime.now().strftime("%Y%m%d-%H%M%S")
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=log_dir,
        histogram_freq=1,
        write_graph=True,
        write_images=True,
        update_freq='epoch'
    )

    # Build the CNN model
    model = tf.keras.Sequential([
        # First Convolutional Block
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(28, 28, 1)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Second Convolutional Block
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Dropout(0.25),
        
        # Flatten and Dense Layers
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Dense(10, activation='softmax')
    ])

    # Compile the model
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    # Train the model with TensorBoard callback
    model.fit(
        x_train, 
        y_train, 
        epochs=epochs, 
        batch_size=128,
        validation_split=0.2,
        callbacks=[tensorboard_callback],
        verbose=1
    )
    
    if save_model:
        save_trained_model(model)
    
    return model

def save_trained_model(model):
    """Saves the trained model to disk.

    Args:
        model (tf.keras.Model): The trained model to save
    """
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)

def load_trained_model():
    """Loads a trained model from disk.

    Returns:
        tf.keras.Model: The loaded model, or None if no saved model exists
    """
    if MODEL_PATH.exists():
        return tf.keras.models.load_model(MODEL_PATH)
    return None

def predict(model, image_data):
    """Predicts the label of an input image.

    Args:
        model (tf.keras.Model): Trained neural network model
        image_data (numpy.array): 784-d array representation of image.

    Returns:
        tuple: (predicted label, probabilities for each digit)
    """
    try:
        # Convert input to numpy array and normalize
        image_data = np.array(image_data, dtype='float32')
        if image_data.max() > 1.0:
            image_data /= 255.0
        
        # Reshape to match MNIST format (28x28)
        if image_data.shape != (28, 28):
            image_data = image_data.reshape(28, 28)
        
        # Add batch and channel dimensions
        image_data = image_data.reshape(1, 28, 28, 1)

        # Get predictions
        predictions = model.predict(image_data, verbose=0)
        
        # Ensure predictions is a numpy array
        predictions = np.array(predictions)
        predicted_label = int(np.argmax(predictions[0]))
        
        # Convert to Python list of floats
        probabilities = [float(p) for p in predictions[0]]
        
        return predicted_label, probabilities
        
    except Exception as e:
        logging.error(f"Error in predict function: {str(e)}")
        # Return a safe default in case of error
        return 0, [0.0] * 10

if __name__ == '__main__':
    x_train, y_train, x_test, y_test = load_and_preprocess_data()
    model = create_and_train_model(x_train, y_train)
    print("Model trained and ready to predict.")
    
    # Evaluate the model
    test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
    print(f"Test accuracy: {test_accuracy:.4f}")
    
    # example prediction
    example_image = x_test[0]
    prediction, probs = predict(model, example_image.reshape(28, 28))
    print("Example Prediction:", prediction)
    print("Actual Label:", y_test[0])
    print("Probabilities:", probs)