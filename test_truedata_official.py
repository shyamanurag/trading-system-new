#!/usr/bin/env python3
"""
Test TrueData Integration with Official SDK
"""

import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_truedata_import():
    """Test if TrueData can be imported"""
    try:
        from truedata import TD_live
        logger.info("✅ TrueData library imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ TrueData import failed: {e}")
        logger.error("💡 Install with: pip install truedata")
        return False

def test_credentials():
    """Test if TrueData credentials are available"""
    username = os.getenv('TRUEDATA_USERNAME')
    password = os.getenv('TRUEDATA_PASSWORD')
    
    if username and password:
        logger.info("✅ TrueData credentials found in environment")
        return True
    else:
        logger.error("❌ TrueData credentials not found!")
        logger.error("Please set environment variables:")
        logger.error("  TRUEDATA_USERNAME=your_username")
        logger.error("  TRUEDATA_PASSWORD=your_password")
        return False

async def test_truedata_client():
    """Test the TrueData client integration"""
    try:
        from src.data.truedata_client import init_truedata_client, get_truedata_client
        
        logger.info("🔍 Testing TrueData client initialization...")
        
        # Initialize client
        client = await init_truedata_client()
        
        if client:
            logger.info("✅ TrueData client initialized successfully")
            
            # Test subscription
            symbols = ['NIFTY', 'BANKNIFTY']
            success = await client.subscribe_symbols(symbols)
            
            if success:
                logger.info("✅ Symbol subscription successful")
                
                # Test data retrieval
                data = client.get_market_data('NIFTY')
                if data:
                    logger.info("✅ Market data retrieval successful")
                else:
                    logger.info("⚠️  No market data yet (normal during market closed hours)")
                
                # Clean up
                await client.disconnect()
                logger.info("✅ TrueData client disconnected")
                return True
            else:
                logger.error("❌ Symbol subscription failed")
                return False
        else:
            logger.error("❌ TrueData client initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ TrueData client test failed: {e}")
        return False

def test_standalone_script():
    """Test the standalone script structure"""
    try:
        # Check if standalone script exists
        if os.path.exists('truedata_standalone.py'):
            logger.info("✅ Standalone script exists")
            
            # Check if it can be imported (syntax check)
            import importlib.util
            spec = importlib.util.spec_from_file_location("truedata_standalone", "truedata_standalone.py")
            module = importlib.util.module_from_spec(spec)
            
            # This will raise an error if there are syntax issues
            spec.loader.exec_module(module)
            
            logger.info("✅ Standalone script syntax is valid")
            return True
        else:
            logger.error("❌ Standalone script not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Standalone script test failed: {e}")
        return False

def main():
    """Run all TrueData tests"""
    logger.info("🚀 Testing TrueData Integration (Official SDK)")
    logger.info("=" * 60)
    
    tests = [
        ("TrueData Import", test_truedata_import),
        ("Credentials Check", test_credentials),
        ("Standalone Script", test_standalone_script),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Async test
    logger.info(f"\n🔍 Running: TrueData Client Integration")
    try:
        result = asyncio.run(test_truedata_client())
        results.append(("TrueData Client Integration", result))
    except Exception as e:
        logger.error(f"❌ TrueData Client Integration failed with exception: {e}")
        results.append(("TrueData Client Integration", False))
    
    # Summary
    logger.info(f"\n📊 Test Results:")
    logger.info("=" * 40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n📈 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! TrueData integration is ready.")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Set your TrueData credentials")
        logger.info("   2. Run: python truedata_standalone.py")
        logger.info("   3. Check the generated JSON files")
    else:
        logger.error("❌ Some tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 