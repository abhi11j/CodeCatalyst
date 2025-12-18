"""
Handles AI service interactions and retry/backoff logic.
"""
from typing import Optional, Dict, Any
import os
import time
import random
import logging
import requests

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, api_key: Optional[str], endpoint: Optional[str], model: Optional[str]):
        self.api_key = api_key or os.environ.get("AICafe_API_KEY")
        self.endpoint = endpoint or os.environ.get("AICafe_API_ENDPOINT")
        self.model = model or os.environ.get("AICafe_MODEL")
        if not self.api_key:
            raise ValueError("AI API key is required")

    def generate(self, prompt: str, max_tokens: int = 1000, attempts: int = 5, timeout: int = 20) -> Dict[str, Any]:
        headers = {"api-key": f"{self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": max_tokens,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        source = "AI Cafe"
        for attempt in range(attempts):
            try:
                logger.info("Sending prompt to AI endpoint (attempt %d)", attempt + 1)
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=timeout)
                if response.status_code == 401:
                    logger.warning("AI auth failed, attempting secondary credentials")
                    # fallback to OpenAI env vars if present
                    self.model = os.environ.get("OpenAI_MODEL") or self.model
                    self.api_key = os.environ.get("OpenAI_API_KEY") or self.api_key
                    self.endpoint = os.environ.get("OpenAI_API_ENDPOINT") or self.endpoint
                    headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
                    source = "Open AI"
                    continue
                if response.status_code == 429:
                    wait_time = min(2 ** attempt, 60) + random.uniform(0, 1)
                    logger.info("AI rate limit hit, backing off %fs", wait_time)
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()
                return {"text": response.text, "status_code": response.status_code, "source": source}
            except requests.exceptions.RequestException as exc:
                logger.debug("AI request error: %s", exc)
                # small backoff before retry
                time.sleep(min(2 ** attempt, 30))
                last_exc = exc
        raise RuntimeError(f"AI endpoint failed after {attempts} attempts: {last_exc}")
