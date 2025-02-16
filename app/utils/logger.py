import logging
import sys
from datetime import datetime

# Configure logging
logger = logging.getLogger('app')
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Export logger
__all__ = ['logger'] 