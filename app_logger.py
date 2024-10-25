# logger_setup.py (a separate file)
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Ensure the _logs directory exists
logs_dir = os.path.abspath('_logs')

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Create a log file with the format log_yyyymmdd.txt
log_filename = f"log_{datetime.now().strftime('%Y%m%d')}.txt"
log_filepath = os.path.join(logs_dir, log_filename)

# Configure the TimedRotatingFileHandler
handler = TimedRotatingFileHandler(
    log_filepath,
    when="D",    # Rotate every day
    interval=1,  # Interval of rotation
    backupCount=30  # Keep logs for 30 days
)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        handler,
        logging.StreamHandler()
    ]
)

# Global logger object
logger = logging.getLogger(__name__)
