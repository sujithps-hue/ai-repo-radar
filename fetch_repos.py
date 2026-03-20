#!/usr/bin/env python3
"""
AI Repo Radar - GitHub API Fetcher
Fetches trending AI repositories and outputs structured JSON
"""

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

# GitHub API configuration
GITHUB_API = "https://api.github.com/search/repositories"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    # Add your GitHub token here for higher rate limits (optional but recommended)
    # "Authorization": "token YOUR_GITHUB_TOKEN"
}

# Niche classification keywords
NICHE_MAP = {
    'Healthcare AI': ['health', 'medical', 'clinical', 'ehr', 'fhir', 'patient', 'diagnosis', 'healthcare'],
    'LLMs': ['llm', 'language-model', 'gpt', 'transformer', 'bert', 'nlp', 'chatbot'],
    'Agents': ['agent', 'autonomous', 'langchain', 'autogen', 'multi-agent'],
    'MLOps': ['mlops', 'mlflow', 'kubeflow', 'deployment', 'monitoring', 'pipeline'],
    'Data': ['data', 'dataset', 'etl', 'pipeline', 'warehouse', 'lakehouse'],
    'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'serverless', 'kubernetes']
}

LANG_COLORS = {
    'Python': '#3572A5',
    'JavaScript': '#f1e05a',
    'TypeScript': '#2b7489',
    'Java': '#b07219',
    'C++': '#f34b7d',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'Ruby': '#701516'
}

def classify_niche(repo):
    """Classify repo into niches based on topics and description"""
    niches = []
    text = (repo.get('description', '') + ' ' + ' '.join(repo.get('topics', []))).lower()
    
    for niche, keywords in NICHE_MAP.items():
        if any(kw in text for kw in keywords):
            niches.append(niche)
    
    return niches if niches else ['General AI']

def determine_trend(stars_today, age_days):
    """Determine if repo is 'hot', 'new', or 'trending'"""
    if age_days <= 7:
        return 'new'
    elif stars_today > 500:
        return 'hot'
    else:
        return 'trending'

def fetch_trending_repos(days_back=7, max_repos=50):
    """Fetch trending AI repos from GitHub"""
    date_threshold = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Multiple search queries to capture different AI repos
    queries = [
        f"topic:ai created:>{date_threshold}",
        f"topic:machine-learning stars:>100 pushed:>{date_threshold}",
        f"topic:deep-learning stars:>50 pushed:>{date_threshold}",
        f"artificial intelligence in:description stars:>100 pushed:>{date_threshold}"
    ]
    
    all_repos = {}
    
    for query in queries:
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': 30
        }
        
        try:
            response = requests.get(GITHUB_API, headers=HEADERS, params=params)
            response.raise_for_status()
            data = response.json()
            
            for repo in data.get('items', []):
                repo_id = repo['id']
                if repo_id not in all_repos:
                    all_repos[repo_id] = repo
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos: {e}")
            continue
    
    return list(all_repos.values())[:max_repos]

def format_number(num):
    """Format number to k/M notation"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)

def process_repos(raw_repos):
    """Process raw GitHub API data into frontend format"""
    processed = []
    
    for idx, repo in enumerate(raw_repos, 1):
        # Calculate approximate stars gained today (simplified)
        total_stars = repo['stargazers_count']
        age_days = (datetime.now() - datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')).days
        stars_per_day = total_stars / max(age_days, 1)
        stars_today = int(stars_per_day)
        
        niches = classify_niche(repo)
        trend = determine_trend(stars_today, age_days)
        
        # Extract main topic
        topics = repo.get('topics', [])
        main_topic = topics[0].replace('-', ' ').title() if topics else 'AI'
        
        processed_repo = {
            'rank': idx,
            'name': repo['full_name'],
            'owner': repo['owner']['login'],
            'desc': repo['description'] or 'No description available',
            'stars': format_number(total_stars),
            'forks': format_number(repo['forks_count']),
            'lang': repo.get('language', 'Unknown'),
            'langColor': LANG_COLORS.get(repo.get('language', ''), '#8b949e'),
            'niche': niches,
            'trend': trend,
            'starsToday': f"+{stars_today}" if stars_today > 0 else "+1",
            'topic': main_topic,
            'url': repo['html_url']
        }
        
        processed.append(processed_repo)
    
    return processed

def main():
    """Main execution function"""
    print("🔍 Fetching trending AI repositories from GitHub...")
    
    raw_repos = fetch_trending_repos(days_back=30, max_repos=50)
    print(f"✓ Found {len(raw_repos)} repositories")
    
    print("📊 Processing and classifying repositories...")
    processed_repos = process_repos(raw_repos)
    
    output = {
        'updated': datetime.now().isoformat(),
        'count': len(processed_repos),
        'repos': processed_repos
    }
    
    # Write to JSON file
    with open('repos.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Successfully wrote {len(processed_repos)} repos to repos.json")
    print(f"📅 Last updated: {output['updated']}")

if __name__ == "__main__":
    main()
