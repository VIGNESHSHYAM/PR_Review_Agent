import argparse
from typing import List

from addict import Dict
from traitlets import Any
from pr_review_agent import PRReviewAgent
from utils.config import load_config
from utils.logger import setup_logger

def display_prs(prs: List[Dict[str, Any]]):
    if not prs:
        print("No pull requests found.")
        return
    
    print(f"{'ID':<8} {'Repository':<30} {'Title':<50} {'State':<10} {'URL'}")
    print("-" * 120)
    
    for pr in prs:
        repo_name = f"{pr['repo_owner']}/{pr['repo_name']}"
        if len(repo_name) > 28:
            repo_name = repo_name[:25] + "..."
        
        title = pr['title']
        if len(title) > 48:
            title = title[:45] + "..."
        
        print(f"{pr['id']:<8} {repo_name:<30} {title:<50} {pr['state']:<10} {pr['url']}")

def main():
    # Set up logging
    logger = setup_logger()
    
    # Load configuration
    config = load_config()
    
    parser = argparse.ArgumentParser(description='PR Review Agent')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Review a specific PR')
    review_parser.add_argument('--server', choices=['github', 'gitlab'], default='github', help='Git server')
    review_parser.add_argument('--repo', required=True, help='Repository URL')
    review_parser.add_argument('--pr', type=int, required=True, help='Pull request ID')
    review_parser.add_argument('--post-comments', action='store_true', help='Post comments to the PR')
    review_parser.add_argument('--github-token', help='GitHub access token', default=config.get('GITHUB_TOKEN'))
    review_parser.add_argument('--gitlab-token', help='GitLab access token', default=config.get('GITLAB_TOKEN'))
    review_parser.add_argument('--gitlab-url', help='GitLab instance URL', default=config.get('GITLAB_URL', 'https://gitlab.com'))
    review_parser.add_argument('--gemini-key', help='Gemini API key', default=config.get('GEMINI_API_KEY'))
    review_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for PRs')
    search_parser.add_argument('--server', choices=['github', 'gitlab'], default='github', help='Git server')
    search_parser.add_argument('--query', help='Search query')
    search_parser.add_argument('--user', help='Username to filter PRs by author')
    search_parser.add_argument('--repo', help='Repository URL to filter PRs by repository')
    search_parser.add_argument('--state', choices=['open', 'closed', 'all'], default='open', help='PR state')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results to return')
    search_parser.add_argument('--github-token', help='GitHub access token', default=config.get('GITHUB_TOKEN'))
    search_parser.add_argument('--gitlab-token', help='GitLab access token', default=config.get('GITLAB_TOKEN'))
    search_parser.add_argument('--gitlab-url', help='GitLab instance URL', default=config.get('GITLAB_URL', 'https://gitlab.com'))
    search_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create agent
    agent = PRReviewAgent(
        git_server=args.server,
        github_token=args.github_token,
        gitlab_token=args.gitlab_token,
        gitlab_url=args.gitlab_url,
        gemini_api_key=args.gemini_key if hasattr(args, 'gemini_key') else None,
        verbose=args.verbose
    )
    
    if args.command == 'review':
        # Review PR
        try:
            result = agent.review_pr(args.repo, args.pr, args.post_comments)
            
            # Print results
            print(f"PR Title: {result['pr_details'].get('title')}")
            print(f"Quality Score: {result['score']:.1f}/100")
            print(f"Feedback Items: {len(result['feedback'])}")
            
            for i, item in enumerate(result['feedback'], 1):
                print(f"\n{i}. [{item['type'].upper()}] {item['message']}")
                if item.get('line'):
                    print(f"   Line: {item['line']}")
                if item.get('code_snippet'):
                    print(f"   Code: {item['code_snippet']}")
                    
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    elif args.command == 'search':
        try:
            prs = agent.search_prs(
                query=args.query,
                state=args.state,
                limit=args.limit,
                username=args.user,
                repo_url=args.repo
            )
            display_prs(prs)
        except Exception as e:
            logger.error(f"Error searching PRs: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()