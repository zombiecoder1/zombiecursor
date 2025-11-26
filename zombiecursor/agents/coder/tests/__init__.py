"""
Test configuration for the Coder Agent.
"""
import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['TESTING'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'