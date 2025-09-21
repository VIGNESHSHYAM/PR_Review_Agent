# adapters/bitbucket_adapter.py
import os
import requests
from typing import Dict, Any, List
from .base_adapter import GitServerAdapter
from utils.logger import get_logger

class BitbucketAdapter(GitServerAdapter):
    """Adapter for Bitbucket Cloud and Server"""
    
    def __init__(self, token: str = None, base_url: str = "https://api.bitbucket.org/2.0"):
        self.token = token or os.environ.get('BITBUCKET_TOKEN')
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
        self.logger = get_logger()
    
    def search_prs(self, query: str, state: str = "OPEN", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for pull requests across Bitbucket"""
        url = f"{self.base_url}/pullrequests"
        params = {
            'q': f'state = "{state}" AND (title ~ "{query}" OR description ~ "{query}")',
            'pagelen': limit,
            'sort': '-updated_on'
        }
        
        self.logger.debug(f"Searching Bitbucket PRs with query: {query}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('values', []):
            # Extract repository details
            repo_url = pr['source']['repository']['links']['html']['href']
            repo_name = pr['source']['repository']['name']
            repo_owner = pr['source']['repository']['full_name'].split('/')[0]
            
            results.append({
                'id': pr['id'],
                'title': pr['title'],
                'state': pr['state'],
                'url': pr['links']['html']['href'],
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': pr['created_on'],
                'updated_at': pr['updated_on'],
                'user': pr['author']['display_name']
            })
        
        return results
    
    def get_user_prs(self, username: str = None, state: str = "OPEN", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs created by a specific user"""
        if not username:
            # Get authenticated user's PRs
            user_url = f"{self.base_url}/user"
            user_response = requests.get(user_url, headers=self.headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            username = user_data['username']
        
        url = f"{self.base_url}/pullrequests/{username}"
        params = {
            'state': state,
            'pagelen': limit,
            'sort': '-updated_on'
        }
        
        self.logger.debug(f"Fetching PRs for user: {username}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('values', []):
            repo_url = pr['source']['repository']['links']['html']['href']
            repo_name = pr['source']['repository']['name']
            repo_owner = pr['source']['repository']['full_name'].split('/')[0]
            
            results.append({
                'id': pr['id'],
                'title': pr['title'],
                'state': pr['state'],
                'url': pr['links']['html']['href'],
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': pr['created_on'],
                'updated_at': pr['updated_on'],
                'user': pr['author']['display_name']
            })
        
        return results
    
    def get_repo_prs(self, repo_url: str, state: str = "OPEN", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs from a specific repository"""
        # Parse owner and repo from URL
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1].replace('.git', '')
        
        url = f"{self.base_url}/repositories/{owner}/{repo}/pullrequests"
        params = {
            'state': state,
            'pagelen': limit,
            'sort': '-updated_on'
        }
        
        self.logger.debug(f"Fetching PRs from {owner}/{repo}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('values', []):
            results.append({
                'id': pr['id'],
                'title': pr['title'],
                'state': pr['state'],
                'url': pr['links']['html']['href'],
                'repo_owner': owner,
                'repo_name': repo,
                'repo_url': repo_url,
                'created_at': pr['created_on'],
                'updated_at': pr['updated_on'],
                'user': pr['author']['display_name']
            })
        
        return results
    
    # Implement other required methods (get_pr_details, get_diff, post_comment)
    def get_pr_details(self, repo_url: str, pr_id: int) -> Dict[str, Any]:
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1].replace('.git', '')
        
        url = f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{pr_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_diff(self, repo_url: str, pr_id: int) -> str:
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1].replace('.git', '')
        
        url = f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{pr_id}/diff"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def post_comment(self, repo_url: str, pr_id: int, comment: str, path: str = None, line: int = None):
        parts = repo_url.rstrip('/').split('/')
        owner = parts[-2]
        repo = parts[-1].replace('.git', '')
        
        url = f"{self.base_url}/repositories/{owner}/{repo}/pullrequests/{pr_id}/comments"
        
        payload = {
            "content": {
                "raw": comment
            }
        }
        
        if path and line:
            payload["inline"] = {
                "path": path,
                "to": line
            }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()