#!/usr/bin/env python3
"""
Environment Setup Script for Battery Monitoring System
This script helps you configure the necessary environment variables.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with the necessary environment variables"""
    
    env_content = """# MongoDB Atlas Connection String
# Replace with your actual MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/battery_db?retryWrites=true&w=majority

# Database Configuration
DATABASE_NAME=battery_db

# Google Gemini AI API Key
# Get your API key from: https://makersuite.google.com/app/apikey
# This is required for AI-powered battery predictions
GEMINI_API_KEY=your_gemini_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Backend Configuration
BACKEND_URL=http://localhost:8000
"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def get_gemini_api_key():
    """Get Gemini API key from user input"""
    print("\n🔑 Google Gemini API Key Setup")
    print("=" * 40)
    print("To use AI-powered battery predictions, you need a Gemini API key.")
    print("1. Visit: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated API key")
    print()
    
    api_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if api_key:
        return api_key
    else:
        print("⚠️  No API key provided. AI predictions will use analytical mode only.")
        return ""

def update_env_file(api_key=""):
    """Update the .env file with the provided API key"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found. Run setup first.")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        if api_key:
            # Replace placeholder with actual API key
            content = content.replace("GEMINI_API_KEY=your_gemini_api_key_here", f"GEMINI_API_KEY={api_key}")
        else:
            # Comment out the API key line
            content = content.replace("GEMINI_API_KEY=your_gemini_api_key_here", "# GEMINI_API_KEY=your_gemini_api_key_here")
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        if api_key:
            print("✅ Gemini API key configured successfully!")
        else:
            print("✅ API key disabled. Using analytical mode only.")
        
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def check_requirements():
    """Check if all required packages are installed"""
    print("\n📦 Checking Requirements")
    print("=" * 30)
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'motor',
        'pymongo',
        'pydantic',
        'python-dotenv',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages are installed!")
        return True

def main():
    """Main setup function"""
    print("🚀 Battery Monitoring System Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install missing packages before continuing.")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Get API key
    api_key = get_gemini_api_key()
    
    # Update .env file
    if not update_env_file(api_key):
        sys.exit(1)
    
    print("\n🎉 Setup Complete!")
    print("=" * 20)
    print("Next steps:")
    print("1. Edit .env file with your MongoDB connection string")
    print("2. Start the backend: uvicorn main:app --reload")
    print("3. Test the system with your QNX monitor")
    
    if api_key:
        print("\n✅ AI predictions are enabled!")
    else:
        print("\n⚠️  AI predictions are disabled. Edit .env file to add your API key later.")

if __name__ == "__main__":
    main() 