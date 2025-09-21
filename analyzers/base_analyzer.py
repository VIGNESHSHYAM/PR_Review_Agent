from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAnalyzer(ABC):
    
    @abstractmethod
    def analyze(self, diff: str) -> List[Dict[str, Any]]:
        pass