from dataclasses import dataclass
from typing import Optional

@dataclass
class Feedback:
    """Data class for feedback items"""
    type: str  # error, warning, info, suggestion
    message: str
    line: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'type': self.type,
            'message': self.message,
            'line': self.line,
            'code_snippet': self.code_snippet,
            'suggestion': self.suggestion
        }