import os
import sys
import logging

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import load_and_preprocess_data, create_and_train_model

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Loading MNIST data...")
        x_train, y_train, x_test, y_test = load_and_preprocess_data()
        
        logger.info("Training model...")
        model = create_and_train_model(x_train, y_train, epochs=10, save_model=True)
        
        # Evaluate the model
        test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=1)
        logger.info(f"Test accuracy: {test_accuracy:.4f}")
        
        logger.info("Model training completed and saved successfully")
        return 0
    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 