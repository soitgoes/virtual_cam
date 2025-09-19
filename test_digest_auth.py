#!/usr/bin/env python3
"""
Test script to verify Digest Authentication implementation.
"""

import hashlib
import base64

def test_digest_auth():
    """Test the digest authentication calculation."""
    username = "username"
    password = "password"
    realm = "Virtual Security Camera"
    method = "GET"
    uri = "/stream"
    nonce = "testnonce123456789"
    
    print("Testing Digest Authentication Calculation")
    print("=" * 50)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Realm: {realm}")
    print(f"Method: {method}")
    print(f"URI: {uri}")
    print(f"Nonce: {nonce}")
    print()
    
    # Calculate HA1
    ha1_string = f"{username}:{realm}:{password}"
    ha1 = hashlib.md5(ha1_string.encode()).hexdigest()
    print(f"HA1 string: {ha1_string}")
    print(f"HA1: {ha1}")
    print()
    
    # Calculate HA2
    ha2_string = f"{method}:{uri}"
    ha2 = hashlib.md5(ha2_string.encode()).hexdigest()
    print(f"HA2 string: {ha2_string}")
    print(f"HA2: {ha2}")
    print()
    
    # Calculate response (without qop)
    response_string = f"{ha1}:{nonce}:{ha2}"
    response = hashlib.md5(response_string.encode()).hexdigest()
    print(f"Response string (no qop): {response_string}")
    print(f"Response (no qop): {response}")
    print()
    
    # Calculate response (with qop=auth)
    nc = "00000001"
    cnonce = "clientnonce123"
    response_string_qop = f"{ha1}:{nonce}:{nc}:{cnonce}:auth:{ha2}"
    response_qop = hashlib.md5(response_string_qop.encode()).hexdigest()
    print(f"Response string (qop=auth): {response_string_qop}")
    print(f"Response (qop=auth): {response_qop}")
    print()
    
    print("Expected Authorization header (no qop):")
    print(f'Authorization: Digest username="{username}", realm="{realm}", nonce="{nonce}", uri="{uri}", response="{response}"')
    print()
    
    print("Expected Authorization header (qop=auth):")
    print(f'Authorization: Digest username="{username}", realm="{realm}", nonce="{nonce}", uri="{uri}", qop=auth, nc={nc}, cnonce="{cnonce}", response="{response_qop}"')

if __name__ == '__main__':
    test_digest_auth()
