import json
from api import app
from fastapi.openapi.utils import get_openapi

def export_openapi():
    # Ensure the app generates the schema
    # We call get_openapi to handle any dynamic generation (like descriptions)
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("OpenAPI specification exported to openapi.json")

if __name__ == "__main__":
    export_openapi()
