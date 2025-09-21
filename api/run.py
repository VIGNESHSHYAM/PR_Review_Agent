
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting PR Review Agent API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
