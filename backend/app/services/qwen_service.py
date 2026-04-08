from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, parse, request

from app.core.config import Settings


@dataclass(slots=True)
class QwenGeneration:
    content: str | None
    provider: str
    model: str
    used_network: bool
    error_message: str | None = None


class QwenService:
    """Small OpenAI-compatible Qwen client with graceful fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, *, system_prompt: str, user_prompt: str) -> QwenGeneration:
        if not self.settings.qwen_api_key or not self.settings.qwen_api_base:
            return QwenGeneration(
                content=None,
                provider="mock",
                model=self.settings.qwen_model,
                used_network=False,
                error_message="Qwen API 未配置，已回退到本地模板回答。",
            )

        url = parse.urljoin(self.settings.qwen_api_base.rstrip("/") + "/", "chat/completions")
        payload = json.dumps(
            {
                "model": self.settings.qwen_model,
                "temperature": self.settings.qwen_temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
        ).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.settings.qwen_api_key}",
            "Content-Type": "application/json",
        }
        http_request = request.Request(url=url, data=payload, headers=headers, method="POST")

        try:
            with request.urlopen(http_request, timeout=self.settings.qwen_timeout_seconds) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            return QwenGeneration(
                content=None,
                provider="qwen",
                model=self.settings.qwen_model,
                used_network=True,
                error_message=f"Qwen API 请求失败：{exc}",
            )

        content = (
            parsed.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
        )
        return QwenGeneration(
            content=content.strip() if isinstance(content, str) else None,
            provider="qwen",
            model=self.settings.qwen_model,
            used_network=True,
        )
