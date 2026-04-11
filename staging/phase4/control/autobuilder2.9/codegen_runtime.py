def generate_backend_files(app_family: str) -> dict:
    files = {
        "apps/api/generated/routes.py": f"# generated backend routes for {app_family}\n",
        "apps/api/generated/services.py": f"# generated backend services for {app_family}\n",
        "apps/api/generated/models.py": f"# generated backend models for {app_family}\n"
    }
    return {"files": files, "status": "generated"}

def generate_frontend_files(app_family: str) -> dict:
    files = {
        "apps/web/generated/pages.tsx": f"export default function Page() {{ return <main>{app_family} generated UI</main>; }}\n",
        "apps/web/generated/components.tsx": f"export const GeneratedComponent = () => <div>{app_family} component</div>;\n"
    }
    return {"files": files, "status": "generated"}

def merge_codegen_outputs(*bundles: dict) -> dict:
    merged = {}
    for bundle in bundles:
        for path, content in bundle.get("files", {}).items():
            merged[path] = content
    return {"files": merged, "status": "merged"}
