import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def update_custom_properties(owner, repo, token, properties):
    url = f"https://api.github.com/repos/{owner}/{repo}/properties/values"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    payload = {"properties": properties}

    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 204:
        print(f"Properties updated successfully for {repo}.")
    elif response.status_code == 200:
        print(f"Properties updated successfully, received data for {repo}: {response.text}")
    else:
        print(f"Failed to update properties for {repo}: {response.status_code} - {response.text}")
        print("Response headers:", response.headers)
        print("Response body:", response.json())

if __name__ == "__main__":
    owner = "spring-media"
    token = os.getenv("GITHUB_TOKEN")

    repositories = [
        #Your repositories
    ]

    properties = [{"property_name": "RepoOwner", "value": " "}] #Your team's name

    for repo in repositories:
        update_custom_properties(owner, repo, token, properties)
