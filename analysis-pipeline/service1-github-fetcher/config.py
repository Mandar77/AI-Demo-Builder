"""
Configuration file for Service 1: GitHub Fetcher
Contains environment variables and default settings
"""

import os

# GitHub API configuration
GITHUB_API = os.environ.get('GITHUB_API', 'https://api.github.com')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Request timeout in seconds
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', '30'))

# Enable/disable README fetching (useful for testing)
FETCH_README = os.environ.get('FETCH_README', 'true').lower() == 'true'

