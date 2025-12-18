"""
Small utilities to build prompts for the AI provider.
"""
import json
from typing import Dict, Any


def build_prompt(context: Dict[str, Any]) -> str:
    return (
        "You are an assistant that returns repository improvement suggestions as JSON.\n"
        "Given the 'target' repository features and a list of 'others', return a complete JSON string with keys and \n"
        "Do not include code fences, explanations, or text outside JSON: \n"
        "- suggestions: an array of objects with keys: title, detail, importance (0-10)\n"
        "Return only JSON and nothing else.\n\n"
        f"Context:\n{json.dumps(context, default=str, indent=2)}"
    )


def build_complete_ai_prompt(project_url: str) -> str:
    return (
        "I have uploaded my project on GitHub here: [{project_url}] \n"
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
