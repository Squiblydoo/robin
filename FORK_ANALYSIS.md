# Fork Analysis Feature

This feature allows you to analyze GitHub repository forks to identify those that are substantially ahead of the parent repository.

## Overview

The fork analysis feature:
- Fetches all forks of a specified repository
- Compares each fork with the parent repository
- Identifies forks with commits ahead of the parent
- Generates a detailed report sorted by commits ahead

## Usage

### Command Line Interface (CLI)

```bash
python main.py analyze-forks --owner <OWNER> --repo <REPO> [OPTIONS]
```

#### Required Arguments:
- `--owner, -o`: Repository owner (username or organization)
- `--repo, -r`: Repository name

#### Optional Arguments:
- `--min-commits, -c`: Minimum commits ahead to report (default: 1)
- `--output, -f`: Filename to save the report

#### Examples:

```bash
# Analyze robin repository
python main.py analyze-forks --owner apurvsinghgautam --repo robin

# Analyze with minimum 10 commits ahead
python main.py analyze-forks -o torproject -r tor -c 10

# Save report to file
python main.py analyze-forks -o apurvsinghgautam -r robin -f report.txt
```

### Web UI

1. Start the Streamlit UI:
   ```bash
   python main.py ui
   ```

2. Navigate to the "Fork Analysis" tab

3. Enter the repository owner and name

4. Adjust the "Minimum Commits Ahead" slider if needed

5. Click "Analyze Forks"

6. View the results and download the report if desired

## Authentication

For better API rate limits, set a GitHub personal access token:

1. Create a token at https://github.com/settings/tokens
   - Select "Generate new token (classic)"
   - Give it a name like "Robin Fork Analysis"
   - No special scopes are needed for public repositories
   - For private repositories, select the `repo` scope

2. Set the environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

3. Run the analysis as usual

Without authentication, you may hit rate limits (60 requests/hour). With authentication, the limit increases to 5,000 requests/hour.

## Output Format

The report includes:
- Repository name and analysis timestamp
- Number of forks ahead
- For each fork:
  - Owner and repository name
  - URL
  - Star count
  - Commits ahead and behind
  - Last update date
  - Description (if available)

## Example Output

```
======================================================================
Fork Analysis Report for apurvsinghgautam/robin
Generated: 2026-02-03 13:38:40
======================================================================

Found 2 fork(s) ahead of the parent repository:

1. tekcin/robin_scrapper
   URL: https://github.com/tekcin/robin_scrapper
   ⭐ Stars: 32
   📊 Commits ahead: 15
   📊 Commits behind: 2
   📅 Last updated: 2026-01-20T14:59:00Z
   📝 Description: Enhanced scrapper with additional features

2. Xer0bit/Dark-Web-OSINT-Tool
   URL: https://github.com/Xer0bit/Dark-Web-OSINT-Tool
   ⭐ Stars: 4
   📊 Commits ahead: 8
   📊 Commits behind: 5
   📅 Last updated: 2025-12-24T09:13:00Z
   📝 Description: Dark Web OSINT with extra search engines

======================================================================
💡 Consider reviewing these forks for potential improvements
   or features that could be merged back to the parent repository.
======================================================================
```

## Use Cases

1. **Project Maintenance**: Discover active forks with improvements
2. **Feature Discovery**: Find innovative features in community forks
3. **Collaboration**: Identify potential contributors
4. **Code Review**: Evaluate changes made by the community
5. **Merge Opportunities**: Find features to merge back into parent

## Limitations

- Requires internet connection
- Subject to GitHub API rate limits
- Private repositories require authentication
- Large repositories with many forks may take time to analyze
