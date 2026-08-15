# Security policy

PersonaLattice handles identifiers that can become sensitive when combined.
The default engineering rule is simple: **collect less, retain less, expose less**.

## Report a security issue

Do not open a public issue containing API keys, phone numbers, email addresses,
private investigation data, credentials, or reproducible personal-data leaks.

For now, report security issues privately to the repository owner through
GitHub's private contact channels.

## Repository rules

- Never commit API keys or raw investigation exports.
- Never put real case data in fixtures.
- Keep raw provider responses outside Git.
- Redact identifiers in screenshots, logs, issues, and pull requests.
- AI-generated claims must link back to evidence; the model is not a source.
- New data sources need a source-policy review before integration.
