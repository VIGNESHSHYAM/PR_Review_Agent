import os
import requests
from typing import Dict, Any, Tuple, List
from .base_adapter import GitServerAdapter
from utils.logger import get_logger

class GitHubAdapter(GitServerAdapter):
    """Adapter for GitHub"""
    
    def __init__(self, token: str = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.logger = get_logger()
        self.base_url = "https://api.github.com"
    
    def get_pr_details(self, repo_url: str, pr_id: int) -> Dict[str, Any]:
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_id}"
        
        self.logger.debug(f"Fetching PR details from {url}")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_diff(self, repo_url: str, pr_id: int) -> str:
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_id}"
        headers = {**self.headers, 'Accept': 'application/vnd.github.v3.diff'}
        
        self.logger.debug(f"Fetching diff from {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    
    def post_comment(self, repo_url: str, pr_id: int, comment: str, path: str = None, line: int = None):
        owner, repo = self._parse_repo_url(repo_url)
        
        payload = {"body": comment}
        if path and line:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_id}/comments"
            payload.update({
                "path": path,
                "line": line,
                "side": "RIGHT"
            })
        else:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_id}/comments"
            
        self.logger.debug(f"Posting comment to {url}")
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_prs(self, query: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for pull requests across GitHub"""
        url = f"{self.base_url}/search/issues"
        params = {
            'q': f'is:pr {query} state:{state}',
            'per_page': limit,
            'sort': 'updated',
            'order': 'desc'
        }
        
        self.logger.debug(f"Searching PRs with query: {query}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for item in data.get('items', []):
            # Extract repo info from the URL
            repo_url = item['repository_url'].replace(f"{self.base_url}/repos/", "")
            owner, repo = repo_url.split('/')
            
            results.append({
                'id': item['number'],
                'title': item['title'],
                'state': item['state'],
                'url': item['html_url'],
                'repo_owner': owner,
                'repo_name': repo,
                'repo_url': f"https://github.com/{owner}/{repo}",
                'created_at': item['created_at'],
                'updated_at': item['updated_at'],
                'user': item['user']['login']
            })
        
        return results
    
    def get_user_prs(self, username: str = None, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs created by a specific user"""
        if not username:
            # Get authenticated user's PRs
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            user_data = response.json()
            username = user_data['login']
        
        return self.search_prs(f"author:{username}", state, limit)
    
    def get_repo_prs(self, repo_url: str, state: str = "open", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs from a specific repository"""
        owner, repo = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        params = {
            'state': state,
            'per_page': limit,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        self.logger.debug(f"Fetching PRs from {owner}/{repo}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        for pr in response.json():
            results.append({
                'id': pr['number'],
                'title': pr['title'],
                'state': pr['state'],
                'url': pr['html_url'],
                'repo_owner': owner,
                'repo_name': repo,
                'repo_url': f"https://github.com/{owner}/{repo}",
                'created_at': pr['created_at'],
                'updated_at': pr['updated_at'],
                'user': pr['user']['login']
            })
        
        return results
    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        # Convert https://github.com/owner/repo.git to (owner, repo)
        parts = repo_url.rstrip('/').replace('.git', '').split('/')
        return parts[-2], parts[-1]