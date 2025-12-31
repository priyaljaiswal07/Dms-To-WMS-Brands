#!/usr/bin/env python3
"""
Quick test script to verify the processors work correctly
"""
import sys
import os

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    try:
        from hul_processor import process_hul_sales
        print("✅ HUL processor imported successfully")
    except Exception as e:
        print(f"❌ HUL processor import failed: {e}")
        return False
    
    try:
        from unicharm_processor import process_unicharm_sales
        print("✅ Unicharm processor imported successfully")
    except Exception as e:
        print(f"❌ Unicharm processor import failed: {e}")
        return False
    
    try:
        from britannia_processor import process_britannia_sales
        print("✅ Britannia processor imported successfully")
    except Exception as e:
        print(f"❌ Britannia processor import failed: {e}")
        return False
    
    try:
        from marico_processor import process_marico_sales
        print("✅ Marico processor imported successfully")
    except Exception as e:
        print(f"❌ Marico processor import failed: {e}")
        return False
    
    try:
        import streamlit
        print(f"✅ Streamlit imported successfully (version: {streamlit.__version__})")
    except Exception as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    return True

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("\nTesting dependencies...")
    dependencies = [
        'pandas', 'numpy', 'fuzzywuzzy', 'openpyxl', 'xlrd', 'tqdm'
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} is installed")
        except ImportError:
            print(f"❌ {dep} is NOT installed")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("=" * 50)
    print("DMS Bulk Upload Web App - Test Script")
    print("=" * 50)
    
    deps_ok = test_dependencies()
    imports_ok = test_imports()
    
    print("\n" + "=" * 50)
    if deps_ok and imports_ok:
        print("✅ All tests passed! You can run the app with:")
        print("   streamlit run app.py")
    else:
        print("❌ Some tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
    print("=" * 50)


