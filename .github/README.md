# GitHub Actions CI/CD

This directory contains GitHub Actions workflows for continuous integration and deployment of the MCP ModelService SDK.

## Workflow: Python Package CI/CD

The `python-package.yml` workflow automates the following tasks:

1. **Testing**: Runs on all pushes to the main branch and pull requests
   - Runs linting with Ruff
   - Runs type checking with mypy
   - Runs unit tests with Python's unittest

2. **Building and Publishing**: Only runs when a tag starting with 'v' is pushed
   - Builds the Python package
   - Publishes the package to PyPI

## Usage

### For Testing Only

The testing part of the workflow runs automatically on:
- All pushes to the main branch
- All pull requests to the main branch
- Manual trigger via GitHub Actions UI

### For Releasing a New Version

To release a new version and publish to PyPI:

1. Update the version in `pyproject.toml`
2. Commit the change: `git commit -am "Bump version to X.Y.Z"`
3. Tag the commit: `git tag vX.Y.Z`
4. Push the changes and tags: `git push && git push --tags`

The workflow will automatically build and publish the package to PyPI when it detects the new tag.

### Manual Workflow Triggering

You can also manually trigger the workflow from the GitHub Actions UI:

1. Go to the "Actions" tab in your GitHub repository
2. Select the "Python Package CI/CD" workflow
3. Click "Run workflow"
4. If you want to publish to PyPI, check the "Publish to PyPI after tests" checkbox
5. Click "Run workflow"

## Required Secrets

For the publish step to work, you need to configure a PyPI API token:

1. Generate a PyPI API token at https://pypi.org/manage/account/token/
2. Add the token as a repository secret named `PYPI_API_TOKEN` in your GitHub repository
   (Go to Settings > Secrets and variables > Actions > New repository secret)

## Manual Workflow Dispatch

The workflow does not currently support manual dispatch. If needed, this can be added by modifying
the workflow file to include the `workflow_dispatch` event trigger. 