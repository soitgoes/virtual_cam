#!/usr/bin/env python3
"""
Test script to verify the virtual camera installation and dependencies.
"""

import sys
import importlib

def test_imports():
    """Test if all required modules can be imported."""
    required_modules = ['cv2', 'numpy', 'cryptography']
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module} imported successfully")
        except ImportError:
            print(f"✗ {module} import failed")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nMissing modules: {', '.join(missing_modules)}")
        print("Please install them using: pip3 install -r requirements.txt")
        return False
    else:
        print("\n✓ All dependencies are installed correctly!")
        return True

def test_camera_access():
    """Test if camera access works."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Camera access successful")
            cap.release()
            return True
        else:
            print("✗ Camera access failed (camera may be in use or not available)")
            print("  You can still use simulation mode with --simulation flag")
            return False
    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        return False

if __name__ == '__main__':
    print("Virtual Security Camera - Installation Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test camera access
        test_camera_access()
        
        print("\n" + "=" * 50)
        print("Installation test completed!")
        print("You can now run: python3 virtual_camera.py")
        print("Or with simulation mode: python3 virtual_camera.py --simulation")
        print("Note: HTTPS is enabled by default with self-signed certificates")
    else:
        print("\n" + "=" * 50)
        print("Please install missing dependencies first.")
        sys.exit(1)
