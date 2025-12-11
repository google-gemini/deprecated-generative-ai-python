"""Test script to reproduce and verify the image encoding issue fix"""
import io
import sys
import pathlib

# Add the google directory to the path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import PIL.Image
import PIL.ImageFile
import numpy as np
from google.generativeai.types import content_types

print(f"Python version: {sys.version}")
print(f"PIL/Pillow version: {PIL.__version__}")
print("-" * 60)

# Test 1: RGBA image (most problematic)
print("\n1. Testing RGBA image conversion:")
try:
    rgba_image = PIL.Image.fromarray(np.zeros([6, 6, 4], dtype=np.uint8))
    blob = content_types.image_to_blob(rgba_image)
    print(f"   ✓ Successfully converted RGBA image")
    print(f"     MIME type: {blob.mime_type}")
    print(f"     Data size: {len(blob.data)} bytes")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")

# Test 2: RGB image (should work fine)
print("\n2. Testing RGB image conversion:")
try:
    rgb_image = PIL.Image.fromarray(np.zeros([6, 6, 3], dtype=np.uint8))
    blob = content_types.image_to_blob(rgb_image)
    print(f"   ✓ Successfully converted RGB image")
    print(f"     MIME type: {blob.mime_type}")
    print(f"     Data size: {len(blob.data)} bytes")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")

# Test 3: Palette mode image
print("\n3. Testing Palette (P) mode image conversion:")
try:
    p_image = PIL.Image.fromarray(np.zeros([6, 6, 3], dtype=np.uint8)).convert("P")
    blob = content_types.image_to_blob(p_image)
    print(f"   ✓ Successfully converted P mode image")
    print(f"     MIME type: {blob.mime_type}")
    print(f"     Data size: {len(blob.data)} bytes")
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")

# Test 4: Base64 encoded image (simulating user's approach)
print("\n4. Testing base64 encoding approach (user's original method):")
try:
    import base64
    # Create a test image and save it
    test_img = PIL.Image.fromarray(np.random.randint(0, 255, [100, 100, 3], dtype=np.uint8))
    temp_path = pathlib.Path(__file__).parent / "temp_test_image.png"
    test_img.save(temp_path)
    
    # User's encoding method
    with open(temp_path, 'rb') as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
    
    print(f"   ✓ Successfully encoded image using base64")
    print(f"     Encoded length: {len(encoded)} characters")
    
    # Now test with our library
    opened_img = PIL.Image.open(temp_path)
    blob = content_types.image_to_blob(opened_img)
    print(f"   ✓ Successfully converted opened image via library")
    print(f"     MIME type: {blob.mime_type}")
    print(f"     Data size: {len(blob.data)} bytes")
    
    # Close the image before deleting the file
    opened_img.close()
    # Clean up
    temp_path.unlink()
except Exception as e:
    print(f"   ✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    # Try to clean up even if there was an error
    try:
        if 'temp_path' in locals() and temp_path.exists():
            import time
            time.sleep(0.1)  # Brief pause to allow file handles to close
            temp_path.unlink()
    except:
        pass

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
