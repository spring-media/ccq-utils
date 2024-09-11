import requests
import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

github_api_key = os.getenv("GIT_API_KEY")
snyk_api_key = os.getenv("SNYK_API_KEY")

# Set headers
github_headers = {'Authorization': f'token {github_api_key}'}
snyk_headers = {'Authorization': f'token {snyk_api_key}', 'Content-Type': 'application/json'}

# Snyk Org Mapping
def load_org_mapping():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'org_mapping.json')
    
    with open(file_path) as file:
        return json.load(file)

org_mapping = load_org_mapping()

def fetch_all_snyk_targets(org_id, headers):
    all_targets = []
    targets_url = f"https://api.snyk.io/rest/orgs/{org_id}/targets"
    params = {'version': '2024-05-08', 'limit': 100, 'created_gte': '2022-01-01T16:00:00Z'}
    while targets_url:
        response = requests.get(targets_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_targets.extend(data.get('data', []))
            targets_url = data.get('links', {}).get('next')
        else:
            logging.error(f"Failed to retrieve targets: {response.status_code} - {response.text}")
            break
        params = None
    return all_targets

def fetch_all_repositories(org, headers):
    repositories = []
    page = 1
    while True:
        repo_url = f"https://api.github.com/orgs/{org}/repos?type=all&per_page=100&page={page}"
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            # Filter out archived repositories
            active_repos = [repo for repo in data if not repo['archived']]
            repositories.extend(active_repos)
            page += 1
        else:
            logging.error(f"Failed to retrieve repositories: {response.status_code} - {response.text}")
            break
    return repositories


def check_and_import_repository(repo_name, repo_owner, owner):
    if repo_owner in org_mapping:
        org_details = org_mapping[repo_owner]
        org_id, integration_id = org_details['org_id'], org_details['integration_id']
        all_targets = fetch_all_snyk_targets(org_id, snyk_headers)
        project_exists = any(target['attributes']['display_name'] == f"{owner}/{repo_name}" for target in all_targets)
        if project_exists:
            logging.info(f"The repository {repo_name} is already integrated into Snyk under {repo_owner}.")
        else:
            import_url = f'https://snyk.io/api/v1/org/{org_id}/integrations/{integration_id}/import'
            data = json.dumps({"target": {"owner": owner, "name": repo_name, "branch": "master"}})
            import_response = requests.post(import_url, headers=snyk_headers, data=data)
            if import_response.status_code == 201:
                logging.info(f"Import of {repo_name} initiated successfully.")
            else:
                logging.error(f"Failed to import {repo_name}: {import_response.status_code} - {import_response.text}")
    else:
        logging.error(f"No Snyk organization mapped for RepoOwner: {repo_owner}")

def fetch_repo_owner_property(owner, repo, headers):
    url = f"https://api.github.com/repos/{owner}/{repo}/properties/values"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        properties = response.json()
        for property in properties:
            if property['property_name'] == 'RepoOwner':
                repo_owner_value = property['value']
                if repo_owner_value.lower() == 'undefined':
                    logging.info(f"'RepoOwner' property for {repo} is set to 'undefined'")
                    return None
                return repo_owner_value
        logging.info(f"'RepoOwner' property not found for {repo}")
    else:
        logging.error(f"Failed to fetch properties from GitHub: {response.status_code} - {response.text}")
    return None

def main():
    owner = 'spring-media'
    repositories = fetch_all_repositories(owner, github_headers)
    for repo in repositories:
        repo_name = repo['name']
        repo_owner = fetch_repo_owner_property(owner, repo_name, github_headers)
        if repo_owner and repo_owner != 'undefined':
            check_and_import_repository(repo_name, repo_owner, owner)
        else:
            logging.info(f"No 'RepoOwner' property found or set to 'undefined' for {repo_name}")

if __name__ == "__main__":
    main()
