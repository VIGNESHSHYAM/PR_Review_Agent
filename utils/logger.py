import logging
import sys
from typing import Optional

def setup_logger(level: Optional[str] = None):
    """Set up logging configuration"""
    log_level = getattr(logging, level or 'INFO', logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pr_review_agent.log')
        ]
    )
    
    return get_logger()

def get_logger(name: str = 'PRReviewAgent'):
    """Get a logger instance"""
    return logging.getLogger(name)