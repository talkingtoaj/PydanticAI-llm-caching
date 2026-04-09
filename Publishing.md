Publish to TestPyPI: If the push was to the main branch (and it wasn't a tag push), the publish-to-testpypi job runs after the build. It downloads the built artifacts and publishes them to TestPyPI using trusted publishing via the testpypi environment.

Publish to PyPI: If the push was a tag starting with v, the publish-to-pypi job runs after the build. It downloads the artifacts and publishes them to the official PyPI index using trusted publishing via the pypi environment. This step will require manual approval in GitHub Actions because we configured the pypi environment that way.


To test the PyPI publishing and release creation, you'll need to:
Approve the deployment to the pypi environment in the GitHub Actions run.



## Shipping a new version

- [ ] Bump **`version`** in **`pyproject.toml`** (e.g. `0.4.0`).
- [ ] Commit and push to `main` (or merge a PR that does the bump).
  ```bash
  git commit -am "Bump version to 0.4.0"
  git push
  ```
- [ ] Create and push an annotated tag whose name matches the version with a **`v`** prefix:
  ```bash
  git tag v0.4.0
  git push origin v0.4.0
  ```
  Tag pushes trigger the workflow that builds wheels, publishes to PyPI (after any required approval), and creates the GitHub Release (including Sigstore signatures for the artifacts in CI).

**Manual step in GitHub:** if the **`pypi`** environment is protected, open the Actions run for that tag and **approve** the deployment to PyPI when prompted. You do not sign releases by hand; signing and release creation run in the workflow.
