"""Qwen service using OpenAI-compatible API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, parse, request

from app.core.config import settings


@dataclass
class QwenGeneration:
    """Result from Qwen generation."""
    
    content: str | None
    provider: str
    model: str
    used_network: bool
    error_message: str | None = None


class QwenService:
    """Qwen service using OpenAI-compatible API (Alibaba Cloud Bailian)."""
    
    def __init__(self, settings_obj=None) -> None:
        """Initialize Qwen service.
        
        Args:
            settings_obj: Settings object (optional, defaults to global settings)
        """
        self.settings = settings_obj or settings
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        enable_thinking: bool = False,
    ) -> QwenGeneration:
        """Generate response using Qwen API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Override temperature (optional)
            enable_thinking: Enable deep thinking mode (for qwen3.7-max)
            
        Returns:
            QwenGeneration object with result
        """
        if not self.settings.qwen_api_key or not self.settings.qwen_api_base:
            return QwenGeneration(
                content=None,
                provider="mock",
                model=self.settings.qwen_model,
                used_network=False,
                error_message="Qwen API 未配置，已回退到本地模板回答。",
            )
        
        url = parse.urljoin(self.settings.qwen_api_base.rstrip("/") + "/", "chat/completions")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        payload = {
            "model": self.settings.qwen_model,
            "messages": messages,
            "temperature": temperature or self.settings.qwen_temperature,
        }
        
        # Enable thinking mode for qwen3.7-max
        if enable_thinking:
            payload["extra_body"] = {"enable_thinking": True}
        
        payload_json = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Authorization": f"Bearer {self.settings.qwen_api_key}",
            "Content-Type": "application/json",
        }
        
        http_request = request.Request(
            url=url,
            data=payload_json,
            headers=headers,
            method="POST",
        )
        
        try:
            with request.urlopen(
                http_request,
                timeout=self.settings.qwen_timeout_seconds
            ) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            return QwenGeneration(
                content=None,
                provider="qwen",
                model=self.settings.qwen_model,
                used_network=True,
                error_message=f"Qwen API 请求失败：{exc}",
            )
        except Exception as exc:
            return QwenGeneration(
                content=None,
                provider="qwen",
                model=self.settings.qwen_model,
                used_network=True,
                error_message=f"Qwen API 处理异常：{exc}",
            )
        
        try:
            content = (
                parsed.get("choices", [{}])[0]
                .get("message", {})
                .get("content")
            )
        except (KeyError, IndexError) as exc:
            return QwenGeneration(
                content=None,
                provider="qwen",
                model=self.settings.qwen_model,
                used_network=True,
                error_message=f"Qwen API 响应解析失败：{exc}",
            )
        
        return QwenGeneration(
            content=content.strip() if isinstance(content, str) else None,
            provider="qwen",
            model=self.settings.qwen_model,
            used_network=True,
        )
    
    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        enable_thinking: bool = False,
    ):
        """Generate streaming response (for future use).
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Override temperature
            enable_thinking: Enable thinking mode
            
        Yields:
            Chunks of response
        """
        # TODO: Implement streaming for better UX
        result = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            enable_thinking=enable_thinking,
        )
        yield result
