import main


def test_fix_binary_schema():
    schema = {
        "a": {"type": "string", "contentMediaType": "application/octet-stream"},
        "b": [{"items": {"contentMediaType": "application/octet-stream"}}],
        "c": {"contentMediaType": "text/plain"},
    }
    main._fix_binary_schema(schema)
    assert schema["a"] == {"type": "string", "format": "binary"}
    assert schema["b"][0]["items"] == {"format": "binary"}
    assert schema["c"] == {"contentMediaType": "text/plain"}


def test_openapi_has_all_routers():
    main.app.openapi_schema = None
    schema = main.app.openapi()
    paths = set(schema["paths"])
    for prefix in ("files", "llms", "projects", "students", "users", "healths"):
        assert any(p.startswith(f"/api/v1/{prefix}") for p in paths), prefix
    assert "contentMediaType" not in str(schema)
    assert main.app.openapi() is schema
