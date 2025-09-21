import re
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from utils.logger import get_logger

class StaticAnalyzer(BaseAnalyzer):
    """Performs static analysis on code changes"""
    
    def __init__(self):
        self.logger = get_logger()
        self.patterns = {
            'print_statement': re.compile(r'print\('),
            'todo_comment': re.compile(r'(TODO|FIXME)'),
            'long_function': re.compile(r'def (\w+)\(.*\):'),
            'empty_except': re.compile(r'except:\s*pass'),
            'hardcoded_secret': re.compile(r'(password|secret|key|token)\s*=\s*[\'"][^\'"]+[\'"]', re.IGNORECASE)
        }
    
    def analyze(self, diff: str) -> List[Dict[str, Any]]:
        """Perform static analysis on the diff"""
        feedback = []
        lines = diff.split('\n')
        
        for i, line in enumerate(lines):
            if line.startswith('+') and not line.startswith('+++'):
                code = line[1:].strip()
                
                # Check for various code issues
                feedback.extend(self._check_print_statements(code, i))
                feedback.extend(self._check_todo_comments(code, i))
                feedback.extend(self._check_empty_except(code, i))
                feedback.extend(self._check_hardcoded_secrets(code, i))
        
        return feedback
    
    def _check_print_statements(self, code: str, line_num: int) -> List[Dict[str, Any]]:
        if self.patterns['print_statement'].search(code):
            return [{
                "type": "warning",
                "message": "Consider using logging instead of print statements for production code",
                "line": line_num + 1,
                "code": code
            }]
        return []
    
    def _check_todo_comments(self, code: str, line_num: int) -> List[Dict[str, Any]]:
        if self.patterns['todo_comment'].search(code):
            return [{
                "type": "info",
                "message": "TODO/FIXME comment found - remember to address before merging",
                "line": line_num + 1,
                "code": code
            }]
        return []
    
    def _check_empty_except(self, code: str, line_num: int) -> List[Dict[str, Any]]:
        if self.patterns['empty_except'].search(code):
            return [{
                "type": "warning",
                "message": "Empty except clause found - consider specifying exception types",
                "line": line_num + 1,
                "code": code
            }]
        return []
    
    def _check_hardcoded_secrets(self, code: str, line_num: int) -> List[Dict[str, Any]]:
        if self.patterns['hardcoded_secret'].search(code):
            return [{
                "type": "error",
                "message": "Potential hardcoded secret found - use environment variables instead",
                "line": line_num + 1,
                "code": code
            }]
        return []