import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
github_api_key = os.getenv("GIT_API_KEY")
snyk_api_key = os.getenv("SNYK_API_KEY")

github_headers = {'Authorization': f'token {github_api_key}'}
snyk_headers = {'Authorization': f'token {snyk_api_key}', 'Content-Type': 'application/json'}

GITHUB_ORG_NAME = "spring-media"

def load_org_mapping():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'org_mapping.json')
    
    with open(file_path) as file:
        return json.load(file)
org_mapping = load_org_mapping()

# fetch all Snyk targets for org
def fetch_all_snyk_targets(org_id, headers):
    all_targets = []
    base_url = "https://api.snyk.io"
    targets_url = f"{base_url}/rest/orgs/{org_id}/targets"
    params = {'version': '2024-05-08', 'limit': 100, 'exclude_empty': 'false'}

    print(f"Fetching all targets in org '{org_id}'...")
    while targets_url:
        response = requests.get(targets_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_targets.extend(data.get('data', []))

            next_url = data.get('links', {}).get('next')
            if next_url:
                # normalize next URL
                if not next_url.startswith('http'):
                    next_url = base_url + next_url
                targets_url = next_url
                print(f"Retrieved {len(data.get('data', []))} targets. Continuing to next page...")
            else:
                targets_url = None
        else:
            print(f"Failed to retrieve targets: {response.status_code} - {response.text}")
            break

        params = None

    print(f"Total targets fetched for org '{org_id}': {len(all_targets)}")
    return all_targets

# batch-check archived status of repo
def batch_check_archived_repos(repo_list, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}

    queries = []
    for i, repo in enumerate(repo_list):
        owner, name = repo.split('/')
        queries.append(f"""
            repo{i}: repository(owner: "{owner}", name: "{name}") {{
                nameWithOwner
                isArchived
            }}
        """)
    query = f"query {{ {' '.join(queries)} }}"

    print(f"Executing batch query for {len(repo_list)} repositories...")
    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code == 200:
        data = response.json()
        result = {}
        for key, value in data.get("data", {}).items():
            if value:
                result[value["nameWithOwner"]] = value["isArchived"]
        return result
    else:
        print(f"GraphQL query failed: {response.status_code} - {response.text}")
        return {}

# remove a target from Snyk
def remove_from_snyk(org_id, target_id):
    delete_url = f"https://api.snyk.io/rest/orgs/{org_id}/targets/{target_id}?version=2024-05-08"

    print(f"Attempting to remove target ID '{target_id}' from org '{org_id}'...")
    response = requests.delete(delete_url, headers=snyk_headers)

    if response.status_code == 204:
        print(f"Successfully removed target with ID '{target_id}' from Snyk organization '{org_id}'.")
    elif response.status_code == 404:
        print(f"Failed: Target '{target_id}' not found.\n")
    else:
        print(f"Failed: Could not remove target '{target_id}' - {response.status_code}: {response.text}\n")

def main():
    selected_orgs = org_mapping.items()
    archived_count = 0
    removed_count = 0

    for org_name, org_details in selected_orgs:
        org_id = org_details["org_id"]
        print(f"\nProcessing organization: {org_name} (Org ID: {org_id})")

        # fetch all targets from Snyk for org & collect repo names to batch-check
        all_targets = fetch_all_snyk_targets(org_id, snyk_headers)
        repo_list = []
        repo_to_target_id = {}

        for target in all_targets:
            display_name = target['attributes'].get('display_name')
            target_id = target.get('id')

            if not display_name or not target_id:
                print(f"Missing data for target: display_name='{display_name}', target_id='{target_id}'")
                continue

            split_display_name = display_name.split('/')
            if len(split_display_name) != 2:
                print(f"Unexpected display name format: {display_name}")
                continue

            owner, repo_name = split_display_name
            full_repo_name = f"{owner}/{repo_name}"
            repo_list.append(full_repo_name)
            repo_to_target_id[full_repo_name] = target_id

        # batch-check archive status
        archived_statuses = batch_check_archived_repos(repo_list, github_api_key)

        for repo_name, is_archived in archived_statuses.items():
            if is_archived:
                archived_count += 1
                print(f"Confirmed archived: {repo_name}. Proceeding with removal.")
                target_id = repo_to_target_id[repo_name]
                remove_from_snyk(org_id, target_id)
                removed_count += 1

    print(f"\nSummary:")
    print(f"Total archived repositories found: {archived_count}")
    print(f"Total removals performed: {removed_count}")

if __name__ == "__main__":
    main()
