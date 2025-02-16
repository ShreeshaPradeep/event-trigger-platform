import logging
import sys
import os
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console handler
        logging.FileHandler(
            os.path.join(logs_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
        )  # File handler
    ]
)

# Create logger
logger = logging.getLogger(__name__) 