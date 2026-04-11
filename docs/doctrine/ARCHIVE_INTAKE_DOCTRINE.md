# Archive Intake Doctrine

This command scans the Downloads folder for known archive names, extracts matches into Quarantine, and registers the extracted folders as governed sources.

## Rules
- archives are extracted into Quarantine only
- extracted folders, not zip files, are registered as sources
- registration is idempotent by source name
- missing archives are skipped, not treated as failure
- all later intake runs must still pass ship validation
