import tensorflow as tf
import numpy as np
from datetime import datetime

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

def create_and_train_model(x_train, y_train, epochs=10):
    """Creates and trains a neural network model.

    Args:
        x_train (numpy.array): Training data
        y_train (numpy.array): Training labels
        epochs (int, optional): Number of epochs to train for. Defaults to 10.

    Returns:
        tf.keras.Model: Trained neural network model.
    """
    # Set up TensorBoard logging
    log_dir = "logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
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
    
    return model

def predict(model, image_data):
    """Predicts the label of an input image.

    Args:
        model (tf.keras.Model): Trained neural network model
        image_data (numpy.array): 784-d array representation of image.

    Returns:
        tuple: (predicted label, probabilities for each digit)
    """
    # Ensure the image is properly shaped and normalized
    image_data = np.array(image_data).astype('float32')
    
    # Reshape to match MNIST format (28x28)
    image_data = image_data.reshape(28, 28)
    
    # Add batch and channel dimensions
    image_data = image_data.reshape(1, 28, 28, 1)

    # Get predictions
    predictions = model.predict(image_data, verbose=0)
    predicted_label = np.argmax(predictions[0])
    probabilities = predictions[0].tolist()
    
    return int(predicted_label), probabilities

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