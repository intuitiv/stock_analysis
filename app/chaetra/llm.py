"""LLM provider management and integration."""
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
import json
import time
from abc import ABC, abstractmethod
import logging
from datetime import datetime

from app.chaetra.interfaces import ILLMProvider
from app.core.config import settings
from app.core.cache import RedisCache

logger = logging.getLogger(__name__)

PROVIDER_STATUS_CACHE_PREFIX = "llm_provider_status:"

class BaseLLMProvider(ILLMProvider):
    """Base implementation of the ILLMProvider interface."""
    
    def __init__(
        self,
        provider_name: str,
        model_name: Optional[str],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') if base_url else None
        self.headers = {"Content-Type": "application/json"}
        if self.api_key and not ("generativelanguage.googleapis.com" in (self.base_url or "")):
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _serialize_context(self, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if context is None:
            return None
        processed_context = {}
        for k, v in context.items():
            if isinstance(v, datetime):
                processed_context[k] = v.isoformat()
            elif isinstance(v, dict):
                processed_context[k] = self._serialize_context(v)
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, datetime):
                        new_list.append(item.isoformat())
                    elif isinstance(item, dict):
                        new_list.append(self._serialize_context(item))
                    else:
                        new_list.append(item)
                processed_context[k] = new_list
            else:
                processed_context[k] = v
        return processed_context

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, temperature: float = 0.7) -> str:
        raise NotImplementedError("Subclasses must implement generate_text")

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation."""
    
    def __init__(self):
        super().__init__(
            provider_name="ollama",
            model_name=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_API_URL
        )

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, temperature: float = 0.7, schema: Optional[Dict[str, Any]] = None) -> str:
        serialized_context = self._serialize_context(context)
        full_prompt = f"Context: {json.dumps(serialized_context)}\n\n{prompt}" if serialized_context else prompt
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                response_data = await response.json()
                return response_data.get("response", "")

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self):
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        super().__init__(
            provider_name="openai",
            model_name=settings.OPENAI_MODEL,
            api_key=api_key,
            base_url="https://api.openai.com/v1"
        )

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, temperature: float = 0.7, schema: Optional[Dict[str, Any]] = None) -> str:
        serialized_context = self._serialize_context(context)
        messages = [{"role": "system", "content": f"Context: {json.dumps(serialized_context)}"} if serialized_context else {"role": "system", "content": "You are a helpful assistant."}]
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                response_data = await response.json()
                return response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider implementation."""
    
    def __init__(self):
        api_key = settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else None
        super().__init__(
            provider_name="gemini",
            model_name=settings.GEMINI_MODEL,
            api_key=api_key,
            base_url=f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}"
        )

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, temperature: float = 0.7, schema: Optional[Dict[str, Any]] = None) -> str:
        serialized_context = self._serialize_context(context)
        content = f"Context: {json.dumps(serialized_context)}\n\n{prompt}" if serialized_context else prompt
        payload = {
            "contents": [{"parts": [{"text": content}]}],
            "generationConfig": {
                "temperature": temperature
            }
        }
        request_url = f"{self.base_url}:generateContent?key={self.api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.post(request_url, json=payload) as response:
                response_data = await response.json()
                try:
                    return response_data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return ""

class LMStudioProvider(OpenAIProvider):
    """LM Studio provider using OpenAI-compatible API."""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "lm_studio"
        self.base_url = settings.LM_STUDIO_BASE_URL
        if settings.LM_STUDIO_MODEL:
            self.model_name = settings.LM_STUDIO_MODEL
        self.headers.pop("Authorization", None)
        logger.info(f"Initialized LM Studio provider with base URL: {self.base_url}")

class LLMManager:
    """Manager for LLM providers."""
    
    def __init__(self):
        self.cache = RedisCache()
        self.providers: Dict[str, ILLMProvider] = {}
        self.provider_order: List[str] = settings.LLM_PROVIDER_ORDER
        self.default_provider_name: Optional[str] = None
        logger.info(f"Creating LLMManager with provider order: {self.provider_order}")

    @classmethod
    async def create(cls) -> 'LLMManager':
        instance = cls()
        await instance._initialize_providers()
        for provider_name in instance.provider_order:
            if provider_name in instance.providers:
                instance.default_provider_name = provider_name
                break
        if not instance.providers:
            raise ValueError("No LLM providers configured.")
        if not instance.default_provider_name:
            raise ValueError("Could not determine a default LLM provider.")
        logger.info(f"LLMManager initialized. Default: {instance.default_provider_name}. Available: {list(instance.providers.keys())}")
        return instance

    async def _initialize_providers(self):
        """Initialize LLM providers based on configuration."""
        for name in self.provider_order:
            try:
                if name == "gemini" and settings.GEMINI_API_KEY and settings.GEMINI_MODEL:
                    self.providers["gemini"] = GeminiProvider()
                    logger.info("Gemini provider initialized")
                
                elif name == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_MODEL:
                    self.providers["openai"] = OpenAIProvider()
                    logger.info("OpenAI provider initialized")
                
                elif name == "lm_studio" and getattr(settings, "ENABLE_LM_STUDIO", False) and settings.LM_STUDIO_BASE_URL:
                    try:
                        provider = LMStudioProvider()
                        # Test connection to LM Studio
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f"{settings.LM_STUDIO_BASE_URL}/models") as response:
                                if response.status == 200:
                                    self.providers["lm_studio"] = provider
                                    logger.info(f"LM Studio provider initialized and connected at {settings.LM_STUDIO_BASE_URL}")
                                else:
                                    logger.warning(f"LM Studio API returned status {response.status}. Provider not initialized.")
                    except Exception as e:
                        logger.warning(f"LM Studio initialization failed: {str(e)}")
                
                elif name == "ollama" and getattr(settings, "ENABLE_OLLAMA", False) and settings.OLLAMA_API_URL and settings.OLLAMA_MODEL:
                    self.providers["ollama"] = OllamaProvider()
                    logger.info("Ollama provider initialized")
                
                else:
                    logger.debug(f"Provider {name} not configured or missing required settings")
                    
            except Exception as e:
                logger.error(f"Error initializing provider {name}: {e}")

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None, temperature: float = 0.7, provider_name: Optional[str] = None) -> str:
        provider = self._get_provider(provider_name)
        if not provider:
            raise ValueError(f"No provider available. Requested: {provider_name}")
        try:
            return await provider.generate_text(prompt, context, temperature)
        except Exception as e:
            logger.error(f"Error generating text with provider {provider.provider_name}: {e}")
            if provider.provider_name != self.default_provider_name:
                default_provider = self._get_provider()
                if default_provider:
                    logger.info(f"Falling back to default provider {default_provider.provider_name}")
                    return await default_provider.generate_text(prompt, context, temperature)
            raise

    def _get_provider(self, provider_name: Optional[str] = None) -> Optional[ILLMProvider]:
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        return self.providers.get(self.default_provider_name)

    async def generate_structured_output(self, prompt: str, schema: Dict[str, Any], provider_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates structured output from a prompt using the specified LLM provider.
        """
        provider = self._get_provider(provider_name)
        if not provider:
            raise ValueError(f"No provider available. Requested: {provider_name}")
        try:
            # Assuming the provider's generate_text method can handle a schema
            response = await provider.generate_text(prompt, schema=schema)
            response = response.strip()
            # Attempt to parse the response as JSON
            try:
                # Remove ```json and ``` wrappers if present
                if response.lower().startswith("```json"):
                    response = response[7:]
                if response.lower().endswith("```"):
                    response = response[:-3]
                logger.error(f"Generated structured output for {response}")
                return json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}, Response: {response}")
                raise ValueError("LLM response could not be parsed as JSON") from e
        except Exception as e:
            logger.error(f"Error generating structured output with provider {provider.provider_name}: {e}")
            raise
