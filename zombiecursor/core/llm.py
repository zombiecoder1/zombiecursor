"""
Local LLM adapter for ZombieCursor.
Supports both Llama.cpp and Ollama backends.
"""
import json
import uuid
import asyncio
from typing import List, Dict, Any, AsyncGenerator
import requests
from core.interfaces import LLMProvider, Message, MessageRole
from core.config import settings
from core.logging_config import log


class LocalLLM(LLMProvider):
    """Local LLM provider supporting multiple backends."""
    
    def __init__(self):
        self.host = settings.llm_host
        self.model = settings.llm_model
        self.timeout = settings.llm_timeout
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        
        # Check if Ollama should be used instead
        if settings.ollama_host:
            self.use_ollama = True
            self.host = settings.ollama_host
            if settings.ollama_model:
                self.model = settings.ollama_model
            log.info(f"Using Ollama backend at {self.host}")
        else:
            self.use_ollama = False
            log.info(f"Using Llama.cpp backend at {self.host}")
    
    def _format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for LLM API."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role.value,
                "content": msg.content
            })
        return formatted
    
    async def chat(self, messages: List[Message]) -> str:
        """Send chat messages and get response."""
        try:
            formatted_messages = self._format_messages(messages)
            
            if self.use_ollama:
                return await self._chat_ollama(formatted_messages)
            else:
                return await self._chat_llamacpp(formatted_messages)
                
        except Exception as e:
            log.error(f"LLM chat error: {str(e)}")
            raise
    
    async def _chat_llamacpp(self, messages: List[Dict[str, str]]) -> str:
        """Chat with Llama.cpp backend."""
        payload = {
            "id": str(uuid.uuid4()),
            "messages": messages,
            "stream": False,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        response = requests.post(
            f"{self.host}/v1/chat/completions",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    async def _chat_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Chat with Ollama backend."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        return result["message"]["content"]
    
    async def chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        """Send chat messages and get streaming response."""
        try:
            formatted_messages = self._format_messages(messages)
            
            if self.use_ollama:
                async for chunk in self._chat_stream_ollama(formatted_messages):
                    yield chunk
            else:
                async for chunk in self._chat_stream_llamacpp(formatted_messages):
                    yield chunk
                    
        except Exception as e:
            log.error(f"LLM chat stream error: {str(e)}")
            raise
    
    async def _chat_stream_llamacpp(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat with Llama.cpp backend."""
        payload = {
            "id": str(uuid.uuid4()),
            "messages": messages,
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        response = requests.post(
            f"{self.host}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    async def _chat_stream_ollama(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """Stream chat with Ollama backend."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            stream=True,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                try:
                    chunk = json.loads(line)
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
                    if 'done' in chunk and chunk['done']:
                        break
                except json.JSONDecodeError:
                    continue
    
    async def health_check(self) -> bool:
        """Check if the LLM backend is healthy."""
        try:
            if self.use_ollama:
                response = requests.get(f"{self.host}/api/tags", timeout=5)
            else:
                response = requests.get(f"{self.host}/health", timeout=5)
            
            return response.status_code == 200
        except Exception as e:
            log.error(f"LLM health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            if self.use_ollama:
                response = requests.get(f"{self.host}/api/tags", timeout=10)
                response.raise_for_status()
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            else:
                # Llama.cpp typically serves one model
                return [self.model] if await self.health_check() else []
        except Exception as e:
            log.error(f"Failed to list models: {str(e)}")
            return []