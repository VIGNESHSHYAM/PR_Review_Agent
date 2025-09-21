import os
import requests
from typing import Dict, Any, List
from .base_adapter import GitServerAdapter
from utils.logger import get_logger

class GitLabAdapter(GitServerAdapter):
    """Adapter for GitLab"""
    
    def __init__(self, token: str = None, base_url: str = "https://gitlab.com"):
        self.token = token or os.environ.get('GITLAB_TOKEN')
        self.base_url = base_url.rstrip('/')
        self.headers = {'Private-Token': self.token}
        self.logger = get_logger()
    
    def get_pr_details(self, repo_url: str, pr_id: int) -> Dict[str, Any]:
        project_id = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{pr_id}"
        
        self.logger.debug(f"Fetching PR details from {url}")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_diff(self, repo_url: str, pr_id: int) -> str:
        project_id = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{pr_id}/changes"
        
        self.logger.debug(f"Fetching diff from {url}")
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        changes = response.json()
        
        # Format changes as a unified diff
        diff_lines = []
        for change in changes.get('changes', []):
            diff_lines.append(f"--- a/{change['old_path']}")
            diff_lines.append(f"+++ b/{change['new_path']}")
            diff_lines.extend(change['diff'].split('\n'))
        
        return '\n'.join(diff_lines)
    
    def post_comment(self, repo_url: str, pr_id: int, comment: str, path: str = None, line: int = None):
        project_id = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{pr_id}/notes"
        
        payload = {"body": comment}
        if path and line:
            # For GitLab, we need more context to create a position-based comment
            pr_details = self.get_pr_details(repo_url, pr_id)
            payload["position"] = {
                "base_sha": pr_details.get('diff_refs', {}).get('base_sha'),
                "start_sha": pr_details.get('diff_refs', {}).get('start_sha'),
                "head_sha": pr_details.get('diff_refs', {}).get('head_sha'),
                "position_type": "text",
                "new_path": path,
                "new_line": line
            }
            
        self.logger.debug(f"Posting comment to {url}")
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_prs(self, query: str, state: str = "opened", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for merge requests across GitLab"""
        url = f"{self.base_url}/api/v4/merge_requests"
        
        params = {
            'scope': 'all',
            'search': query,
            'state': state,
            'per_page': limit,
            'order_by': 'updated_at',
            'sort': 'desc'
        }
        
        self.logger.debug(f"Searching PRs with query: {query}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        for mr in response.json():
            # Get project details to extract repo info
            project_url = f"{self.base_url}/api/v4/projects/{mr['project_id']}"
            project_response = requests.get(project_url, headers=self.headers)
            
            if project_response.status_code == 200:
                project = project_response.json()
                repo_name = project['name']
                repo_owner = project['namespace']['full_path']
                repo_url = project['web_url']
            else:
                repo_name = f"project-{mr['project_id']}"
                repo_owner = "unknown"
                repo_url = f"{self.base_url}/projects/{mr['project_id']}"
            
            results.append({
                'id': mr['iid'],
                'title': mr['title'],
                'state': mr['state'],
                'url': mr['web_url'],
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': mr['created_at'],
                'updated_at': mr['updated_at'],
                'user': mr['author']['username']
            })
        
        return results
    
    def get_user_prs(self, username: str = None, state: str = "opened", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs created by a specific user"""
        if not username:
            # Get authenticated user's PRs
            url = f"{self.base_url}/api/v4/user"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            user_data = response.json()
            username = user_data['username']
        
        url = f"{self.base_url}/api/v4/merge_requests"
        
        params = {
            'author_username': username,
            'state': state,
            'per_page': limit,
            'order_by': 'updated_at',
            'sort': 'desc'
        }
        
        self.logger.debug(f"Fetching PRs for user: {username}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        for mr in response.json():
            # Get project details
            project_url = f"{self.base_url}/api/v4/projects/{mr['project_id']}"
            project_response = requests.get(project_url, headers=self.headers)
            
            if project_response.status_code == 200:
                project = project_response.json()
                repo_name = project['name']
                repo_owner = project['namespace']['full_path']
                repo_url = project['web_url']
            else:
                repo_name = f"project-{mr['project_id']}"
                repo_owner = "unknown"
                repo_url = f"{self.base_url}/projects/{mr['project_id']}"
            
            results.append({
                'id': mr['iid'],
                'title': mr['title'],
                'state': mr['state'],
                'url': mr['web_url'],
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': mr['created_at'],
                'updated_at': mr['updated_at'],
                'user': mr['author']['username']
            })
        
        return results
    
    def get_repo_prs(self, repo_url: str, state: str = "opened", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs from a specific repository"""
        project_id = self._parse_repo_url(repo_url)
        url = f"{self.base_url}/api/v4/projects/{project_id}/merge_requests"
        
        params = {
            'state': state,
            'per_page': limit,
            'order_by': 'updated_at',
            'sort': 'desc'
        }
        
        self.logger.debug(f"Fetching PRs from project: {project_id}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        # Get project details
        project_url = f"{self.base_url}/api/v4/projects/{project_id}"
        project_response = requests.get(project_url, headers=self.headers)
        
        if project_response.status_code == 200:
            project = project_response.json()
            repo_name = project['name']
            repo_owner = project['namespace']['full_path']
            repo_url = project['web_url']
        else:
            repo_name = f"project-{project_id}"
            repo_owner = "unknown"
            repo_url = f"{self.base_url}/projects/{project_id}"
        
        results = []
        for mr in response.json():
            results.append({
                'id': mr['iid'],
                'title': mr['title'],
                'state': mr['state'],
                'url': mr['web_url'],
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': mr['created_at'],
                'updated_at': mr['updated_at'],
                'user': mr['author']['username']
            })
        
        return results
    
    def _parse_repo_url(self, repo_url: str) -> str:
        # Convert https://gitlab.com/owner/repo.git to URL-encoded project ID
        parts = repo_url.replace('.git', '').strip('/').split('/')
        project_path = f"{parts[-2]}/{parts[-1]}"
        return requests.utils.quote(project_path, safe='')