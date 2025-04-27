"""Unit tests for the Graph API."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from graph_api.main import app
from graph_context import BaseGraphContext


@pytest_asyncio.fixture
async def graph_context():
    """Create a test graph context."""
    return BaseGraphContext()


@pytest.fixture
def client(graph_context):
    """Create a test client with graph context."""
    app.state.graph_context = graph_context
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_entity(client):
    """Test creating an entity."""
    response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "John Doe", "age": 30}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["entity_type"] == "Person"
    assert data["properties"]["name"] == "John Doe"
    assert data["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_get_entity(client):
    """Test getting an entity."""
    # First create an entity

    create_response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "Jane Doe", "age": 25}},
    )
    entity_id = create_response.json()["id"]

    # Then get it

    response = client.get(f"/api/v1/entities/{entity_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entity_id
    assert data["entity_type"] == "Person"
    assert data["properties"]["name"] == "Jane Doe"
    assert data["properties"]["age"] == 25


@pytest.mark.asyncio
async def test_create_relation(client):
    """Test creating a relation."""
    # First create two entities

    entity1_response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "Alice"}},
    )
    entity2_response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "Bob"}},
    )
    entity1_id = entity1_response.json()["id"]
    entity2_id = entity2_response.json()["id"]

    # Then create a relation between them

    response = client.post(
        "/api/v1/relations",
        json={
            "relation_type": "KNOWS",
            "from_entity": entity1_id,
            "to_entity": entity2_id,
            "properties": {"since": 2023},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["relation_type"] == "KNOWS"
    assert data["from_entity"] == entity1_id
    assert data["to_entity"] == entity2_id
    assert data["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_query_relations(client):
    """Test querying relations."""
    # First create two entities and a relation

    entity1_response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "Alice"}},
    )
    entity2_response = client.post(
        "/api/v1/entities",
        json={"entity_type": "Person", "properties": {"name": "Bob"}},
    )
    entity1_id = entity1_response.json()["id"]
    entity2_id = entity2_response.json()["id"]

    client.post(
        "/api/v1/relations",
        json={
            "relation_type": "KNOWS",
            "from_entity": entity1_id,
            "to_entity": entity2_id,
            "properties": {"since": 2023},
        },
    )

    # Then query the relations using the correct format from graph-context

    response = client.post(
        "/api/v1/query",
        json={
            "entity_type": "Person",
            "conditions": [
                {
                    "relation_type": "KNOWS",
                    "from_entity": entity1_id,
                    "direction": "outbound",
                }
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(
        relation["from_entity"] == entity1_id
        and relation["to_entity"] == entity2_id
        and relation["relation_type"] == "KNOWS"
        for relation in data
    )
