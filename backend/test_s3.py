#!/usr/bin/env python3
"""
Test script to verify S3 connectivity and basic operations.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.s3_service import S3Service

def test_s3_connectivity():
    """Test S3 connectivity and basic operations."""
    print("🔍 Testing S3 connectivity and basic operations...")
    
    try:
        # Initialize S3 service
        s3_service = S3Service()
        print("✅ S3Service initialized successfully")
        
        # Test bucket access
        bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        if not bucket_name:
            print("❌ AWS_S3_BUCKET_NAME not found in environment variables")
            return False
        
        print(f"📦 Using S3 bucket: {bucket_name}")
        
        # Test basic operations
        print("\n🧪 Testing basic S3 operations...")
        
        # Test RSS feeds operations
        feeds = s3_service.get_rss_feeds()
        print(f"✅ Retrieved {len(feeds)} RSS feeds")
        
        # Test articles operations
        articles_data = s3_service.get_all_articles(limit=5)
        print(f"✅ Retrieved {len(articles_data['articles'])} articles (total: {articles_data['total']})")
        
        # Test logs operations
        logs = s3_service.get_fetch_logs(limit=5)
        print(f"✅ Retrieved {len(logs)} fetch logs")
        
        # Test stats operations
        stats = s3_service.get_stats()
        print(f"✅ Retrieved stats: {stats['total_articles']} articles, {stats['total_feeds']} feeds")
        
        print("\n🎉 All S3 operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing S3 operations: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_S3_BUCKET_NAME',
        'AWS_REGION'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * len(value)} (hidden)")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    print("🚀 News 4U v2 - S3 Integration Test")
    print("=" * 50)
    
    # Test environment variables
    if not test_environment_variables():
        sys.exit(1)
    
    # Test S3 connectivity
    if not test_s3_connectivity():
        sys.exit(1)
    
    print("\n🎯 All tests passed! S3 integration is working correctly.")
    print("You can now start the News 4U v2 application.") 