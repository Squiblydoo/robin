#!/usr/bin/env python3
"""
Test script for fork analysis functionality.
This demonstrates the feature with mock data when API is rate-limited.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fork_analysis import ForkAnalyzer

def test_with_mock_data():
    """Test fork analysis with mock data."""
    
    print("="*70)
    print("Fork Analysis Test - Using Mock Data")
    print("="*70)
    print()
    
    # Create analyzer instance
    analyzer = ForkAnalyzer("apurvsinghgautam", "robin")
    
    # Mock fork data (simulating what we'd get from GitHub API)
    mock_forks = [
        {
            "owner": {"login": "tekcin"},
            "name": "robin_scrapper",
            "html_url": "https://github.com/tekcin/robin_scrapper",
            "description": "Enhanced scrapper with additional features",
            "stargazers_count": 32,
            "updated_at": "2026-01-20T14:59:00Z"
        },
        {
            "owner": {"login": "Xer0bit"},
            "name": "Dark-Web-OSINT-Tool",
            "html_url": "https://github.com/Xer0bit/Dark-Web-OSINT-Tool",
            "description": "Dark Web OSINT with extra search engines",
            "stargazers_count": 4,
            "updated_at": "2025-12-24T09:13:00Z"
        },
        {
            "owner": {"login": "Magician83"},
            "name": "robin",
            "html_url": "https://github.com/Magician83/robin",
            "description": "",
            "stargazers_count": 1,
            "updated_at": "2025-04-16T15:38:00Z"
        }
    ]
    
    # Mock comparison data (simulating forks ahead of parent)
    mock_ahead_forks = [
        {
            "owner": "tekcin",
            "name": "robin_scrapper",
            "html_url": "https://github.com/tekcin/robin_scrapper",
            "description": "Enhanced scrapper with additional features",
            "stars": 32,
            "updated_at": "2026-01-20T14:59:00Z",
            "ahead_by": 15,
            "behind_by": 2,
            "total_commits": 15
        },
        {
            "owner": "Xer0bit",
            "name": "Dark-Web-OSINT-Tool",
            "html_url": "https://github.com/Xer0bit/Dark-Web-OSINT-Tool",
            "description": "Dark Web OSINT with extra search engines",
            "stars": 4,
            "updated_at": "2025-12-24T09:13:00Z",
            "ahead_by": 8,
            "behind_by": 5,
            "total_commits": 8
        }
    ]
    
    # Generate and print report
    report = analyzer.generate_report(mock_ahead_forks)
    print(report)
    
    print("\n✅ Test completed successfully!")
    print("💡 This demonstrates the fork analysis output with mock data.")
    print("💡 To use with real data, set GITHUB_TOKEN environment variable.")
    

if __name__ == "__main__":
    test_with_mock_data()
