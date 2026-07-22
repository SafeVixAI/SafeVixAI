# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi.testclient import TestClient


def _get_openapi(app):
    """Fetch and unwrap the OpenAPI schema from the response envelope."""
    tc = TestClient(app)
    resp = tc.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.json()
    # ApiResponseMiddleware wraps data in {"data": ..., "error": ..., "success": ...}
    return body.get("data", body)


class TestOpenAPISchema:
    def test_openapi_schema_valid(self, app):
        schema = _get_openapi(app)

        assert "openapi" in schema
        assert isinstance(schema["openapi"], str)
        assert schema["openapi"].startswith("3")

        assert "info" in schema
        assert "title" in schema["info"]
        assert isinstance(schema["info"]["title"], str)
        assert schema["info"]["title"]
        assert "version" in schema["info"]
        assert isinstance(schema["info"]["version"], str)
        assert schema["info"]["version"]

        assert "paths" in schema
        assert isinstance(schema["paths"], dict)
        assert len(schema["paths"]) >= 10

        assert "components" in schema
        assert "schemas" in schema["components"]
        assert isinstance(schema["components"]["schemas"], dict)
        assert len(schema["components"]["schemas"]) >= 5

        methods_seen = set()
        for path, path_item in schema["paths"].items():
            for method in ("get", "post", "put", "patch", "delete"):
                if method in path_item:
                    methods_seen.add(method)
        assert "get" in methods_seen, "No GET method found across all paths"
        assert "post" in methods_seen, "No POST method found across all paths"

    def test_docs_redirects(self, app):
        tc = TestClient(app)
        resp_docs = tc.get("/docs")
        assert resp_docs.status_code == 200
        assert "text/html" in resp_docs.headers.get("content-type", "")

        resp_redoc = tc.get("/redoc")
        assert resp_redoc.status_code == 200
        assert "text/html" in resp_redoc.headers.get("content-type", "")

    def test_all_routes_have_tags(self, app):
        schema = _get_openapi(app)

        for path, path_item in schema["paths"].items():
            for method in ("get", "post", "put", "patch", "delete", "options"):
                operation = path_item.get(method)
                if operation is None:
                    continue
                assert "tags" in operation, (
                    f"{method.upper()} {path} has no tags"
                )
                assert isinstance(operation["tags"], list), (
                    f"{method.upper()} {path} tags must be a list"
                )
                assert len(operation["tags"]) >= 1, (
                    f"{method.upper()} {path} has empty tags list"
                )

    def test_mandatory_routes_exist(self, app):
        schema = _get_openapi(app)
        paths = schema["paths"]

        mandatory = [
            "/api/v1/emergency/nearby",
            "/api/v1/challan/calculate",
            "/api/v1/chat/",
            "/api/v1/auth/login",
            "/health",
        ]
        for route in mandatory:
            assert route in paths, f"Mandatory route {route} not found in OpenAPI schema"

    def test_response_schemas_defined(self, app):
        schema = _get_openapi(app)

        routes_with_response_schema = 0
        for path, path_item in schema["paths"].items():
            for method in ("get", "post", "put", "patch", "delete"):
                operation = path_item.get(method)
                if operation is None:
                    continue
                responses = operation.get("responses", {})
                for status_code, response in responses.items():
                    content = response.get("content")
                    if content is None:
                        continue
                    for media_type, media_type_obj in content.items():
                        media_schema = media_type_obj.get("schema", {})
                        if "$ref" in media_schema:
                            routes_with_response_schema += 1

        assert routes_with_response_schema >= 5, (
            f"Only {routes_with_response_schema} route responses have a $ref schema defined, "
            "expected at least 5"
        )
