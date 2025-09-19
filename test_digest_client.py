#!/usr/bin/env python3
"""
Test client for Digest Authentication.
"""

import requests
from requests.auth import HTTPDigestAuth
import hashlib
import time

def test_digest_auth():
    """Test digest authentication with the virtual camera server."""
    url = "http://localhost:8081/stream"
    username = "username"
    password = "password"
    
    print("Testing Digest Authentication")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print()
    
    try:
        # Test with requests library (handles digest auth automatically)
        print("Testing with requests library...")
        response = requests.get(url, auth=HTTPDigestAuth(username, password), stream=True, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Digest authentication successful!")
            # Read a few bytes to verify we're getting the stream
            data = next(response.iter_content(chunk_size=1024), b'')
            print(f"Received {len(data)} bytes of stream data")
        else:
            print("❌ Digest authentication failed")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test manual digest auth calculation
    print("Testing manual digest calculation...")
    test_manual_digest()

def test_manual_digest():
    """Test manual digest authentication calculation."""
    username = "username"
    password = "password"
    realm = "Virtual Security Camera"
    method = "GET"
    uri = "/stream"
    nonce = "testnonce123456789"  # This would come from the server
    
    # Calculate expected values
    ha1 = hashlib.md5(f"{username}:{realm}:{password}".encode()).hexdigest()
    ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
    response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
    
    print(f"HA1: {ha1}")
    print(f"HA2: {ha2}")
    print(f"Response: {response}")
    print(f"Expected Authorization header:")
    print(f'Authorization: Digest username="{username}", realm="{realm}", nonce="{nonce}", uri="{uri}", response="{response}"')

if __name__ == '__main__':
    test_digest_auth()
