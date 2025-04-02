# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Here are the versions that are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an email to [your-email@example.com]. All security vulnerabilities will be promptly addressed.

Please do not disclose security-related issues publicly until a fix has been announced.

## Security Best Practices

When using this library, please follow these security best practices:

1. **Redis Security**
   - Use SSL/TLS for Redis connections when possible
   - Use strong passwords for Redis authentication
   - Restrict Redis access to trusted networks
   - Keep Redis updated to the latest version

2. **API Keys and Credentials**
   - Never commit API keys or credentials to version control
   - Use environment variables for sensitive data
   - Rotate API keys regularly
   - Use the minimum required permissions for API keys

3. **Rate Limiting**
   - Configure appropriate rate limits for your use case
   - Monitor rate limit usage
   - Implement proper error handling for rate limit exceeded cases

4. **Data Security**
   - Be careful with sensitive data in prompts
   - Consider implementing data sanitization
   - Use appropriate TTL values for cached data
   - Monitor cache size and implement cleanup if needed

## Security Updates

We will:
1. Acknowledge receipt of security reports within 48 hours
2. Release a security advisory within 72 hours
3. Release a patch within 7 days
4. Keep the community informed of the progress

## Contact

For security-related issues, please contact:
- Email: talkingtoaj@hotmail.com
- GitHub Issues: [Create a security issue](https://github.com/talkingtoaj/llm-caching/security/advisories) 