# pr_review_agent.py
import os
from typing import List, Dict, Any
from adapters import GitHubAdapter, GitLabAdapter, BitbucketAdapter, AzureDevOpsAdapter
from analyzers import CodeAnalyzer
from utils.logger import get_logger

class PRReviewAgent:
    """Main PR Review Agent class"""
    
    def __init__(self, git_server: str = 'github', **kwargs):
        self.git_server = git_server.lower()
        self.adapter = self._create_adapter(git_server, kwargs)
        self.analyzer = CodeAnalyzer(
            gemini_api_key=kwargs.get('gemini_api_key'),
            verbose=kwargs.get('verbose', False)
        )
        self.logger = get_logger()
        self.verbose = kwargs.get('verbose', False)
    
    def _create_adapter(self, git_server: str, kwargs: dict):
        if git_server == 'github':
            return GitHubAdapter(kwargs.get('github_token'))
        elif git_server == 'gitlab':
            return GitLabAdapter(
                kwargs.get('gitlab_token'),
                kwargs.get('gitlab_url', 'https://gitlab.com')
            )
        elif git_server == 'bitbucket':
            return BitbucketAdapter(
                kwargs.get('bitbucket_token'),
                kwargs.get('bitbucket_url', 'https://api.bitbucket.org/2.0')
            )
        elif git_server == 'azure':
            return AzureDevOpsAdapter(
                kwargs.get('azure_devops_token'),
                kwargs.get('azure_devops_org_url')
            )
        else:
            raise ValueError(f"Unsupported git server: {git_server}")
    
    def search_prs(self, query: str = None, state: str = "open", limit: int = 10, 
                  username: str = None, repo_url: str = None) -> List[Dict[str, Any]]:
        """Search for pull requests"""
        if repo_url:
            return self.adapter.get_repo_prs(repo_url, state, limit)
        elif username:
            return self.adapter.get_user_prs(username, state, limit)
        elif query:
            return self.adapter.search_prs(query, state, limit)
        else:
            # Default: get authenticated user's PRs
            return self.adapter.get_user_prs(None, state, limit)
    
    # Existing methods for review_pr, _calculate_score, etc.
    
    def review_pr(self, repo_url: str, pr_id: int, post_comments: bool = False) -> Dict[str, Any]:
        """Review a pull request and optionally post comments"""
        self.logger.info(f"Reviewing PR #{pr_id} in {repo_url}")
        
        # Get PR details and diff
        pr_details = self.adapter.get_pr_details(repo_url, pr_id)
        diff = self.adapter.get_diff(repo_url, pr_id)
        
        if self.verbose:
            self.logger.debug(f"Retrieved diff with {len(diff)} characters")
        
        # Analyze the code changes
        feedback = self.analyzer.analyze_diff(diff)
        
        # Calculate a score based on feedback
        score = self._calculate_score(feedback)
        
        # Post comments if requested
        if post_comments:
            self._post_feedback_comments(repo_url, pr_id, feedback)
        
        return {
            "pr_details": pr_details,
            "feedback": feedback,
            "score": score
        }
    
    
    def _calculate_score(self, feedback: List[Dict[str, Any]]) -> float:
        """Calculate a quality score based on feedback"""
        if not feedback:
            return 100.0  # Perfect score if no issues found
        
        # Weight different types of feedback
        weights = {
            "error": 5.0,
            "warning": 2.0,
            "info": 0.5,
            "suggestion": 0.2
        }
        
        # Start with a perfect score and deduct for issues
        score = 100.0
        for item in feedback:
            score -= weights.get(item.get('type', 'info'), 0.5)
        
        return max(0.0, min(100.0, score))  # Ensure score is between 0-100
    
    def _post_feedback_comments(self, repo_url: str, pr_id: int, feedback: List[Dict[str, Any]]):
        """Post feedback as comments on the PR"""
        self.logger.info(f"Posting {len(feedback)} comments to PR #{pr_id}")
        
        for item in feedback:
            message = f"**{item['type'].upper()}**: {item['message']}"
            if item.get('code_snippet'):
                message += f"\n\n```\n{item['code_snippet']}\n```"
            
            try:
                self.adapter.post_comment(
                    repo_url, 
                    pr_id, 
                    message,
                    item.get('path'),
                    item.get('line')
                )
                self.logger.debug(f"Posted comment: {item['type']} - {item['message'][:50]}...")
            except Exception as e:
                self.logger.error(f"Failed to post comment: {e}")