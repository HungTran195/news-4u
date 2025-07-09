#!/usr/bin/env python3
"""
PostgreSQL database setup script.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Set up PostgreSQL database and run migrations."""
    print("🚀 Setting up News 4U PostgreSQL database...")
    
    # Check if PostgreSQL is running
    if not run_command("pg_isready -h localhost", "Checking PostgreSQL connection"):
        print("❌ PostgreSQL is not running or not accessible")
        print("Please start PostgreSQL and try again")
        sys.exit(1)
    
    # Create database if it doesn't exist
    if not run_command("createdb -h localhost -U postgres news_4u", "Creating database"):
        print("⚠️  Database might already exist, continuing...")
    
    # Initialize Alembic (if not already done)
    if not os.path.exists("alembic/versions"):
        if not run_command("alembic init alembic", "Initializing Alembic"):
            print("❌ Failed to initialize Alembic")
            sys.exit(1)
    
    # Run database migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        print("❌ Failed to run migrations")
        sys.exit(1)
    
    # Initialize with RSS feeds
    if not run_command("python scripts/init_db.py", "Initializing RSS feeds"):
        print("❌ Failed to initialize RSS feeds")
        sys.exit(1)
    
    print("\n🎉 PostgreSQL database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend: uvicorn main:app --reload")
    print("2. Or use Docker: docker-compose up --build")
    print("\nDatabase connection details:")
    print("- Host: localhost")
    print("- Port: 5432")
    print("- Database: news_4u")
    print("- User: postgres")
    print("- Password: password")


if __name__ == "__main__":
    main() 