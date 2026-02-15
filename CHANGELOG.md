# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.11] - 2026-02-15

### Changed
- Release 0.2.11

## [0.2.0] - 2024-04-16

### Changed
- Modified `cached_agent_run` and `cached_agent_run_sync` to always return full result object instead of just the data field
- Removed `full_result` parameter as it's no longer needed
- Replaced `transcript_history` parameter with `message_history` for better alignment with PydanticAI
- Removed `message_converter` parameter in favor of native message handling
- Updated tests to handle full result objects and new parameter structure
- Improved type hints and stub files for better IDE support

### Added
- Comprehensive migration guide in README.md
- Enhanced documentation for accessing result metadata
- Better error messages for type-related issues

### Removed
- `transcript_history` parameter
- `message_converter` parameter
- `full_result` parameter

## [0.1.0] - 2024-04-02

### Added
- Initial release
- Redis-based caching for LLM responses
- Configurable message format conversion
- Flexible expense tracking
- Rate limit handling with exponential backoff
- Support for multiple LLM providers
- Customizable cost tables for different models

### Changed
- None (initial release)

### Deprecated
- None (initial release)

### Removed
- None (initial release)

### Fixed
- None (initial release)

### Security
- None (initial release) 