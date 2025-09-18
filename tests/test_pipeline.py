"""
End-to-End Pipeline Tests
Smoke tests for the complete copilot platform pipeline
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TestLLMPipeline:
    """Test LLM pipeline end-to-end"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for the FastAPI agent"""
        return "http://localhost:8000"
    
    @pytest.fixture
    async def client(self):
        """HTTP client for making requests"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_llm_query_local_model(self, client, base_url):
        """
        Test LLM query with local model
        Simulate sending text "Summarize this case law" via FastAPI /llm/query
        Model = "local"
        Expect response to contain "Local model placeholder"
        """
        # Test data
        test_prompt = "Summarize this case law"
        test_model = "local"
        
        # Prepare request payload
        payload = {
            "text": test_prompt,
            "provider": "local",
            "model": test_model,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            # Make request to FastAPI endpoint
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Assert response status
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            
            # Parse response
            response_data = response.json()
            
            # Assert response structure
            assert "response" in response_data, "Response should contain 'response' field"
            assert "model" in response_data, "Response should contain 'model' field"
            assert "provider" in response_data, "Response should contain 'provider' field"
            
            # Assert model and provider
            assert response_data["model"] == test_model, f"Expected model '{test_model}', got '{response_data['model']}'"
            assert response_data["provider"] == "local", f"Expected provider 'local', got '{response_data['provider']}'"
            
            # Assert response content contains expected placeholder
            response_text = response_data["response"]
            assert "Local model placeholder" in response_text, f"Expected 'Local model placeholder' in response, got: {response_text}"
            
            # Assert response contains the original prompt
            assert test_prompt in response_text, f"Expected original prompt '{test_prompt}' in response"
            
            logger.info(f"✅ LLM query test passed. Response: {response_text[:100]}...")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running. Start with: python agent/app.py")
        except Exception as e:
            logger.error(f"❌ LLM query test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_llm_query_openai_model(self, client, base_url):
        """
        Test LLM query with OpenAI model (placeholder)
        """
        payload = {
            "text": "What is artificial intelligence?",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert "OpenAI placeholder" in response_data["response"]
            assert response_data["model"] == "gpt-4"
            assert response_data["provider"] == "openai"
            
            logger.info("✅ OpenAI LLM query test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ OpenAI LLM query test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_llm_query_gemini_model(self, client, base_url):
        """
        Test LLM query with Gemini model (placeholder)
        """
        payload = {
            "text": "Explain quantum computing",
            "provider": "gemini",
            "model": "gemini-pro",
            "temperature": 0.8,
            "max_tokens": 800
        }
        
        try:
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert "Gemini placeholder" in response_data["response"]
            assert response_data["model"] == "gemini-pro"
            assert response_data["provider"] == "gemini"
            
            logger.info("✅ Gemini LLM query test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ Gemini LLM query test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_llm_query_onprem_model(self, client, base_url):
        """
        Test LLM query with on-premises model (placeholder)
        """
        payload = {
            "text": "Analyze this contract",
            "provider": "onprem",
            "model": "custom-model-1",
            "temperature": 0.6,
            "max_tokens": 1200
        }
        
        try:
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert "On-Prem placeholder" in response_data["response"]
            assert response_data["model"] == "custom-model-1"
            assert response_data["provider"] == "onprem"
            
            logger.info("✅ On-premises LLM query test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ On-premises LLM query test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_health_check(self, client, base_url):
        """
        Test health check endpoint
        """
        try:
            response = await client.get(f"{base_url}/health")
            
            assert response.status_code == 200
            health_data = response.json()
            
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "copilot-desktop-agent"
            
            logger.info("✅ Health check test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ Health check test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_llm_providers_endpoint(self, client, base_url):
        """
        Test LLM providers endpoint
        """
        try:
            response = await client.get(f"{base_url}/llm/providers")
            
            assert response.status_code == 200
            providers_data = response.json()
            
            assert "providers" in providers_data
            assert "default_provider" in providers_data
            assert "default_model" in providers_data
            
            # Check that our expected providers are present
            providers = providers_data["providers"]
            assert "local" in providers
            assert "openai" in providers
            assert "gemini" in providers
            assert "onprem" in providers
            
            logger.info("✅ LLM providers endpoint test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ LLM providers endpoint test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_invalid_provider(self, client, base_url):
        """
        Test LLM query with invalid provider
        """
        payload = {
            "text": "Test prompt",
            "provider": "invalid_provider",
            "model": "test-model"
        }
        
        try:
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 400 for invalid provider
            assert response.status_code == 400
            
            logger.info("✅ Invalid provider test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ Invalid provider test failed: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client, base_url):
        """
        Test LLM query with missing required fields
        """
        payload = {
            "text": "Test prompt"
            # Missing provider and model
        }
        
        try:
            response = await client.post(
                f"{base_url}/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 422 for validation error
            assert response.status_code == 422
            
            logger.info("✅ Missing required fields test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ Missing required fields test failed: {e}")
            raise


class TestPDFPipeline:
    """Test PDF processing pipeline"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_pdf_extract_endpoint(self, client, base_url):
        """
        Test PDF extraction endpoint (placeholder)
        """
        payload = {
            "file_url": "https://example.com/sample.pdf",
            "extract_text": True,
            "extract_metadata": True,
            "extract_images": False
        }
        
        try:
            response = await client.post(
                f"{base_url}/pdf/extract",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert response_data["success"] is True
            assert "text" in response_data
            assert "metadata" in response_data
            
            logger.info("✅ PDF extraction test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ PDF extraction test failed: {e}")
            raise


class TestSearchPipeline:
    """Test web search pipeline"""
    
    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_search_endpoint(self, client, base_url):
        """
        Test web search endpoint (placeholder)
        """
        payload = {
            "query": "artificial intelligence legal implications",
            "provider": "duckduckgo",
            "max_results": 5
        }
        
        try:
            response = await client.post(
                f"{base_url}/search/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            response_data = response.json()
            
            assert response_data["success"] is True
            assert "results" in response_data
            assert len(response_data["results"]) > 0
            
            logger.info("✅ Web search test passed")
            
        except httpx.ConnectError:
            pytest.skip("FastAPI agent not running")
        except Exception as e:
            logger.error(f"❌ Web search test failed: {e}")
            raise


# Utility functions for running tests
def run_smoke_test():
    """Run the main smoke test"""
    import asyncio
    
    async def _run_test():
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "text": "Summarize this case law",
                "provider": "local",
                "model": "local",
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            try:
                response = await client.post(
                    "http://localhost:8000/llm/query",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "Local model placeholder" in data["response"]:
                        print("✅ Smoke test PASSED!")
                        print(f"Response: {data['response'][:200]}...")
                        return True
                    else:
                        print("❌ Smoke test FAILED: Response doesn't contain expected placeholder")
                        return False
                else:
                    print(f"❌ Smoke test FAILED: HTTP {response.status_code}")
                    return False
                    
            except httpx.ConnectError:
                print("❌ Smoke test FAILED: Cannot connect to FastAPI agent")
                print("Start the agent with: python agent/app.py")
                return False
            except Exception as e:
                print(f"❌ Smoke test FAILED: {e}")
                return False
    
    return asyncio.run(_run_test())


if __name__ == "__main__":
    # Run smoke test directly
    success = run_smoke_test()
    exit(0 if success else 1)
