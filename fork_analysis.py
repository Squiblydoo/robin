import requests
import os
from datetime import datetime
from typing import List, Dict, Optional

class ForkAnalyzer:
    """Analyzes GitHub repository forks to find those ahead of the parent."""
    
    def __init__(self, owner: str, repo: str, github_token: Optional[str] = None):
        """
        Initialize the ForkAnalyzer.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            github_token: GitHub personal access token (optional, for higher rate limits)
        """
        self.owner = owner
        self.repo = repo
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Robin-Fork-Analyzer"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    def get_forks(self) -> List[Dict]:
        """
        Fetch all forks of the repository.
        
        Returns:
            List of fork information dictionaries
        """
        forks = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/forks"
            params = {
                "per_page": per_page,
                "page": page,
                "sort": "newest"
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 403:
                    if 'rate limit exceeded' in response.text.lower():
                        print(f"\n⚠️  GitHub API rate limit exceeded.")
                        print("💡 Tip: Set GITHUB_TOKEN environment variable to increase rate limit.")
                        print("   You can create a personal access token at: https://github.com/settings/tokens")
                    else:
                        print(f"\n⚠️  GitHub API access forbidden: {response.status_code}")
                        print("💡 Repository might be private or access is restricted.")
                    break
                
                response.raise_for_status()
                
                page_forks = response.json()
                if not page_forks:
                    break
                
                forks.extend(page_forks)
                page += 1
                
                # Stop if we've retrieved all forks
                if len(page_forks) < per_page:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching forks: {e}")
                break
        
        return forks
    
    def get_default_branch(self, owner: str, repo: str) -> str:
        """
        Get the default branch of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Default branch name
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get("default_branch", "main")
        except requests.exceptions.RequestException:
            return "main"
    
    def compare_with_parent(self, fork_owner: str, fork_repo: str) -> Optional[Dict]:
        """
        Compare a fork with the parent repository.
        
        Args:
            fork_owner: Fork owner username
            fork_repo: Fork repository name
            
        Returns:
            Dictionary with comparison details or None if comparison fails
        """
        # Get default branches
        parent_branch = self.get_default_branch(self.owner, self.repo)
        fork_branch = self.get_default_branch(fork_owner, fork_repo)
        
        # Compare using GitHub's compare API
        url = f"{self.base_url}/repos/{fork_owner}/{fork_repo}/compare/{self.owner}:{parent_branch}...{fork_owner}:{fork_branch}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "ahead_by": data.get("ahead_by", 0),
                "behind_by": data.get("behind_by", 0),
                "total_commits": data.get("total_commits", 0),
                "status": data.get("status", "unknown")
            }
        except requests.exceptions.RequestException as e:
            print(f"Error comparing {fork_owner}/{fork_repo}: {e}")
            return None
    
    def analyze_forks(self, min_ahead_commits: int = 1) -> List[Dict]:
        """
        Analyze all forks and identify those ahead of the parent.
        
        Args:
            min_ahead_commits: Minimum number of commits ahead to be considered substantial
            
        Returns:
            List of forks that are substantially ahead
        """
        print(f"Fetching forks of {self.owner}/{self.repo}...")
        forks = self.get_forks()
        print(f"Found {len(forks)} forks. Analyzing...")
        
        ahead_forks = []
        
        for i, fork in enumerate(forks, 1):
            fork_owner = fork["owner"]["login"]
            fork_name = fork["name"]
            
            print(f"[{i}/{len(forks)}] Analyzing {fork_owner}/{fork_name}...")
            
            comparison = self.compare_with_parent(fork_owner, fork_name)
            
            if comparison and comparison["ahead_by"] >= min_ahead_commits:
                ahead_forks.append({
                    "owner": fork_owner,
                    "name": fork_name,
                    "html_url": fork["html_url"],
                    "description": fork.get("description", ""),
                    "stars": fork.get("stargazers_count", 0),
                    "updated_at": fork.get("updated_at", ""),
                    "ahead_by": comparison["ahead_by"],
                    "behind_by": comparison["behind_by"],
                    "total_commits": comparison["total_commits"]
                })
        
        # Sort by commits ahead (descending)
        ahead_forks.sort(key=lambda x: x["ahead_by"], reverse=True)
        
        return ahead_forks
    
    def generate_report(self, ahead_forks: List[Dict]) -> str:
        """
        Generate a human-readable report of forks ahead of the parent.
        
        Args:
            ahead_forks: List of fork information dictionaries
            
        Returns:
            Formatted report string
        """
        if not ahead_forks:
            return f"\n✅ No forks are ahead of {self.owner}/{self.repo}\n"
        
        report = [
            f"\n{'='*70}",
            f"Fork Analysis Report for {self.owner}/{self.repo}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*70}\n",
            f"Found {len(ahead_forks)} fork(s) ahead of the parent repository:\n"
        ]
        
        for i, fork in enumerate(ahead_forks, 1):
            report.extend([
                f"{i}. {fork['owner']}/{fork['name']}",
                f"   URL: {fork['html_url']}",
                f"   ⭐ Stars: {fork['stars']}",
                f"   📊 Commits ahead: {fork['ahead_by']}",
                f"   📊 Commits behind: {fork['behind_by']}",
                f"   📅 Last updated: {fork['updated_at']}",
            ])
            
            if fork['description']:
                report.append(f"   📝 Description: {fork['description']}")
            
            report.append("")
        
        report.extend([
            f"{'='*70}",
            "💡 Consider reviewing these forks for potential improvements",
            "   or features that could be merged back to the parent repository.",
            f"{'='*70}\n"
        ])
        
        return "\n".join(report)


def analyze_repository_forks(owner: str, repo: str, 
                             min_ahead_commits: int = 1,
                             github_token: Optional[str] = None) -> str:
    """
    Convenience function to analyze repository forks.
    
    Args:
        owner: Repository owner
        repo: Repository name
        min_ahead_commits: Minimum commits ahead to be considered substantial
        github_token: GitHub personal access token (optional)
        
    Returns:
        Report string
    """
    analyzer = ForkAnalyzer(owner, repo, github_token)
    ahead_forks = analyzer.analyze_forks(min_ahead_commits)
    return analyzer.generate_report(ahead_forks)
