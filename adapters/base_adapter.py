# adapters/base_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class GitServerAdapter(ABC):
    """Abstract base class for git server adapters"""
    
    @abstractmethod
    def get_pr_details(self, repo_url: str, pr_id: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_diff(self, repo_url: str, pr_id: int) -> str:
        pass
    
    @abstractmethod
    def post_comment(self, repo_url: str, pr_id: int, comment: str, path: str = None, line: int = None):
        pass
    
    @abstractmethod
    def search_prs(self, query: str, state: str, limit: int) -> List[Dict[str, Any]]:
        """Search for pull requests"""
        pass
    
    @abstractmethod
    def get_user_prs(self, username: str, state: str, limit: int) -> List[Dict[str, Any]]:
        """Get PRs created by a specific user"""
        pass
    
    @abstractmethod
    def get_repo_prs(self, repo_url: str, state: str, limit: int) -> List[Dict[str, Any]]:
        """Get PRs from a specific repository"""
        pass