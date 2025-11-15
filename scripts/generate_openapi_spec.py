#!/usr/bin/env python3
"""Generate OpenAPI specification files (JSON and YAML)."""
import json
import sys
from pathlib import Path

# Add parent directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


def generate_openapi_spec():
    """Generate OpenAPI specification in JSON and YAML formats."""
    # Get OpenAPI schema
    openapi_schema = app.openapi()
    
    # Create docs directory if it doesn't exist
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Write JSON file
    json_path = docs_dir / "openapi.json"
    with open(json_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✓ Generated OpenAPI JSON: {json_path}")
    
    # Write YAML file
    try:
        import yaml
        yaml_path = docs_dir / "openapi.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Generated OpenAPI YAML: {yaml_path}")
    except ImportError:
        print("⚠ PyYAML not installed, skipping YAML generation")
        print("  Install with: pip install pyyaml")
    
    print(f"\n✓ OpenAPI specification generated successfully!")
    print(f"\nView documentation at:")
    print(f"  - Swagger UI: http://localhost:8000/docs")
    print(f"  - ReDoc: http://localhost:8000/redoc")
    print(f"  - OpenAPI JSON: http://localhost:8000/openapi.json")


if __name__ == "__main__":
    generate_openapi_spec()
