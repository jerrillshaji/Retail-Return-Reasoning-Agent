"""Prints every endpoint of the API and what each one expects.
Run from the project root:   python -m scripts.show_routes
Nothing is changed; it only reads the API description."""

from app.main import app

spec = app.openapi()
schemas = spec.get("components", {}).get("schemas", {})

print("=== ENDPOINTS ===")
for path, methods in spec["paths"].items():
    for method, info in methods.items():
        body = info.get("requestBody", {}).get("content", {})
        kinds = []
        for content_type, detail in body.items():
            ref = detail.get("schema", {}).get("$ref", "").split("/")[-1]
            kinds.append(f"{content_type} -> {ref or 'inline'}")
        params = [f"{p['name']} ({p['in']})" for p in info.get("parameters", [])]
        secured = "needs login" if info.get("security") else "open"
        print(f"{method.upper():<7}{path}")
        print(f"        {secured}; body: {kinds or 'none'}; params: {params or 'none'}")

print("\n=== BODY / RESPONSE FIELDS ===")
for name, schema in schemas.items():
    if name in ("HTTPValidationError", "ValidationError"):
        continue
    required = set(schema.get("required", []))
    fields = [f + ("*" if f in required else "") for f in schema.get("properties", {})]
    print(f"{name}: {', '.join(fields)}")
print("\n(* = required)")
