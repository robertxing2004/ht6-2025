#!/usr/bin/env python3
"""
MongoDB Setup Script for Battery Monitoring API
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_mongodb_installed():
    """Check if MongoDB is installed"""
    try:
        result = subprocess.run(["mongod", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB is already installed")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ MongoDB is not installed")
    return False

def install_mongodb():
    """Install MongoDB based on the operating system"""
    import platform
    
    system = platform.system().lower()
    
    if system == "windows":
        print("📋 MongoDB installation on Windows:")
        print("1. Download MongoDB Community Server from: https://www.mongodb.com/try/download/community")
        print("2. Run the installer and follow the setup wizard")
        print("3. Add MongoDB to your PATH environment variable")
        print("4. Create data directory: mkdir C:\\data\\db")
        return False
    
    elif system == "darwin":  # macOS
        print("📋 Installing MongoDB on macOS...")
        if run_command("brew --version", "Checking Homebrew"):
            return run_command("brew tap mongodb/brew", "Adding MongoDB tap") and \
                   run_command("brew install mongodb-community", "Installing MongoDB")
        else:
            print("❌ Homebrew not found. Please install Homebrew first: https://brew.sh/")
            return False
    
    elif system == "linux":
        print("📋 Installing MongoDB on Linux...")
        # This is a simplified version - you might need to adjust for your specific Linux distribution
        commands = [
            ("wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -", "Adding MongoDB GPG key"),
            ("echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse' | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list", "Adding MongoDB repository"),
            ("sudo apt-get update", "Updating package list"),
            ("sudo apt-get install -y mongodb-org", "Installing MongoDB")
        ]
        
        for command, description in commands:
            if not run_command(command, description):
                return False
        return True
    
    else:
        print(f"❌ Unsupported operating system: {system}")
        return False

def start_mongodb():
    """Start MongoDB service"""
    import platform
    
    system = platform.system().lower()
    
    if system == "windows":
        print("📋 Starting MongoDB on Windows:")
        print("1. Open Command Prompt as Administrator")
        print("2. Run: net start MongoDB")
        print("3. Or start manually: mongod --dbpath C:\\data\\db")
        return False
    
    elif system == "darwin":  # macOS
        return run_command("brew services start mongodb-community", "Starting MongoDB service")
    
    elif system == "linux":
        return run_command("sudo systemctl start mongod", "Starting MongoDB service")
    
    return False

def create_database():
    """Create the database and collection"""
    print("📋 Creating database and collection...")
    
    # MongoDB connection string
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "battery_monitoring")
    
    # MongoDB shell commands
    commands = f"""
    use {db_name}
    db.createCollection('battery_telemetry')
    db.battery_telemetry.createIndex({{"timestamp": 1}})
    db.battery_telemetry.createIndex({{"source": 1}})
    db.battery_telemetry.createIndex({{"received_at": -1}})
    db.battery_telemetry.createIndex({{"source": 1, "timestamp": -1}})
    print("Database and collection created successfully")
    """
    
    try:
        result = subprocess.run(
            ["mongosh", "--eval", commands],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Database and collection created successfully")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ MongoDB shell (mongosh) not found. Please install MongoDB first.")
        return False
    except subprocess.TimeoutExpired:
        print("❌ MongoDB connection timeout. Is MongoDB running?")
        return False

def main():
    """Main setup function"""
    print("🚀 MongoDB Setup for Battery Monitoring API")
    print("=" * 50)
    
    # Check if MongoDB is installed
    if not check_mongodb_installed():
        print("\n📦 Installing MongoDB...")
        if not install_mongodb():
            print("\n❌ MongoDB installation failed. Please install manually.")
            return False
    
    # Start MongoDB
    print("\n🔄 Starting MongoDB...")
    if not start_mongodb():
        print("\n⚠️  Please start MongoDB manually and run this script again.")
        return False
    
    # Create database
    print("\n🗄️  Setting up database...")
    if not create_database():
        print("\n❌ Database setup failed.")
        return False
    
    print("\n✅ MongoDB setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Install Python dependencies: pip install -r requirements.txt")
    print("2. Start the API: python index.py")
    print("3. Test the API: http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 