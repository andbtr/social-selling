#!/usr/bin/env python3
"""
Test script for the Social Listening Platform API

This script demonstrates the basic functionality of the platform:
1. Starting the server
2. Testing health endpoints
3. Ingesting data from different platforms
4. Querying and filtering comments
"""

import requests
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def test_health_endpoints():
    """Test health check endpoints."""
    print("🔍 Testing health endpoints...")
    
    # Test root endpoint
    response = requests.get(f"{BASE_URL}/")
    print(f"  ✓ Root endpoint: {response.json()}")
    
    # Test health endpoint
    response = requests.get(f"{BASE_URL}/health")
    print(f"  ✓ Health endpoint: {response.json()}")
    print()


def test_ingestion():
    """Test data ingestion from different platforms."""
    print("📥 Testing data ingestion...")
    
    # Test Meta ingestion
    print("  Testing Meta ingestion...")
    response = requests.post(f"{BASE_URL}/ingest/meta/test_post_123")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Ingested {len(data)} comment(s) from Meta")
    
    # Test X ingestion
    print("  Testing X (Twitter) ingestion...")
    response = requests.post(f"{BASE_URL}/ingest/x/test_tweet_456")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Ingested {len(data)} reply(ies) from X")
    
    # Test TripAdvisor ingestion
    print("  Testing TripAdvisor ingestion...")
    response = requests.post(f"{BASE_URL}/ingest/tripadvisor/test_location_789")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Ingested {len(data)} review(s) from TripAdvisor")
    print()


def test_comment_queries():
    """Test comment querying and filtering."""
    print("📊 Testing comment queries...")
    
    # Get all comments
    response = requests.get(f"{BASE_URL}/comments/")
    data = response.json()
    print(f"  ✓ Total comments: {data['total']}")
    
    # Filter by platform
    for platform in ['meta', 'x', 'tripadvisor']:
        response = requests.get(f"{BASE_URL}/comments/?platform={platform}")
        data = response.json()
        print(f"  ✓ {platform.upper()}: {data['total']} comment(s)")
    
    # Get specific comment
    response = requests.get(f"{BASE_URL}/comments/1")
    if response.status_code == 200:
        comment = response.json()
        print(f"  ✓ Retrieved comment #1: {comment['content'][:50]}...")
    print()


def main():
    """Main test function."""
    print("=" * 60)
    print("🚀 Social Listening Platform - Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Wait for server to be ready
        print("⏳ Waiting for server to start...")
        max_retries = 10
        for i in range(max_retries):
            try:
                requests.get(f"{BASE_URL}/health", timeout=1)
                print("✅ Server is ready!\n")
                break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    print("❌ Server not responding. Please start it with: uvicorn main:app")
                    sys.exit(1)
                time.sleep(1)
        
        # Run tests
        test_health_endpoints()
        test_ingestion()
        test_comment_queries()
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
        print()
        print("📚 Next steps:")
        print("  1. Visit http://localhost:8000/docs for interactive API documentation")
        print("  2. Configure real API credentials in .env file")
        print("  3. Implement actual API calls in app/services/ingestion_service.py")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
