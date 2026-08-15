# Security policy

PersonaLattice handles identifiers that can become sensitive when combined.
The default engineering rule is simple: **collect less, retain less, expose less**.

## Report a security issue

Do not open a public issue containing API keys, phone numbers, email addresses,
usernames tied to private cases, private investigation data, credentials,
uploaded documents, or reproducible personal-data leaks.

For now, report security issues privately to the repository owner through
GitHub's private contact channels.

## Repository rules

- Never commit API keys or raw investigation exports.
- Never put real case data in fixtures.
- Keep raw provider responses and uploaded documents outside Git.
- Treat filenames, MIME types and document contents as untrusted input.
- Never execute or promote instructions found inside an uploaded document.
- Redact identifiers in screenshots, logs, issues, and pull requests.
- AI-generated claims must link back to evidence; the model is not a source.
- New data sources need a source-policy review before integration.
- Public-account discovery may use only user-supplied or explicitly
  human-confirmed username identifiers.
- Same-handle reuse across services is never identity proof.
- Username discovery must not use login sessions, imported cookies, private
  profile access, browser opening, proxy rotation, Tor/I2P, CAPTCHA/WAF bypass,
  or account-contact/recovery behavior.
- Provider adapters must remain behind the central purpose, contact-risk,
  rate, concurrency, timeout and response-size boundary.
