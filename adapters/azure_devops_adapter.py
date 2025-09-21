# adapters/azure_devops_adapter.py
import os
import requests
from typing import Dict, Any, List
from .base_adapter import GitServerAdapter
from utils.logger import get_logger

class AzureDevOpsAdapter(GitServerAdapter):
    """Adapter for Azure DevOps"""
    
    def __init__(self, token: str = None, org_url: str = None):
        self.token = token or os.environ.get('AZURE_DEVOPS_TOKEN')
        self.org_url = org_url or os.environ.get('AZURE_DEVOPS_ORG_URL')
        self.headers = {
            'Authorization': f'Basic {self.token}',
            'Accept': 'application/json'
        }
        self.logger = get_logger()
    
    def search_prs(self, query: str, state: str = "active", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for pull requests across Azure DevOps"""
        # Azure DevOps doesn't have a direct PR search API, so we list PRs and filter
        url = f"{self.org_url}/_apis/git/pullrequests"
        params = {
            'searchCriteria.status': state,
            '$top': limit
        }
        
        self.logger.debug(f"Searching Azure DevOps PRs with query: {query}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('value', []):
            repo_name = pr['repository']['name']
            repo_url = pr['repository']['remoteUrl']
            repo_owner = self.org_url.split('/')[-1]  # Organization name
            
            # Filter by query if provided
            if query.lower() not in pr['title'].lower() and query.lower() not in pr.get('description', '').lower():
                continue
            
            results.append({
                'id': pr['pullRequestId'],
                'title': pr['title'],
                'state': pr['status'],
                'url': f"{self.org_url}/_git/{repo_name}/pullrequest/{pr['pullRequestId']}",
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': pr['creationDate'],
                'updated_at': pr['lastMergeCommit']['date'] if 'lastMergeCommit' in pr else pr['creationDate'],
                'user': pr['createdBy']['displayName']
            })
        
        return results
    
    def get_user_prs(self, username: str = None, state: str = "active", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs created by a specific user"""
        if not username:
            # Get authenticated user's PRs
            user_url = f"{self.org_url}/_apis/user"
            user_response = requests.get(user_url, headers=self.headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            username = user_data['displayName']
        
        url = f"{self.org_url}/_apis/git/pullrequests"
        params = {
            'searchCriteria.status': state,
            'searchCriteria.creatorId': username,
            '$top': limit
        }
        
        self.logger.debug(f"Fetching PRs for user: {username}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('value', []):
            repo_name = pr['repository']['name']
            repo_url = pr['repository']['remoteUrl']
            repo_owner = self.org_url.split('/')[-1]
            
            results.append({
                'id': pr['pullRequestId'],
                'title': pr['title'],
                'state': pr['status'],
                'url': f"{self.org_url}/_git/{repo_name}/pullrequest/{pr['pullRequestId']}",
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': pr['creationDate'],
                'updated_at': pr['lastMergeCommit']['date'] if 'lastMergeCommit' in pr else pr['creationDate'],
                'user': pr['createdBy']['displayName']
            })
        
        return results
    
    def get_repo_prs(self, repo_url: str, state: str = "active", limit: int = 10) -> List[Dict[str, Any]]:
        """Get PRs from a specific repository"""
        # Parse repo ID from URL
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        url = f"{self.org_url}/_apis/git/repositories/{repo_name}/pullrequests"
        params = {
            'searchCriteria.status': state,
            '$top': limit
        }
        
        self.logger.debug(f"Fetching PRs from repository: {repo_name}")
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        results = []
        data = response.json()
        
        for pr in data.get('value', []):
            repo_owner = self.org_url.split('/')[-1]
            
            results.append({
                'id': pr['pullRequestId'],
                'title': pr['title'],
                'state': pr['status'],
                'url': f"{self.org_url}/_git/{repo_name}/pullrequest/{pr['pullRequestId']}",
                'repo_owner': repo_owner,
                'repo_name': repo_name,
                'repo_url': repo_url,
                'created_at': pr['creationDate'],
                'updated_at': pr['lastMergeCommit']['date'] if 'lastMergeCommit' in pr else pr['creationDate'],
                'user': pr['createdBy']['displayName']
            })
        
        return results
    
    # Implement other required methods (get_pr_details, get_diff, post_comment)
    def get_pr_details(self, repo_url: str, pr_id: int) -> Dict[str, Any]:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        url = f"{self.org_url}/_apis/git/repositories/{repo_name}/pullrequests/{pr_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_diff(self, repo_url: str, pr_id: int) -> str:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        url = f"{self.org_url}/_apis/git/repositories/{repo_name}/pullrequests/{pr_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        # Azure DevOps doesn't provide a direct diff endpoint, so we generate it from commits
        pr_details = response.json()
        target_commit = pr_details['lastMergeTargetCommit']['commitId']
        source_commit = pr_details['lastMergeSourceCommit']['commitId']
        
        diff_url = f"{self.org_url}/_apis/git/repositories/{repo_name}/diffs/commits"
        diff_params = {
            'baseVersion': target_commit,
            'targetVersion': source_commit,
            'diffCommonCommit': True
        }
        
        diff_response = requests.get(diff_url, headers=self.headers, params=diff_params)
        diff_response.raise_for_status()
        return diff_response.text
    
    def post_comment(self, repo_url: str, pr_id: int, comment: str, path: str = None, line: int = None):
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        url = f"{self.org_url}/_apis/git/repositories/{repo_name}/pullrequests/{pr_id}/threads"
        
        payload = {
            "comments": [
                {
                    "parentCommentId": 0,
                    "content": comment,
                    "commentType": 1
                }
            ],
            "status": 1
        }
        
        if path and line:
            payload["threadContext"] = {
                "filePath": path,
                "rightFileStart": {
                    "line": line,
                    "offset": 1
                },
                "rightFileEnd": {
                    "line": line,
                    "offset": 1
                }
            }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()