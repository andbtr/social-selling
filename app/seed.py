import sys
import os

# Add project root to the Python path to allow imports from 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.seeders import run_all

if __name__ == "__main__":
    run_all()
