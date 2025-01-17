import subprocess
import webbrowser
from pathlib import Path
import time
import logging

def start_tensorboard(logdir="logs/fit", port=6006):
    """
    Start TensorBoard server and open it in the default web browser
    
    Args:
        logdir (str): Directory containing the TensorBoard logs
        port (int): Port to run TensorBoard on
    """
    logging.info(f"Starting TensorBoard server on port {port}")
    
    # Ensure the log directory exists
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    # Start TensorBoard server
    tensorboard = subprocess.Popen(
        ["tensorboard", "--logdir", logdir, "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for TensorBoard to start
    time.sleep(3)
    
    # Open TensorBoard in browser
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    
    logging.info(f"TensorBoard is running at {url}")
    return tensorboard

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Start TensorBoard
    tensorboard_process = start_tensorboard()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        logging.info("Shutting down TensorBoard...")
        tensorboard_process.terminate()
        tensorboard_process.wait() 