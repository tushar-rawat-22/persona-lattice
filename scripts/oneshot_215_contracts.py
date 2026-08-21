from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, got {count}: {old!r}")
    p.write_text(text.replace(old, new, 1))


replace_once(
    "services/api/tests/test_bluesky_public_provider.py",
    '    assert descriptor.supported_identifier_kinds == frozenset({"username"})\n',
    '    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})\n',
)
replace_once(
    "services/api/tests/test_intelligence_source_catalog.py",
    '    assert bluesky.accepts == frozenset({LeadKind.USERNAME})\n',
    '    assert bluesky.accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})\n',
)
replace_once(
    "services/api/tests/test_intelligence_source_catalog_provider_registry.py",
    '    assert descriptor.supported_identifier_kinds == frozenset({"username"})\n',
    '    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})\n',
)
replace_once(
    "services/api/tests/test_intelligence_source_bindings.py",
    '        ["sherlock", "bluesky_public_profile"],\n',
    '        ["sherlock"],\n',
)
path = Path("services/api/tests/test_intelligence_source_bindings.py")
text = path.read_text()
anchor = '''def test_username_only_governed_sources_match_provider_descriptors(name: str) -> None:\n    binding = source_binding_for(name, kind=LeadKind.USERNAME)\n    descriptor = PROVIDER_BY_NAME[name]\n    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER\n    assert binding.provider_name == name\n    assert descriptor.status == ProviderStatus.DEVELOPMENT.value\n    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN\n    assert descriptor.supported_identifier_kinds == frozenset({"username"})\n'''
if anchor not in text:
    raise SystemExit("binding test anchor not found")
addition = anchor + '''\n\ndef test_bluesky_username_and_url_binding_matches_provider_descriptor() -> None:\n    binding = source_binding_for("bluesky_public_profile", kind=LeadKind.URL)\n    descriptor = PROVIDER_BY_NAME["bluesky_public_profile"]\n    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER\n    assert binding.provider_name == "bluesky_public_profile"\n    assert binding.accepts == frozenset({LeadKind.USERNAME, LeadKind.URL})\n    assert descriptor.status == ProviderStatus.DEVELOPMENT.value\n    assert descriptor.contact_risk is ContactRisk.NONE_KNOWN\n    assert descriptor.supported_identifier_kinds == frozenset({"username", "url"})\n'''
path.write_text(text.replace(anchor, addition, 1))
print("contract tests updated")
