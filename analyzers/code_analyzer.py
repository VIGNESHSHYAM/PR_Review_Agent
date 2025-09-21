from typing import List, Dict, Any
from .static_analyzer import StaticAnalyzer
from .gemini_analyzer import GeminiAnalyzer
from utils.logger import get_logger

class CodeAnalyzer:
    
    def __init__(self, gemini_api_key: str = None, verbose: bool = False):
        self.static_analyzer = StaticAnalyzer()
        self.gemini_analyzer = GeminiAnalyzer(gemini_api_key)
        self.logger = get_logger()
        self.verbose = verbose
    
    def analyze_diff(self, diff: str) -> List[Dict[str, Any]]:
        feedback = []
        
        if self.verbose:
            self.logger.info("Running static analysis")
        feedback.extend(self.static_analyzer.analyze(diff))
        
        if self.gemini_analyzer.api_key:
            if self.verbose:
                self.logger.info("Running AI analysis")
            feedback.extend(self.gemini_analyzer.analyze(diff))
        else:
            self.logger.warning("No Gemini API key provided, skipping AI analysis")
        
        feedback = self._deduplicate_feedback(feedback)
        
        return feedback
    
    def _deduplicate_feedback(self, feedback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique_feedback = []
        
        for item in feedback:
            # Create a unique identifier for this feedback item
            identifier = (item.get('line'), item.get('message', '')[:100])
            
            if identifier not in seen:
                seen.add(identifier)
                unique_feedback.append(item)
        
        return unique_feedback