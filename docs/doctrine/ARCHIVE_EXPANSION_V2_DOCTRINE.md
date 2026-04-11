# Archive Expansion V2 Doctrine

Purpose: turn raw uploaded zip archives into a governed quarantine inventory with fingerprints, duplicate detection, family classification, canon-role hints, and repeatable extraction inputs.

Rules:
1. No archive becomes live runtime truth directly.
2. Every archive is copied into quarantine archives before extraction.
3. Every archive gets a manifest.
4. Every archive gets a SHA-256 fingerprint.
5. Duplicate hashes are recorded and treated as one lineage unless proven otherwise.
6. Expansion is quarantine-only.
7. Canon imports happen later through extraction records and merge gates.
