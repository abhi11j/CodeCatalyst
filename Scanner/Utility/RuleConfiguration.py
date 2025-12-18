
from typing import Any, Dict


DEFAULT_COMPARISON_RULES: Dict[str, Dict[str, Any]] = {
    "dockerfile": {
        "field": "has_dockerfile",
        "threshold": -0.1,
        "add_msg": "Add a Dockerfile to simplify deployment and ensure reproducible builds.",
        "remove_msg": "Consider removing the Dockerfile if it is unused by your CI/CD flow.",
    },
    "ci": {
        "field": "has_ci",
        "threshold": 0.5,
        "add_msg": "Add CI workflows (GitHub Actions / other) to run tests and lint on push/PR.",
        "remove_msg": "Consider simplifying or removing unused CI workflows.",
    },
    "tests": {
        "field": "has_tests",
        "threshold": 0.01,
        "add_msg": "Add a test suite and configure test runner (pytest/unittest) to improve reliability.",
        "remove_msg": "Consider whether your test structure is necessary; if not, consider removing it.",
    },
    "readme": {
        "field": "has_readme",
        "threshold": 0.9,
        "add_msg": "Add a README.md that describes the project, quickstart, and contribution guidelines.",
        "remove_msg": "README seems optional for this group of projects; consider reviewing and simplifying it.",
    },
    # language rule: if a majority of others use a different language, suggest setting primary language
    "language": {
        "field": "language",
        "threshold": 0.6,
        "add_msg": "Set the primary language for the project to {primary}.",
        "no_remove": True,
    }
}
