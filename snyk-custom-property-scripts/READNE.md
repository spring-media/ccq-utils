# Snyk Custom Property Scripts

This folder contains scripts to manage custom properties and automate the integration of GitHub repositories into Snyk. These scripts ensure proper ownership setup and visibility for Snyk vulnerability scans.

## Overview of Files

<details>
  <summary>1. create_custom_property.py</summary>

  **Purpose**: Automates the setting of custom properties (such as `RepoOwner`) on specified repositories within GitHub, maintaining clear ownership assignments.

  **Functionality**:
  - **Update Custom Properties**: Uses PATCH requests to update or set properties for each specified repository in GitHub.

  **Environment Variables**:
  - `GITHUB_TOKEN`: The GitHub API token for authentication.

  **Usage**:
  1. Define the list of repositories to update in the `repositories` list.
  2. Specify the desired property in the `properties` dictionary.

</details>

<details>
  <summary>2. org_mapping.json</summary>

  **Purpose**: Maps each team name (e.g., "CCQ Team", "E-Team") to its Snyk organization ID and integration ID, enabling automated imports of GitHub repositories into Snyk based on team ownership.

  **Structure**:
  - **`org_id`**: The Snyk organization ID.
  - **`integration_id`**: The Snyk integration ID for GitHub repositories.

  **Usage**: Used as a reference in `snyk-import.py` to map repositories to their respective Snyk organizations.

</details>

<details>
  <summary>3. snyk-import.py</summary>

  **Purpose**: Automates the import of GitHub repositories to Snyk, based on the `RepoOwner` custom property. Repositories with `RepoOwner` set to “undefined” are skipped to prevent duplicate or erroneous imports.

  **Functionality**:
  - **Fetch Repositories**: Retrieves all unarchived repositories within the specified GitHub organization.
  - **Check RepoOwner Property**: Validates the `RepoOwner` property on each repository and checks for matching Snyk organizations in `org_mapping.json`.
  - **Import to Snyk**: Initiates Snyk imports for each repository not already present in Snyk.

  **Environment Variables**:
  - `GIT_API_KEY`: The GitHub API token for authentication.
  - `SNYK_API_KEY`: The Snyk API token for repository imports.

### Snyk Import Workflow (snyk-import.yaml)

  **Schedule**: Runs daily at 11 AM UTC and can be manually triggered as needed.

  **Environment**:
  - Uses GitHub Secrets (`GIT_API_KEY` and `SNYK_API_KEY`) for secure access to GitHub and Snyk APIs.

</details>
