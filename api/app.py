import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from typing import Dict, Any, List

import sys
sys.path.append('..')

from pr_review_agent import PRReviewAgent
from utils.logger import setup_logger

load_dotenv()

app = Flask(__name__)
CORS(app)  

logger = setup_logger()

SUPPORTED_SERVERS = {
    'github': {
        'name': 'GitHub',
        'env_token': 'GITHUB_TOKEN',
        'default_url': 'https://github.com'
    },
    'gitlab': {
        'name': 'GitLab',
        'env_token': 'GITLAB_TOKEN',
        'env_url': 'GITLAB_URL',
        'default_url': 'https://gitlab.com'
    },
    'bitbucket': {
        'name': 'Bitbucket',
        'env_token': 'BITBUCKET_TOKEN',
        'default_url': 'https://bitbucket.org'
    },
    'azure': {
        'name': 'Azure DevOps',
        'env_token': 'AZURE_DEVOPS_TOKEN',
        'env_url': 'AZURE_DEVOPS_ORG_URL'
    }
}

@app.route('/api/health', methods=['GET'])
def health_check():

    return jsonify({
        'status': 'healthy',
        'message': 'PR Review Agent API is running',
        'supported_servers': list(SUPPORTED_SERVERS.keys())
    })

@app.route('/api/servers', methods=['GET'])
def list_servers():

    servers_info = {}
    
    for server_id, server_info in SUPPORTED_SERVERS.items():
        has_token = os.environ.get(server_info['env_token']) is not None
        server_url = os.environ.get(server_info.get('env_url', ''), server_info.get('default_url', ''))
        
        servers_info[server_id] = {
            'name': server_info['name'],
            'configured': has_token,
            'url': server_url
        }
    
    return jsonify(servers_info)

@app.route('/api/search', methods=['GET'])
def search_prs():

    try:
        server = request.args.get('server', 'github')
        query = request.args.get('query')
        username = request.args.get('user')
        repo_url = request.args.get('repo')
        state = request.args.get('state', 'open')
        limit = int(request.args.get('limit', 10))
        
        if server not in SUPPORTED_SERVERS:
            return jsonify({'error': f'Unsupported server: {server}'}), 400
        
        agent_config = _get_agent_config(server)
        agent = PRReviewAgent(git_server=server, **agent_config)
        
        state_map = {
            'github': {
                'open': 'open',
                'closed': 'closed',
                'all': 'all'
            },
            'gitlab': {
                'open': 'opened',
                'closed': 'closed',
                'all': 'all'
            },
            'bitbucket': {
                'open': 'OPEN',
                'closed': 'MERGED',
                'all': 'ALL'
            },
            'azure': {
                'open': 'active',
                'closed': 'completed',
                'all': 'all'
            }
        }
        
        server_state = state_map[server][state]
        
        prs = agent.search_prs(
            query=query,
            state=server_state,
            limit=limit,
            username=username,
            repo_url=repo_url
        )
        
        return jsonify({
            'server': server,
            'query': query,
            'state': state,
            'results': prs
        })
        
    except Exception as e:
        logger.error(f"Error searching PRs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/review', methods=['POST'])
def review_pr():
    try:
        data = request.get_json()
        
        server = data.get('server', 'github')
        repo_url = data.get('repo_url')
        pr_id = data.get('pr_id')
        post_comments = data.get('post_comments', False)
        
        if not repo_url or not pr_id:
            return jsonify({'error': 'repo_url and pr_id are required'}), 400
        
        if server not in SUPPORTED_SERVERS:
            return jsonify({'error': f'Unsupported server: {server}'}), 400
        
        agent_config = _get_agent_config(server)
        agent = PRReviewAgent(git_server=server, **agent_config)
        
        result = agent.review_pr(repo_url, pr_id, post_comments)
        
        return jsonify({
            'server': server,
            'repo_url': repo_url,
            'pr_id': pr_id,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        return jsonify({'error': str(e)}), 500

def _get_agent_config(server: str) -> Dict[str, Any]:

    server_info = SUPPORTED_SERVERS[server]
    config = {}
    
    # Add token
    token = os.environ.get(server_info['env_token'])
    if token:
        config[f'{server}_token'] = token
    
    if 'env_url' in server_info:
        url = os.environ.get(server_info['env_url'])
        if url:
            config[f'{server}_url'] = url
    
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        config['gemini_api_key'] = gemini_key
    
    return config

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)