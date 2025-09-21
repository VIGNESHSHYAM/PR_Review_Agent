import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    
    return {
        'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN'),
        'GITLAB_TOKEN': os.environ.get('GITLAB_TOKEN'),
        'GITLAB_URL': os.environ.get('GITLAB_URL', 'https://gitlab.com'),
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
        'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO')
    }