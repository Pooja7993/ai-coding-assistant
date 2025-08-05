"""
Test suite for the AI Coding Assistant.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import settings
from app.core.memory import RAGMemory, FAISMemoryBackend
from app.services.agent import AIAgent, CodeRequest, ChatRequest

# Test client
client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Coding Assistant"
        assert data["status"] == "running"
        assert "endpoints" in data
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestMemory:
    """Test memory functionality."""
    
    def setup_method(self):
        """Setup test method."""
        self.memory = RAGMemory("faiss")
    
    def test_memory_initialization(self):
        """Test memory backend initialization."""
        assert isinstance(self.memory.backend, FAISMemoryBackend)
        assert self.memory.max_size == settings.max_memory_size
    
    def test_add_conversation(self):
        """Test adding conversation to memory."""
        user_message = "Hello, how are you?"
        assistant_response = "I'm doing well, thank you!"
        
        self.memory.add_conversation(user_message, assistant_response)
        
        # Search for the conversation
        results = self.memory.search_relevant_context("hello")
        assert len(results) > 0
        assert user_message.lower() in results[0]['document'].lower()
    
    def test_add_code_context(self):
        """Test adding code context to memory."""
        code = "def hello_world():\n    print('Hello, World!')"
        description = "A simple hello world function"
        
        self.memory.add_code_context(code, description)
        
        # Search for the code
        results = self.memory.search_relevant_context("hello world")
        assert len(results) > 0
        assert "hello_world" in results[0]['document']
    
    def test_clear_memory(self):
        """Test clearing memory."""
        self.memory.add_conversation("test", "response")
        self.memory.clear_memory()
        
        results = self.memory.search_relevant_context("test")
        assert len(results) == 0


class TestAIAgent:
    """Test AI Agent functionality."""
    
    def setup_method(self):
        """Setup test method."""
        self.agent = AIAgent()
    
    @patch('app.services.agent.OpenAI')
    def test_agent_initialization(self, mock_openai):
        """Test agent initialization."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Access the client to trigger initialization
        client = self.agent._get_client()
        assert client == mock_client
    
    def test_build_system_prompt(self):
        """Test system prompt building."""
        prompt = self.agent._build_system_prompt("code_generation")
        assert "coding assistant" in prompt.lower()
        assert "code generation" in prompt.lower()
    
    def test_get_relevant_context(self):
        """Test getting relevant context."""
        context = self.agent._get_relevant_context("test query")
        assert isinstance(context, list)
    
    def test_format_context(self):
        """Test context formatting."""
        context_items = [
            {
                'document': 'Test document content',
                'metadata': {'type': 'conversation'}
            }
        ]
        
        formatted = self.agent._format_context(context_items)
        assert "Test document content" in formatted
        assert "conversation" in formatted
    
    @patch('app.services.agent.OpenAI')
    @pytest.mark.asyncio
    async def test_generate_code_success(self, mock_openai):
        """Test successful code generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```python\ndef hello():\n    print('Hello')\n```"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            request = CodeRequest(prompt="Create a hello function", language="python")
            response = await self.agent.generate_code(request)
            
            assert response.language == "python"
            assert "def hello" in response.code
    
    @pytest.mark.asyncio
    async def test_generate_code_no_api_key(self):
        """Test code generation without API key."""
        with patch.object(settings, 'openai_api_key', None):
            request = CodeRequest(prompt="Create a hello function")
            
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                await self.agent.generate_code(request)
    
    @patch('app.services.agent.OpenAI')
    @pytest.mark.asyncio
    async def test_chat_success(self, mock_openai):
        """Test successful chat interaction."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Hello! How can I help you with coding?"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            request = ChatRequest(message="Hello")
            response = await self.agent.chat(request)
            
            assert "help you" in response.response
            assert isinstance(response.context_used, list)
    
    def test_review_code(self):
        """Test code review functionality."""
        code = "def add(a, b):\n    return a + b"
        review = self.agent.review_code(code)
        
        assert "overall_score" in review
        assert "suggestions" in review
        assert isinstance(review["suggestions"], list)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    @patch('app.services.agent.OpenAI')
    def test_generate_code_endpoint(self, mock_openai):
        """Test code generation endpoint."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```python\nprint('Hello')\n```"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            response = client.post(
                "/api/generate-code",
                json={
                    "prompt": "Print hello",
                    "language": "python"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "code" in data
            assert "explanation" in data
    
    def test_generate_code_endpoint_no_api_key(self):
        """Test code generation endpoint without API key."""
        with patch.object(settings, 'openai_api_key', None):
            response = client.post(
                "/api/generate-code",
                json={
                    "prompt": "Print hello",
                    "language": "python"
                }
            )
            
            assert response.status_code == 400
    
    @patch('app.services.agent.OpenAI')
    def test_chat_endpoint(self, mock_openai):
        """Test chat endpoint."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "I can help you with that!"
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch.object(settings, 'openai_api_key', 'test-key'):
            response = client.post(
                "/api/chat",
                json={
                    "message": "Can you help me?",
                    "use_memory": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "context_used" in data
    
    def test_review_code_endpoint(self):
        """Test code review endpoint."""
        response = client.post(
            "/api/review-code",
            json={
                "code": "def add(a, b):\n    return a + b",
                "language": "python"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "review" in data
        assert "overall_score" in data["review"]
    
    def test_memory_stats_endpoint(self):
        """Test memory stats endpoint."""
        response = client.get("/api/memory/stats")
        assert response.status_code == 200
        data = response.json()
        assert "backend_type" in data
        assert "total_documents" in data
    
    def test_clear_memory_endpoint(self):
        """Test clear memory endpoint."""
        response = client.delete("/api/memory/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_search_memory_endpoint(self):
        """Test memory search endpoint."""
        response = client.get("/api/memory/search?query=test&k=3")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_initialization(self):
        """Test settings initialization."""
        assert settings.api_port == 8000
        assert settings.model_name == "gpt-3.5-turbo"
        assert settings.memory_type in ["faiss", "chroma"]
        assert settings.max_memory_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])