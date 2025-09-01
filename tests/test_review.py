#!/usr/bin/env python3
"""
Test script for the review tracking functionality
"""
import requests
import json
import time
import sys

API_ENDPOINT = 'http://127.0.0.1:5001/log'

def check_server():
    """Check if server is running"""
    try:
        response = requests.get('http://127.0.0.1:5001/')
        return True
    except requests.exceptions.ConnectionError:
        return False

# Test data
test_problem = {
    "problem_number": "1",
    "name": "Two Sum", 
    "difficulty": "Easy",
    "url": "https://leetcode.com/problems/two-sum/",
    "topic": "Array, Hash Table",
    "notes": "First submission - basic solution"
}

def test_first_submission():
    """Test first time submitting a problem"""
    print("🧪 Testing first submission...")
    
    response = requests.post(API_ENDPOINT, json=test_problem)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ First submission successful: {result['message']}")
        return True
    else:
        print(f"❌ First submission failed: {response.text}")
        return False

def test_review_submission():
    """Test submitting the same problem again (review)"""
    print("\n🧪 Testing review submission (same problem)...")
    
    # Modify notes for review
    review_data = test_problem.copy()
    review_data["notes"] = "Review submission - optimized solution with hash map"
    
    response = requests.post(API_ENDPOINT, json=review_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Review submission successful: {result['message']}")
        return True
    else:
        print(f"❌ Review submission failed: {response.text}")
        return False

def test_multiple_reviews():
    """Test multiple reviews to see spaced repetition in action"""
    print("\n🧪 Testing multiple reviews...")
    
    for i in range(3):
        review_data = test_problem.copy()
        review_data["notes"] = f"Review #{i+2} - getting better at this!"
        
        print(f"  Submitting review #{i+2}...")
        response = requests.post(API_ENDPOINT, json=review_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Review #{i+2}: {result['message']}")
        else:
            print(f"  ❌ Review #{i+2} failed: {response.text}")
        
        time.sleep(1)  # Small delay between requests

if __name__ == "__main__":
    print("🚀 Testing Review Tracking Functionality")
    print("=" * 50)
    
    # Check if server is running
    if not check_server():
        print("❌ Server is not running on http://127.0.0.1:5001")
        print("Please start the Flask server first: python app.py")
        sys.exit(1)
    
    print("✅ Server is running!")
    
    # Test first submission
    if test_first_submission():
        time.sleep(2)  # Wait a moment
        
        # Test review submission
        if test_review_submission():
            time.sleep(2)  # Wait a moment
            
            # Test multiple reviews
            test_multiple_reviews()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed! Check your Google Sheet for results.")