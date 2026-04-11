def derive_codegen_consistency_report(bundle: dict) -> dict:
    files = list(bundle.get("files", {}).keys())
    return {
        "generated_file_count": len(files),
        "has_backend": any("apps/api" in f for f in files),
        "has_frontend": any("apps/web" in f for f in files),
        "status": "consistent_enough_for_scaffold" if files else "empty"
    }
