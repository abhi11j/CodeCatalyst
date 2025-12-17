import json
import logging
from typing import Dict, Any, List, Optional

from Scanner.GitHub.Interface.ISearchProvider import ISearchProvider
from Scanner.Utility.RuleConfiguration import DEFAULT_COMPARISON_RULES
from Scanner.Model.RepoFeatures import RepoFeatures

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ===== Comparison Engine =====

"""Compare repositories and generate improvement suggestions."""
class AutomatedSuggestion(ISearchProvider):
    """Initialize comparator with optional custom rules."""
    def __init__(self = None):        
        self.rules = DEFAULT_COMPARISON_RULES
    
    """Compare target repo with similar repos and generate suggestions."""
    def GenerateSuggestions(self, context: Dict[str, Any], target_url: Optional[str] = None, ai_only: bool = False) -> Dict[str, Any]:
        target = context.get("target", {})
        others = context.get("others", [])
        stats = self.CalculateStats(others, self.rules)
        suggestions = self.GetSuggestions(target, stats)
        
        return suggestions
        # {
        #     # "stats": stats,
        #     "suggestions": suggestions,
        #     # "metadata": {
        #     #     "target": target.name,
        #     #     "repos_analyzed": len(others),
        #     #     "comparison_fields": list(self.rules.keys())
        #     # }
        # }
    
    """Calculate comparison statistics based on provided rules."""
    def CalculateStats(self, repos_features: List[RepoFeatures], rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        if not repos_features:
            return {}
        
        if rules is None:
            rules = self.rules
        
        total = len(repos_features)
        stats = {}
        
        for key, rule in rules.items():
            field = rule["field"]
            stat_key = f"{field[4:]}_ratio"  # Convert has_x to x_ratio
            stats[stat_key] = sum(1 for r in repos_features if getattr(r, field, False)) / total
        
        logger.info("Calculated stats: %s", json.dumps(stats, default=str, indent=2 ))
        return stats
    
    """Generate improvement suggestions."""
    def GetSuggestions(self, target: RepoFeatures, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        suggestions = []
        
        for key, rule in self.rules.items():
            field = rule["field"]
            threshold = rule["threshold"]
            stat_key = f"{field[4:]}_ratio"  # Convert has_x to x_ratio
            
            if stat_key not in stats:
                continue
            
            ratio = stats[stat_key]
            target_has = getattr(target, field)
            
            if not target_has and ratio >= threshold:
                suggestions.append({
                    "title": f"Add {key.upper()}",  # Use uppercase for consistency
                    "details": rule["add_msg"],
                    "priority": "high" if ratio > 0.8 else "medium" if ratio > 0.4 else "low",
                    "source": "Automation Rules"
                })
        
        return suggestions
