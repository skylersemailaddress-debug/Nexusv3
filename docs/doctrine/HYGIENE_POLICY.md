# Hygiene Policy

Forbidden in canonical source:
- checked-in virtual environments
- checked-in node_modules
- committed secrets
- hardcoded auth tokens
- duplicate dist trees outside assembly/dist
- alternate state backends in live runtime path
- archive snapshots mixed into source

If uncertain, quarantine first.
