# Github Scripts
Here you will find a collection of used GitHub scripts.

<details>
  <summary>Monthly Undefined Repo Owner Report</summary>

Automates identification of repositories missing the `repoOwner` property, preventing Snyk scans for vulnerabilities. The script generates a monthly Excel report listing affected repositories, including last commit dates.

### Script Overview

1. **Fetch Repositories**: Retrieves all unarchived repositories in the organization.
2. **Check `repoOwner`**: Identifies repositories with `repoOwner` set to `'undefined'`.
3. **Fetch Last Commit**: Gets the last commit date for each affected repository.
4. **Generate Report**: Creates an Excel file (`undefined_repo_owner_<date>.xlsx`) with repository names, prefixes, and commit dates.

### Todo
- Automatically send out emails to CCQ with the Excel file

</details>
