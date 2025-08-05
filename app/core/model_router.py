"""
Multi-Model Router for handling different AI providers.
Supports OpenAI, Claude (Anthropic), Mistral, and local Ollama.
"""
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum
from pydantic import BaseModel
import asyncio
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    MISTRAL = "mistral"
    OLLAMA = "ollama"


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider: ModelProvider
    model_name: str
    max_tokens: int = 2000
    temperature: float = 0.1
    cost_per_token: float = 0.0
    priority: int = 1  # Lower number = higher priority
    enabled: bool = True
    rate_limit: int = 100  # Requests per minute


class ModelInterface(ABC):
    """Abstract interface for AI model providers."""
    
    @abstractmethod
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion from the model."""
        pass
    
    @abstractmethod
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion from the model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model provider is available."""
        pass


class OpenAIProvider(ModelInterface):
    """OpenAI model provider."""
    
    def __init__(self):
        self._client = None
        
    def _get_client(self):
        """Get OpenAI client."""
        if self._client is None and settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not available")
                return None
        return self._client
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using OpenAI."""
        client = self._get_client()
        if not client:
            raise ValueError("OpenAI client not available")
        
        try:
            response = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "provider": ModelProvider.OPENAI,
                "model": config.model_name
            }
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion using OpenAI."""
        client = self._get_client()
        if not client:
            raise ValueError("OpenAI client not available")
        
        try:
            stream = await client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return bool(settings.openai_api_key and self._get_client())


class ClaudeProvider(ModelInterface):
    """Anthropic Claude model provider."""
    
    def __init__(self):
        self._client = None
        
    def _get_client(self):
        """Get Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                api_key = getattr(settings, 'anthropic_api_key', None)
                if api_key:
                    self._client = anthropic.AsyncAnthropic(api_key=api_key)
            except ImportError:
                logger.warning("Anthropic package not available")
                return None
        return self._client
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Claude."""
        client = self._get_client()
        if not client:
            raise ValueError("Claude client not available")
        
        try:
            # Convert messages format for Claude
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = await client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=system_msg,
                messages=user_messages,
                **kwargs
            )
            
            return {
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "provider": ModelProvider.CLAUDE,
                "model": config.model_name
            }
        except Exception as e:
            logger.error(f"Claude completion failed: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion using Claude."""
        client = self._get_client()
        if not client:
            raise ValueError("Claude client not available")
        
        try:
            system_msg = ""
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            stream = await client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=system_msg,
                messages=user_messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
                    
        except Exception as e:
            logger.error(f"Claude streaming failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Claude is available."""
        return bool(getattr(settings, 'anthropic_api_key', None) and self._get_client())


class MistralProvider(ModelInterface):
    """Mistral AI model provider."""
    
    def __init__(self):
        self._client = None
        
    def _get_client(self):
        """Get Mistral client."""
        if self._client is None:
            try:
                from mistralai.async_client import MistralAsyncClient
                api_key = getattr(settings, 'mistral_api_key', None)
                if api_key:
                    self._client = MistralAsyncClient(api_key=api_key)
            except ImportError:
                logger.warning("Mistral package not available")
                return None
        return self._client
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Mistral."""
        client = self._get_client()
        if not client:
            raise ValueError("Mistral client not available")
        
        try:
            response = await client.chat(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "provider": ModelProvider.MISTRAL,
                "model": config.model_name
            }
        except Exception as e:
            logger.error(f"Mistral completion failed: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion using Mistral."""
        client = self._get_client()
        if not client:
            raise ValueError("Mistral client not available")
        
        try:
            stream = await client.chat_stream(
                model=config.model_name,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Mistral streaming failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Mistral is available."""
        return bool(getattr(settings, 'mistral_api_key', None) and self._get_client())


class OllamaProvider(ModelInterface):
    """Local Ollama model provider."""
    
    def __init__(self):
        self._client = None
        
    def _get_client(self):
        """Get Ollama client."""
        if self._client is None:
            try:
                import httpx
                ollama_url = getattr(settings, 'ollama_url', 'http://localhost:11434')
                self._client = httpx.AsyncClient(base_url=ollama_url)
            except ImportError:
                logger.warning("httpx package not available for Ollama")
                return None
        return self._client
    
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion using Ollama."""
        client = self._get_client()
        if not client:
            raise ValueError("Ollama client not available")
        
        try:
            # Convert messages to Ollama format
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            response = await client.post("/api/generate", json={
                "model": config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            })
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "content": data.get("response", ""),
                    "usage": {
                        "prompt_tokens": 0,  # Ollama doesn't provide token counts
                        "completion_tokens": 0,
                        "total_tokens": 0
                    },
                    "provider": ModelProvider.OLLAMA,
                    "model": config.model_name
                }
            else:
                raise ValueError(f"Ollama request failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama completion failed: {e}")
            raise
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        config: ModelConfig,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion using Ollama."""
        client = self._get_client()
        if not client:
            raise ValueError("Ollama client not available")
        
        try:
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            async with client.stream("POST", "/api/generate", json={
                "model": config.model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            }) as response:
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                            
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            # Use a simple synchronous check
            import requests
            response = requests.get(f"{getattr(settings, 'ollama_url', 'http://localhost:11434')}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class ModelRouter:
    """Router for managing multiple AI model providers."""
    
    def __init__(self):
        self.providers: Dict[ModelProvider, ModelInterface] = {
            ModelProvider.OPENAI: OpenAIProvider(),
            ModelProvider.CLAUDE: ClaudeProvider(),
            ModelProvider.MISTRAL: MistralProvider(),
            ModelProvider.OLLAMA: OllamaProvider(),
        }
        
        # Default model configurations
        self.model_configs: Dict[str, ModelConfig] = {
            "gpt-3.5-turbo": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=2000,
                temperature=0.1,
                cost_per_token=0.002,
                priority=1
            ),
            "gpt-4": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                max_tokens=2000,
                temperature=0.1,
                cost_per_token=0.03,
                priority=2
            ),
            "claude-3-sonnet": ModelConfig(
                provider=ModelProvider.CLAUDE,
                model_name="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.1,
                cost_per_token=0.015,
                priority=3
            ),
            "mistral-medium": ModelConfig(
                provider=ModelProvider.MISTRAL,
                model_name="mistral-medium",
                max_tokens=2000,
                temperature=0.1,
                cost_per_token=0.01,
                priority=4
            ),
            "llama2": ModelConfig(
                provider=ModelProvider.OLLAMA,
                model_name="llama2",
                max_tokens=2000,
                temperature=0.1,
                cost_per_token=0.0,  # Local model, no cost
                priority=5
            )
        }
        
        logger.info(f"Initialized ModelRouter with {len(self.providers)} providers")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        available = []
        for model_name, config in self.model_configs.items():
            if (config.enabled and 
                self.providers[config.provider].is_available()):
                available.append(model_name)
        return available
    
    def select_best_model(
        self, 
        task_type: str = "general",
        preferred_provider: Optional[ModelProvider] = None,
        max_cost: Optional[float] = None
    ) -> Optional[str]:
        """Select the best model for a given task."""
        available_models = self.get_available_models()
        
        if not available_models:
            return None
        
        # Filter by preferences and constraints
        candidates = []
        for model_name in available_models:
            config = self.model_configs[model_name]
            
            # Check provider preference
            if preferred_provider and config.provider != preferred_provider:
                continue
                
            # Check cost constraint
            if max_cost and config.cost_per_token > max_cost:
                continue
            
            candidates.append((model_name, config))
        
        if not candidates:
            # Fallback to any available model
            candidates = [(name, self.model_configs[name]) for name in available_models]
        
        # Sort by priority (lower number = higher priority)
        candidates.sort(key=lambda x: x[1].priority)
        
        return candidates[0][0] if candidates else None
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        task_type: str = "general",
        fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate completion with automatic model selection and fallback."""
        
        # Select model if not specified
        if not model_name:
            model_name = self.select_best_model(task_type)
            
        if not model_name:
            raise ValueError("No available models")
        
        config = self.model_configs.get(model_name)
        if not config:
            raise ValueError(f"Unknown model: {model_name}")
        
        provider = self.providers[config.provider]
        
        try:
            result = await provider.generate_completion(messages, config, **kwargs)
            result['selected_model'] = model_name
            return result
            
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            
            if fallback and len(self.get_available_models()) > 1:
                # Try fallback model
                available = self.get_available_models()
                for fallback_model in available:
                    if fallback_model != model_name:
                        try:
                            logger.info(f"Trying fallback model: {fallback_model}")
                            fallback_config = self.model_configs[fallback_model]
                            fallback_provider = self.providers[fallback_config.provider]
                            result = await fallback_provider.generate_completion(
                                messages, fallback_config, **kwargs
                            )
                            result['selected_model'] = fallback_model
                            result['is_fallback'] = True
                            return result
                        except Exception as fallback_error:
                            logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                            continue
            
            # If all models fail, raise the original error
            raise e
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        task_type: str = "general",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream completion with model selection."""
        
        # Select model if not specified
        if not model_name:
            model_name = self.select_best_model(task_type)
            
        if not model_name:
            raise ValueError("No available models")
        
        config = self.model_configs.get(model_name)
        if not config:
            raise ValueError(f"Unknown model: {model_name}")
        
        provider = self.providers[config.provider]
        
        # Yield metadata first
        yield {
            "type": "metadata",
            "selected_model": model_name,
            "provider": config.provider.value
        }
        
        # Stream content
        async for chunk in provider.stream_completion(messages, config, **kwargs):
            yield {
                "type": "content",
                "content": chunk
            }


# Global router instance
router = ModelRouter()