"""HTTP contract tests for lab 02, tasks 1–8."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app import storage
from app.main import app

BASE = "/api/v1"
UNKNOWN_ID = "00000000-0000-4000-8000-000000000099"


@pytest.fixture
def client():
    storage.categories.clear()
    storage.products.clear()
    storage.reviews.clear()
    with TestClient(app) as test_client:
        yield test_client
    storage.categories.clear()
    storage.products.clear()
    storage.reviews.clear()


def create(client, resource, payload):
    response = client.post(f"{BASE}/{resource}", json=payload)
    assert response.status_code == 201, response.text
    record = response.json()
    assert str(UUID(record["id"])) == record["id"]
    assert response.headers["Location"].endswith(f"{BASE}/{resource}/{record['id']}")
    return record


def assert_error(response, status):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "details"}
    assert isinstance(error["code"], str) and error["code"]
    assert isinstance(error["message"], str) and error["message"]
    assert isinstance(error["details"], list)
    assert all(set(detail) == {"field", "rule", "message"} for detail in error["details"])
    assert "Traceback" not in response.text
    assert "app/main.py" not in response.text
    return error


@pytest.fixture
def records(client):
    category = create(client, "categories", {"name": "Books", "description": "Paper books"})
    product = create(
        client,
        "products",
        {
            "category_id": category["id"],
            "name": "Novel",
            "price": 100,
            "discount_price": 80,
            "stock": 3,
            "condition": "used",
        },
    )
    review = create(
        client, "reviews", {"product_id": product["id"], "rating": 4, "text": "Good book"}
    )
    return {"categories": category, "products": product, "reviews": review}


@pytest.fixture
def payloads(records):
    return {
        "categories": {"name": "Books"},
        "products": {
            "category_id": records["categories"]["id"],
            "name": "Novel",
            "price": 100,
            "stock": 3,
        },
        "reviews": {"product_id": records["products"]["id"], "rating": 4},
    }


@pytest.mark.parametrize(
    "resource,initial,changes,expected,identity",
    [
        (
            "categories",
            {"name": "  Books  ", "description": "Old"},
            {"name": "Updated"},
            {"name": "Updated", "description": None},
            ("id",),
        ),
        (
            "products",
            {"name": "  Novel  ", "discount_price": 80, "condition": "used"},
            {"name": "Updated", "price": 50, "stock": 0},
            {
                "name": "Updated",
                "price": 50,
                "stock": 0,
                "discount_price": None,
                "condition": "new",
            },
            ("id", "seller_id"),
        ),
        ("reviews", {"text": "Old"}, {"rating": 5}, {"rating": 5, "text": None}, ("id", "user_id")),
    ],
)
def test_crud_and_put_resets_defaults_preserving_identity(
    client, payloads, resource, initial, changes, expected, identity
):
    record = create(client, resource, {**payloads[resource], **initial})
    path = f"{BASE}/{resource}/{record['id']}"
    assert all(str(UUID(record[field])) == record[field] for field in identity)
    assert record.get("name", "") == record.get("name", "").strip()
    assert client.get(path).status_code == 200
    assert client.get(path).json() == record
    listing = client.get(f"{BASE}/{resource}")
    assert listing.status_code == 200 and record in listing.json()

    replaced = client.put(path, json={**payloads[resource], **changes})

    assert replaced.status_code == 200
    assert replaced.json() == {**record, **expected}
    assert client.get(path).json() == replaced.json()
    deleted = client.delete(path)
    assert deleted.status_code == 204 and deleted.content == b""
    assert record not in client.get(f"{BASE}/{resource}").json()
    assert_error(client.get(path), 404)


@pytest.mark.parametrize(
    "resource,changes",
    [
        ("categories", {"name": ""}),
        ("categories", {"name": "   "}),
        ("categories", {"name": "x" * 81}),
        ("categories", {"description": "x" * 501}),
        ("products", {"name": "   "}),
        ("products", {"name": "x" * 101}),
        ("products", {"category_id": "not-a-uuid"}),
        ("products", {"price": 0}),
        ("products", {"price": -1}),
        ("products", {"price": "NaN"}),
        ("products", {"price": "Infinity"}),
        ("products", {"discount_price": -1}),
        ("products", {"discount_price": 101}),
        ("products", {"stock": -1}),
        ("products", {"condition": "broken"}),
        ("reviews", {"product_id": "not-a-uuid"}),
        ("reviews", {"rating": 0}),
        ("reviews", {"rating": 6}),
        ("reviews", {"text": "x" * 1001}),
    ],
)
def test_create_rejects_invalid_fields(client, payloads, resource, changes):
    payload = {**payloads[resource], **changes}

    response = client.post(f"{BASE}/{resource}", json=payload)

    error = assert_error(response, 422)
    assert error["details"]
    assert all(
        detail["field"] and detail["rule"] and detail["message"] for detail in error["details"]
    )


INPUT_OPERATIONS = [
    ("POST", "categories", ""),
    ("PUT", "categories", "/{id}"),
    ("PATCH", "categories", "/{id}"),
    ("POST", "products", ""),
    ("PUT", "products", "/{id}"),
    ("POST", "reviews", ""),
    ("PUT", "reviews", "/{id}"),
    ("PATCH", "reviews", "/{id}"),
]


@pytest.mark.parametrize("method,resource,suffix", INPUT_OPERATIONS)
def test_all_input_schemas_forbid_extra_fields(client, records, payloads, method, resource, suffix):
    path = f"{BASE}/{resource}" + suffix.format(id=records[resource]["id"])
    payload = {**payloads[resource], "unexpected": "value"}

    response = client.request(method, path, json=payload)

    error = assert_error(response, 422)
    assert any(detail["field"].endswith("unexpected") for detail in error["details"])


@pytest.mark.parametrize("method,suffix", [("POST", ""), ("PUT", "/{id}")])
@pytest.mark.parametrize(
    "resource,field",
    [
        ("categories", "id"),
        ("products", "id"),
        ("products", "seller_id"),
        ("reviews", "id"),
        ("reviews", "user_id"),
    ],
)
def test_mass_assignment_is_rejected(client, records, payloads, method, suffix, resource, field):
    path = f"{BASE}/{resource}" + suffix.format(id=records[resource]["id"])
    payload = {**payloads[resource], field: UNKNOWN_ID}

    response = client.request(method, path, json=payload)

    error = assert_error(response, 422)
    assert any(detail["field"].endswith(field) for detail in error["details"])
    assert client.get(f"{BASE}/{resource}/{records[resource]['id']}").json() == records[resource]


@pytest.mark.parametrize("resource", ["categories", "products", "reviews"])
def test_put_requires_full_payload(client, records, resource):
    path = f"{BASE}/{resource}/{records[resource]['id']}"

    response = client.put(path, json={})

    assert assert_error(response, 422)["details"]
    assert client.get(path).json() == records[resource]


@pytest.mark.parametrize(
    "method,resource",
    [
        ("GET", "categories"),
        ("PUT", "categories"),
        ("PATCH", "categories"),
        ("DELETE", "categories"),
        ("GET", "products"),
        ("PUT", "products"),
        ("DELETE", "products"),
        ("GET", "reviews"),
        ("PUT", "reviews"),
        ("PATCH", "reviews"),
        ("DELETE", "reviews"),
    ],
)
def test_unknown_resource_returns_404(client, payloads, method, resource):
    response = client.request(method, f"{BASE}/{resource}/{UNKNOWN_ID}", json=payloads[resource])

    assert_error(response, 404)


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
@pytest.mark.parametrize("resource", ["categories", "products", "reviews"])
def test_malformed_path_uuid_returns_422(client, payloads, method, resource):
    response = client.request(method, f"{BASE}/{resource}/not-a-uuid", json=payloads[resource])

    error = assert_error(response, 422)
    assert any(detail["field"].startswith("path.") for detail in error["details"])


@pytest.mark.parametrize(
    "method,resource,suffix,field",
    [
        ("POST", "products", "", "category_id"),
        ("PUT", "products", "/{id}", "category_id"),
        ("POST", "reviews", "", "product_id"),
        ("PUT", "reviews", "/{id}", "product_id"),
        ("PATCH", "reviews", "/{id}", "product_id"),
    ],
)
def test_unknown_foreign_key_returns_404(
    client, records, payloads, method, resource, suffix, field
):
    path = f"{BASE}/{resource}" + suffix.format(id=records[resource]["id"])
    payload = {**payloads[resource], field: UNKNOWN_ID}

    response = client.request(method, path, json=payload)

    assert_error(response, 404)
    assert client.get(f"{BASE}/{resource}/{records[resource]['id']}").json() == records[resource]


@pytest.mark.parametrize("resource", ["categories", "products"])
def test_parent_with_children_cannot_be_deleted(client, records, resource):
    path = f"{BASE}/{resource}/{records[resource]['id']}"

    response = client.delete(path)

    assert_error(response, 409)
    assert client.get(path).json() == records[resource]


@pytest.mark.parametrize(
    "resource,changes,expected,nullable",
    [
        ("categories", {"name": "  Fiction  "}, {"name": "Fiction"}, "description"),
        ("reviews", {"rating": 1}, {"rating": 1}, "text"),
    ],
)
def test_patch_preserves_missing_fields_and_accepts_explicit_null(
    client, records, resource, changes, expected, nullable
):
    record = records[resource]
    path = f"{BASE}/{resource}/{record['id']}"

    response = client.patch(path, json=changes)

    assert response.status_code == 200
    assert response.json() == {**record, **expected}
    assert client.get(path).json() == response.json()
    unchanged = client.patch(path, json={})
    assert unchanged.status_code == 200 and unchanged.json() == response.json()
    cleared = client.patch(path, json={nullable: None})
    assert cleared.status_code == 200
    assert cleared.json() == {**record, **expected, nullable: None}
    assert client.get(path).json() == cleared.json()


@pytest.mark.parametrize(
    "resource,payload",
    [
        ("categories", {"name": None}),
        ("categories", {"name": "   "}),
        ("categories", {"name": "x" * 81}),
        ("categories", {"description": "x" * 501}),
        ("categories", {"id": UNKNOWN_ID}),
        ("reviews", {"product_id": None}),
        ("reviews", {"rating": None}),
        ("reviews", {"rating": 0}),
        ("reviews", {"rating": 6}),
        ("reviews", {"text": "x" * 1001}),
        ("reviews", {"user_id": UNKNOWN_ID}),
    ],
)
def test_patch_retains_constraints_and_rejects_nonnullable_null(client, records, resource, payload):
    path = f"{BASE}/{resource}/{records[resource]['id']}"

    response = client.patch(path, json=payload)

    assert assert_error(response, 422)["details"]
    assert client.get(path).json() == records[resource]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 1000},
        {"offset": -1},
        {"sort_by": "seller_id"},
        {"condition": "broken"},
        {"min_price": -1},
        {"max_price": -1},
    ],
)
def test_product_list_rejects_invalid_query(client, params):
    response = client.get(f"{BASE}/products", params=params)

    error = assert_error(response, 422)
    assert any(detail["field"].startswith("query.") for detail in error["details"])


@pytest.fixture
def catalog(client, records):
    client.delete(f"{BASE}/reviews/{records['reviews']['id']}")
    client.delete(f"{BASE}/products/{records['products']['id']}")
    base = {"category_id": records["categories"]["id"], "price": 25, "stock": 2}
    create(client, "products", {**base, "name": "Used", "condition": "used"})
    create(client, "products", {**base, "name": "Cheap", "price": 5, "stock": 5})
    create(client, "products", {**base, "name": "C", "price": 30, "stock": 3})
    create(client, "products", {**base, "name": "A", "price": 20, "stock": 6})
    create(client, "products", {**base, "name": "B", "stock": 4})
    create(client, "products", {**base, "name": "Expensive", "price": 50, "stock": 1})


@pytest.mark.parametrize(
    "params,expected",
    [
        ({}, ["A", "B", "C", "Cheap", "Expensive", "Used"]),
        ({"sort_by": "name"}, ["A", "B", "C", "Cheap", "Expensive", "Used"]),
        ({"sort_by": "stock"}, ["Expensive", "Used", "C", "B", "Cheap", "A"]),
        ({"sort_by": "price", "condition": "new"}, ["Cheap", "A", "B", "C", "Expensive"]),
    ],
)
def test_product_sorting(client, catalog, params, expected):
    response = client.get(f"{BASE}/products", params=params)

    assert response.status_code == 200
    assert [product["name"] for product in response.json()] == expected


def test_filtering_and_sorting_happen_before_pagination(client, catalog):
    params = {
        "condition": "new",
        "min_price": 20,
        "max_price": 30,
        "sort_by": "price",
        "limit": 1,
        "offset": 1,
    }

    response = client.get(f"{BASE}/products", params=params)

    assert response.status_code == 200
    assert [product["name"] for product in response.json()] == ["B"]


def test_filtered_pages_do_not_overlap_and_include_range_boundaries(client, catalog):
    params = {"condition": "new", "min_price": 20, "max_price": 30, "limit": 2}

    first = client.get(f"{BASE}/products", params={**params, "offset": 0})
    second = client.get(f"{BASE}/products", params={**params, "offset": 2})
    beyond_end = client.get(f"{BASE}/products", params={**params, "offset": 99})

    assert first.status_code == second.status_code == beyond_end.status_code == 200
    assert [product["name"] for product in first.json()] == ["A", "B"]
    assert [product["name"] for product in second.json()] == ["C"]
    assert beyond_end.json() == []


@pytest.mark.parametrize(
    "method,resource",
    [
        ("PATCH", "products"),
        ("POST", "categories"),
        ("POST", "products"),
        ("POST", "reviews"),
    ],
)
def test_method_not_allowed_uses_error_envelope_and_retains_allow(
    client, records, method, resource
):
    path = f"{BASE}/{resource}/{records[resource]['id']}"

    response = client.request(method, path, json={})

    assert_error(response, 405)
    allowed = response.headers["Allow"].split(", ")
    assert allowed
    assert method not in allowed
    assert set(allowed) <= {"GET", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def test_openapi_describes_service_tags_and_product_query_defaults(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] != "FastAPI"
    assert schema["info"]["version"]
    assert schema["info"]["description"]
    tags = {tag["name"]: tag["description"] for tag in schema["tags"]}
    assert tags["categories"] and tags["products"] and tags["reviews"]
    parameters = {
        parameter["name"]: parameter["schema"]
        for parameter in schema["paths"][f"{BASE}/products"]["get"]["parameters"]
    }
    assert parameters["limit"]["default"] == 20
    assert parameters["limit"]["minimum"] == 1
    assert parameters["limit"]["maximum"] == 100
    assert parameters["offset"]["minimum"] == 0
    assert parameters["sort_by"]["default"] == "name"
    assert not any("vuln" in path for path in schema["paths"])


@pytest.mark.parametrize("method,resource,suffix", INPUT_OPERATIONS)
def test_openapi_input_schemas_forbid_extras_and_include_examples(client, method, resource, suffix):
    id_name = {"categories": "category_id", "products": "product_id", "reviews": "review_id"}[
        resource
    ]
    path = f"{BASE}/{resource}" + suffix.format(id="{" + id_name + "}")
    document = client.get("/openapi.json").json()
    operation = document["paths"][path][method.lower()]
    reference = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]

    schema = document["components"]["schemas"][reference.rsplit("/", 1)[1]]

    assert operation["tags"] == [resource]
    assert operation["summary"] and operation["description"]
    assert "422" in operation["responses"]
    assert schema["additionalProperties"] is False
    assert schema.get("examples") or any(
        field.get("examples") for field in schema["properties"].values()
    )


def test_teaching_vulnerability_is_only_in_separate_app(client, payloads):
    from app.vuln import app as vulnerable_app

    payload = {**payloads["products"], "seller_id": UNKNOWN_ID}

    safe_response = client.post(f"{BASE}/products", json=payload)
    with TestClient(vulnerable_app) as vulnerable_client:
        vulnerable_response = vulnerable_client.post(f"{BASE}/products", json=payload)

    assert_error(safe_response, 422)
    assert vulnerable_response.status_code == 201
    assert vulnerable_response.json()["seller_id"] == UNKNOWN_ID


@pytest.mark.parametrize(
    "schema_name,field,field_type",
    [
        ("CategoryPatch", "name", "string"),
        ("ReviewPatch", "product_id", "string"),
        ("ReviewPatch", "rating", "integer"),
    ],
)
def test_patch_openapi_allows_omission_but_not_null(client, schema_name, field, field_type):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    schema = schemas[schema_name]

    assert field not in schema.get("required", [])
    assert schema["properties"][field].get("type") == field_type
