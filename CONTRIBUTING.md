# Contributing to LLM Caching

Thank you for your interest in contributing to LLM Caching! This document provides guidelines and steps for contributing.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/talkingtoaj/llm-caching.git
   cd llm-caching
   ```

2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Install pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

2. Make your changes, following the coding style:
   - Use type hints
   - Add docstrings for public functions and classes
   - Follow PEP 8 guidelines
   - Run `poetry run black .` to format code
   - Run `poetry run ruff .` to check for issues

3. Add tests for your changes:
   - Add tests in the `tests/` directory
   - Run tests with `poetry run pytest`
   - Ensure test coverage is maintained

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request:
   - Go to the GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template
   - Submit the PR

## Code Style

- We use Black for code formatting
- We use Ruff for linting
- We use MyPy for type checking
- All public functions and classes must have docstrings
- Follow PEP 8 guidelines

## Testing

- Write tests for all new features
- Ensure tests pass locally before submitting PR
- Maintain or improve test coverage
- Include integration tests for complex features

## Documentation

- Update README.md if needed
- Add docstrings to all public functions and classes
- Update CHANGELOG.md with your changes
- Add comments for complex logic

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. The CI/CD pipeline will automatically publish to PyPI

## Questions?

If you have any questions, feel free to:
- Open an issue
- Join our discussions
- Contact the maintainers

Thank you for contributing! 