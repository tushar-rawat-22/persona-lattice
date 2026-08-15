# Source policy

PersonaLattice is meant to assemble explainable identity intelligence, not to
become a data-hoarding scraper.

A source can enter the product only after four questions are answered:

1. **Is the use lawful and permitted by the source's terms?**
2. **Is the license compatible with how we ship the product?**
3. **Does using it contact, notify, authenticate as, or otherwise interact with the subject?**
4. **Can we explain the reliability and limitations of the returned data?**

## Source classes

### Public-source
Public webpages, public profiles, public documents, public repositories and
publicly accessible official registries.

### Consented enrichment
Information queried because the subject explicitly agreed to the check or
submitted the identifier themselves.

### Restricted / disabled
Account-recovery enumeration, OTP flows, private-account access, credential
testing, leaked credential dumps, hidden KYC records, precise live location,
or anything that depends on bypassing access controls.

## Contact-risk labels

Every provider adapter must declare one of:

- `none_known`
- `possible`
- `likely`
- `direct_contact`

Silent/public research mode may only use `none_known` sources.

## Evidence rule

A provider result is an observation, not a fact about a person. PersonaLattice
promotes observations into claims only when the evidence model can explain why.
