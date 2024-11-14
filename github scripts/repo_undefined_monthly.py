import requests
import os
import pandas as pd
import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_github_data(url, headers):
    """Reusable function to fetch data from GitHub API."""
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch data: {response.status_code} - {response.text}")
        return None

def fetch_repositories(owner, token):
    """Fetch all repositories for a specified owner, including private and internal ones, filtering out archived ones."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    all_repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{owner}/repos?type=all&per_page=100&page={page}"
        logging.info(f"Fetching page {page} for {owner}")
        
        repos = fetch_github_data(url, headers)
        
        if repos is None:
            logging.error("Error fetching data. Stopping pagination.")
            break
        
        if not repos:
            logging.info("No more repositories found. Ending pagination.")
            break
        
        # Filter out archived repositories and add unarchived repos to the list
        all_repos.extend([repo for repo in repos if not repo.get('archived')])
        logging.info(f"Page {page} fetched with {len(repos)} repositories (unarchived added: {len(all_repos)})")
        page += 1

    logging.info(f"Total unarchived repositories fetched: {len(all_repos)}")
    return all_repos

def fetch_repo_owner_property(owner, repo, token):
    """Fetch the 'RepoOwner' property for the repository and check if it's 'undefined'."""
    url = f"https://api.github.com/repos/{owner}/{repo}/properties/values"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}"
    }
    properties = fetch_github_data(url, headers)
    if properties:
        for prop in properties:
            if prop.get('property_name') == 'RepoOwner' and prop.get('value', '').lower() == 'undefined':
                logging.info(f"'RepoOwner' property for {repo} is set to 'undefined'")
                return True
    return False

def fetch_last_commit(owner, repo, token):
    """Fetch the last commit date for a given repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    commits = fetch_github_data(url, headers)
    if commits:
        date_str = commits[0]['commit']['committer']['date']
        return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').strftime('%d %b %Y')
    return None

def extract_prefix(repo_name):
    """Extract prefix from repository name before the first hyphen, or return empty if no hyphen."""
    return repo_name.split('-')[0] if '-' in repo_name else ''

def create_excel(data):
    """Create an Excel file from the list of repositories, including a 'Prefix' column."""
    df = pd.DataFrame(data, columns=['Repository', 'Prefix', 'Last Commit Date'])
    
    filename = 'ccq-utils/github scripts/output/undefined_repo_owner_latest.xlsx'

    output_dir = os.path.dirname(filename)
    os.makedirs(output_dir, exist_ok=True)
    
    df.to_excel(filename, index=False)
    logging.info(f"Excel file '{filename}' created successfully in 'output' directory.")

def main():
    owner = "spring-media"
    token = os.getenv("GIT_API_KEY")

    if not token:
        logging.critical("GIT_API_KEY is not set. Please check your environment variables.")
        return

    repositories = fetch_repositories(owner, token)
    undefined_owners = []

    for repo in repositories:
        if fetch_repo_owner_property(owner, repo['name'], token):
            last_commit_date = fetch_last_commit(owner, repo['name'], token)
            undefined_owners.append({
                'Repository': repo['name'],
                'Prefix': extract_prefix(repo['name']),
                'Last Commit Date': last_commit_date
            })

    if undefined_owners:
        create_excel(undefined_owners)
    else:
        logging.info("No repositories with 'RepoOwner' set to 'undefined' were found.")

if __name__ == "__main__":
    main()
