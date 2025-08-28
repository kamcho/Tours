#!/usr/bin/env python3
"""
Test script to check database connection to PythonAnywhere MySQL
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travelske.settings')

# Setup Django
django.setup()

# Test database connection
from django.db import connection
from django.core.management import execute_from_command_line

def test_connection():
    try:
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful! Result: {result}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    test_connection()
