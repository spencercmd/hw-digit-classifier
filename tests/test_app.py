import unittest
import json
import numpy as np
from app import app
from model import load_and_preprocess_data, create_and_train_model, predict

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        x_train, y_train, _, _ = load_and_preprocess_data()
        self.model = create_and_train_model(x_train, y_train)

    def test_predict_endpoint(self):
        # Generate a random image
        random_image = np.random.rand(784).tolist()
        response = self.app.post('/predict', json={'image_data': random_image})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('predicted_label', data)
        self.assertIsInstance(data['predicted_label'], int)

    def test_predict_endpoint_no_data(self):
        response = self.app.post('/predict', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn('error', data)

    def test_predict_model(self):
        # generate a random image
        random_image = np.random.rand(784)
        prediction = predict(self.model, random_image)
        self.assertIsInstance(prediction, np.int64)
        self.assertGreaterEqual(prediction, 0)
        self.assertLessEqual(prediction, 9)

if __name__ == '__main__':
    unittest.main()