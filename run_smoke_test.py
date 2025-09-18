#!/usr/bin/env python3
"""
Smoke Test Runner for Copilot Platform
Run this to test the end-to-end pipeline
"""

import asyncio
import httpx
import sys
import time
from typing import Dict, Any


async def test_llm_pipeline() -> bool:
    """Test the LLM pipeline end-to-end"""
    print("🧪 Running LLM Pipeline Smoke Test...")
    
    # Test configuration
    base_url = "http://localhost:8000"
    test_prompt = "Summarize this case law"
    test_model = "local"
    
    payload = {
        "text": test_prompt,
        "provider": "local",
        "model": test_model,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"📡 Sending request to {base_url}/llm/query")
            print(f"📝 Prompt: '{test_prompt}'")
            print(f"🤖 Model: {test_model}")
            
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["response", "model", "provider"]
                for field in required_fields:
                    if field not in data:
                        print(f"❌ Missing required field: {field}")
                        return False
                
                # Check model and provider
                if data["model"] != test_model:
                    print(f"❌ Wrong model: expected '{test_model}', got '{data['model']}'")
                    return False
                
                if data["provider"] != "local":
                    print(f"❌ Wrong provider: expected 'local', got '{data['provider']}'")
                    return False
                
                # Check response content
                response_text = data["response"]
                if "Local model placeholder" not in response_text:
                    print("❌ Response doesn't contain expected 'Local model placeholder'")
                    print(f"📄 Actual response: {response_text[:200]}...")
                    return False
                
                if test_prompt not in response_text:
                    print(f"❌ Response doesn't contain original prompt '{test_prompt}'")
                    return False
                
                print("✅ LLM Pipeline Test PASSED!")
                print(f"📄 Response preview: {response_text[:150]}...")
                return True
                
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to FastAPI agent")
        print("💡 Start the agent with: python agent/app.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


async def test_health_check() -> bool:
    """Test health check endpoint"""
    print("\n🏥 Testing health check endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print("✅ Health check PASSED!")
                    return True
                else:
                    print(f"❌ Health check failed: {data}")
                    return False
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to FastAPI agent")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_providers_endpoint() -> bool:
    """Test LLM providers endpoint"""
    print("\n🔧 Testing LLM providers endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/llm/providers")
            
            if response.status_code == 200:
                data = response.json()
                expected_providers = ["local", "openai", "gemini", "onprem"]
                
                providers = data.get("providers", {})
                for provider in expected_providers:
                    if provider not in providers:
                        print(f"❌ Missing provider: {provider}")
                        return False
                
                print("✅ Providers endpoint PASSED!")
                print(f"📋 Available providers: {list(providers.keys())}")
                return True
            else:
                print(f"❌ Providers endpoint failed: HTTP {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to FastAPI agent")
        return False
    except Exception as e:
        print(f"❌ Providers endpoint error: {e}")
        return False


async def run_all_tests() -> bool:
    """Run all smoke tests"""
    print("🚀 Starting Copilot Platform Smoke Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("LLM Providers", test_providers_endpoint),
        ("LLM Pipeline", test_llm_pipeline),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Pipeline is working correctly.")
        return True
    else:
        print("⚠️  Some tests FAILED. Check the output above.")
        return False


def main():
    """Main entry point"""
    print("Copilot Platform Smoke Test Runner")
    print("This will test the end-to-end LLM pipeline")
    print()
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
