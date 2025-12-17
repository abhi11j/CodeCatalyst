from __future__ import annotations
import json

import os
import random
import time
from typing import Any, Dict, Optional
import requests

from Scanner.GitHub.Interface.ISearchProvider import ISearchProvider
from Scanner.Utility.RuleConfiguration import DEFAULT_COMPARISON_RULES

import logging
logger = logging.getLogger(__name__)

"""OpenAI-compatible provider using the HTTP API.
    This implementation expects an API key in the env var AI_API_KEY or passed via
    the `api_key` argument. It calls the Chat Completions endpoint and attempts to parse
    a JSON object from the assistant's response.
"""
class AISuggestion(ISearchProvider):
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None):
        # Credentials with AI Cafe
        self.api_key = api_key or os.environ.get("AICafe_API_KEY")
        self.endpoint = endpoint or os.environ.get("AICafe_API_ENDPOINT")
        self.model = model or os.environ.get("AICafe_MODEL")
        if not self.api_key:
            raise ValueError("AI_API_KEY or api_key must be provided for OpenAIProvider")

    def GenerateSuggestions(self, context: Dict[str, Any], target_url: Optional[str] = None, ai_only: bool = False) -> Dict[str, Any]:
        target = context.get("target", {})
        others = context.get("others", [])
        suggestions = []
        prompt = self.BuildCompleteAIPrompt(target_url) if ai_only else self.BuildPrompt(context)
        try:
            source = "AI Cafe"
            headers = {"api-key": f"{self.api_key}"}
            for attempt in range(5):
                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 1000,
                    "top_p": 1.0,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                }
                logger.info("Promt %e", prompt)
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=20)
                # response.raise_for_status()
                logger.info("Reponse status code: %s", response.status_code)
                if response.status_code == 401:
                    logger.error("Connection failed, switching credentials...")
                    # switch credentials to Open AI
                    self.model = os.environ.get("OpenAI_MODEL")
                    self.api_key = os.environ.get("OpenAI_API_KEY")
                    self.endpoint = os.environ.get("OpenAI_API_ENDPOINT")
                    headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "OpenAI-Project": "proj_unuNqffFtTEvJ1Aclibn4iIT"}
                    source = "Open AI"
                elif response.status_code == 429:
                    # No Retry-After header, so use exponential backoff + jitter
                    wait_time = min(2 ** attempt, 60) + random.uniform(0, 1)
                    logger.info(f"Rate limit hit. Waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.info("Status %e", response.status_code)
                    response_json = self.extract_suggestions(response.text)
                    suggestions = [
                        {("details" if k == "detail" else k): v for k, v in item.items()}
                        for item in response_json
                    ]

                    for item in suggestions:
                        item.update(source=source)

        except Exception as e:
            raise ValueError("OpenAIProvider.generate_suggestions failed: %s", e)
        return suggestions
        # {
        #     "suggestions": suggestions
        # }
    
    def check_connection(endpoint, headers):
        try:
            # HEAD is lighter than GET
            resp = requests.head(endpoint, headers=headers, timeout=5)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False  
    
    def extract_suggestions(self, raw_str):
        logger.info("Extracting Json from: %s", raw_str)
        # Step 1: Parse outer JSON
        outer = json.loads(raw_str)

        # Step 2: Extract the inner JSON (stored as a string)
        inner_json_str = outer["choices"][0]["message"]["content"]

        # Step 3: Parse inner JSON
        inner_json = json.loads(inner_json_str)

        # Step 4: Return suggestions only
        return inner_json["suggestions"]


    def BuildPrompt(self, context: Dict[str, Any]) -> str:
        logger.info("Returing build prompt.")
        # Small prompt instructing the model to emit JSON only
        return (
            "You are an assistant that returns repository improvement suggestions as JSON.\n"
            "Given the 'target' repository features and a list of 'others', return a complete JSON string with keys and \n"
            "Do not include code fences, explanations, or text outside JSON: \n"
            "- suggestions: an array of objects with keys: title, detail, importance (0-10)\n"
            "Return only JSON and nothing else.\n\n"
            f"Context:\n{json.dumps(context, default=str, indent=2)}"
        )
    
    # https://github.com/abhi11j/SampleWebApp
    def BuildCompleteAIPrompt(self, project_url) -> str:
        return (
            "I have uploaded my project on GitHub here: [YOUR_PROJECT_URL] \n"
            "Please analyze this repository and provide improvement suggestions by comparing it with other open-source projects written in the same programming language that are publicly available on GitHub. \n" 
            "Focus on: \n"
            "- Code quality and structure \n"
            "- Naming conventions and readability \n"
            "- Best practices (design patterns, error handling, testing) \n"
            "- Documentation and comments \n"
            "- Performance optimizations \n"
            "- Project organization (folders, modules, dependencies) \n"
            "Highlight specific areas where my project differs from well-maintained repositories and suggest actionable improvements. \n"
            "return a complete JSON string with keys and \n"
            "Do not include code fences, explanations, or text outside JSON: \n"
            "- suggestions: an array of objects with keys: title, detail, importance (0-10)\n"
            "Return only JSON and nothing else.\n\n"
        )