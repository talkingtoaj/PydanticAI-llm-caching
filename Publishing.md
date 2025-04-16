Publish to TestPyPI: If the push was to the main branch (and it wasn't a tag push), the publish-to-testpypi job runs after the build. It downloads the built artifacts and publishes them to TestPyPI using trusted publishing via the testpypi environment.

Publish to PyPI: If the push was a tag starting with v, the publish-to-pypi job runs after the build. It downloads the artifacts and publishes them to the official PyPI index using trusted publishing via the pypi environment. This step will require manual approval in GitHub Actions because we configured the pypi environment that way.


To test the PyPI publishing and release creation, you'll need to:
Approve the deployment to the pypi environment in the GitHub Actions run.




To push a new:
- [ ] Update the version in pyproject.toml (e.g., to 0.1.1 or 1.0.0).
- [ ] Update the __version__ in __init__.py
- [ ] Commit the change.
`git commit -m "Bump version to 0.1.1"`
`git push main`

- [ ] Create a git tag matching the version (e.g., git tag v0.1.1).
`git tag v0.1.1`
`git push origin v0.1.1`

- [ ] Push the tag to GitHub (git push origin v0.1.1).
- [ ] Sign the release on GitHub actions
