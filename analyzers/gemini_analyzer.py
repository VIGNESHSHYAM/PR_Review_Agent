import os
import requests
import json
import re
from typing import List, Dict, Any
from .base_analyzer import BaseAnalyzer
from utils.logger import get_logger

class GeminiAnalyzer(BaseAnalyzer):
    """Uses Gemini AI to analyze code changes"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.logger = get_logger()
    
    def analyze(self, diff: str) -> List[Dict[str, Any]]:
        """Use Gemini AI to analyze the code changes"""
        if not self.api_key:
            self.logger.warning("No Gemini API key provided, skipping AI analysis")
            return []
        
        try:
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key
            }
            
            prompt = self._create_prompt(diff)
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            self.logger.debug("Sending request to Gemini API")
            response = requests.post(self.url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            return self._parse_response(response.json())
                
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {e}")
            return []
    
    def _create_prompt(self, diff: str) -> str:
        return f"""
        You are an expert code reviewer. Analyze the following code changes from a pull request and provide specific, actionable feedback.
        
        Focus on:
        1. Code quality and readability
        2. Potential bugs or logical errors
        3. Security vulnerabilities
        4. Performance issues
        5. Adherence to Python best practices and coding standards
        6. Error handling and edge cases
        
        For each issue found, provide:
        - Type (error, warning, info, or suggestion)
        - A clear message explaining the issue
        - The line number (if applicable)
        - A code snippet showing the problematic code
        - Suggested fix (if applicable)
        
        Format your response as a valid JSON array of objects with these fields:
        - type (string)
        - message (string)
        - line (number or null)
        - code_snippet (string or null)
        - suggestion (string or null)
        
        Code changes (in unified diff format):
        {diff}
        
        Response (JSON only):
        """
    
    def _parse_response(self, response_data: Dict) -> List[Dict[str, Any]]:
        """Parse the Gemini response and extract feedback"""
        try:
            candidates = response_data.get('candidates', [{}])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [{}])
                if parts:
                    feedback_text = parts[0].get('text', '').strip()
                    
                    # Try to extract JSON from the response
                    json_match = re.search(r'\[\s*\{.*\}\s*\]', feedback_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        return json.loads(json_str)
                    else:
                        # Fallback: try to parse the entire response as JSON
                        return json.loads(feedback_text)
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            # Fallback: return as a single info item
            return [{
                "type": "info",
                "message": f"AI Analysis completed but response format was unexpected",
                "line": None,
                "code_snippet": None,
                "suggestion": "Check the AI response format"
            }]
        
        return []