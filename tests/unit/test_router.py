"""Unit tests for the API router.

This module contains unit tests for the FastAPI router endpoints,
including entity and relation management.
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from graph_api.api.router import router
from graph_api.models.base import (
    EntityCreate,
    EntityUpdate,
    QueryRequest,
    RelationCreate,
    RelationUpdate,
)
from graph_api.services.graph_service import get_graph_service, GraphService
from graph_context import BaseGraphContext
from graph_context.exceptions import (
    EntityNotFoundError,
    RelationNotFoundError,
    SchemaError,
    TransactionError,
    ValidationError,
)


@pytest.fixture
def mock_context() -> AsyncMock:
    """Create a mock graph context.

    Returns:
        AsyncMock: A mock graph context
    """
    context = AsyncMock(spec=BaseGraphContext)
    return context


@pytest.fixture
def mock_service() -> GraphService:
    """Create a mock graph service.

    Returns:
        The mock graph service
    """
    service = GraphService()
    service.create_entity = AsyncMock()
    service.get_entity = AsyncMock()
    service.update_entity = AsyncMock()
    service.delete_entity = AsyncMock()
    service.create_relation = AsyncMock()
    service.get_relation = AsyncMock()
    service.update_relation = AsyncMock()
    service.delete_relation = AsyncMock()
    service.query = AsyncMock()
    return service


@pytest.fixture
def app(mock_service: GraphService) -> FastAPI:
    """Create a FastAPI test application.

    Args:
        mock_service: The mock graph service

    Returns:
        FastAPI: A configured FastAPI application
    """
    app = FastAPI()
    app.include_router(router)

    async def get_test_service() -> GraphService:
        return mock_service

    app.dependency_overrides[get_graph_service] = get_test_service
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client.

    Args:
        app: The FastAPI application

    Returns:
        TestClient: A configured test client
    """
    return TestClient(app)


def test_create_entity_success(client: TestClient, mock_service: GraphService) -> None:
    """Test successful entity creation.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    expected_response = {
        "id": "entity-123",
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    mock_service.create_entity.return_value = expected_response

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response
    mock_service.create_entity.assert_called_once_with(EntityCreate(**entity_data))


def test_create_entity_validation_error(
    client: TestClient, mock_service: GraphService
) -> None:
    """Test entity creation with validation error.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": "invalid"},
    }
    mock_service.create_entity.side_effect = ValidationError(
        message="Invalid age type", field="age", constraint="must be integer"
    )

    # Act
    response = client.post("/entities", json=entity_data)

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "message": "Invalid age type",
            "field": "age",
            "constraint": "must be integer",
        }
    }
    mock_service.create_entity.assert_called_once_with(EntityCreate(**entity_data))


def test_create_entity_schema_error(client: TestClient) -> None:
    """Test entity creation with schema error.

    Args:
        client: The test client
    """
    # Arrange
    entity_data = {
        "entity_type": "InvalidType",
        "properties": {"name": "John Doe"},
    }

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid entity type"
    assert response.json()["detail"]["schema_type"] == "entity_type"


def test_get_entity_success(client: TestClient) -> None:
    """Test successful entity retrieval.

    Args:
        client: The test client
    """
    # Arrange
    # First create an entity
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    create_response = client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]

    # Act
    response = client.get(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == entity_id
    assert response.json()["entity_type"] == "Person"
    assert response.json()["properties"]["name"] == "John Doe"
    assert response.json()["properties"]["age"] == 30


def test_get_entity_not_found(client: TestClient) -> None:
    """Test entity retrieval with not found error.

    Args:
        client: The test client
    """
    # Arrange
    entity_id = "non-existent"

    # Act
    response = client.get(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_update_entity_success(client: TestClient) -> None:
    """Test successful entity update.

    Args:
        client: The test client
    """
    # Arrange
    # First create an entity
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    create_response = client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]

    # Update data
    update_data = {
        "properties": {"name": "John Doe", "age": 31},
    }

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == entity_id
    assert response.json()["properties"]["age"] == 31


def test_update_entity_not_found(client: TestClient) -> None:
    """Test entity update with not found error.

    Args:
        client: The test client
    """
    # Arrange
    entity_id = "non-existent"
    update_data = {
        "properties": {"name": "John Doe", "age": 31},
    }

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_delete_entity_success(client: TestClient) -> None:
    """Test successful entity deletion.

    Args:
        client: The test client
    """
    # Arrange
    # First create an entity
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    create_response = client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]

    # Act
    response = client.delete(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Entity deleted successfully"

    # Verify entity is actually deleted
    get_response = client.get(f"/api/v1/entities/{entity_id}")
    assert get_response.status_code == 404


def test_delete_entity_not_found(client: TestClient) -> None:
    """Test entity deletion with not found error.

    Args:
        client: The test client
    """
    # Arrange
    entity_id = "non-existent"

    # Act
    response = client.delete(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_create_relation_success(client: TestClient) -> None:
    """Test successful relation creation.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    # Create relation
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["relation_type"] == "KNOWS"
    assert response.json()["from_entity"] == entity1_id
    assert response.json()["to_entity"] == entity2_id
    assert response.json()["properties"]["since"] == 2023


def test_create_relation_entity_not_found(client: TestClient) -> None:
    """Test relation creation with entity not found error.

    Args:
        client: The test client
    """
    # Arrange
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": "non-existent",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Entity non-existent not found"


def test_create_relation_schema_error(client: TestClient) -> None:
    """Test relation creation with schema error.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    # Create relation with invalid type
    relation_data = {
        "relation_type": "INVALID",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid relation type"
    assert response.json()["detail"]["schema_type"] == "relation_type"


def test_create_relation_validation_error(client: TestClient) -> None:
    """Test relation creation with validation error.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    # Create relation with invalid property
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": "invalid"},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid since type"
    assert response.json()["detail"]["field"] == "since"
    assert response.json()["detail"]["constraint"] == "must be integer"


def test_get_relation_success(client: TestClient) -> None:
    """Test successful relation retrieval.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities and a relation
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }
    create_relation_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_relation_response.json()["id"]

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == relation_id
    assert response.json()["relation_type"] == "KNOWS"
    assert response.json()["from_entity"] == entity1_id
    assert response.json()["to_entity"] == entity2_id
    assert response.json()["properties"]["since"] == 2023


def test_get_relation_not_found(client: TestClient) -> None:
    """Test relation retrieval with not found error.

    Args:
        client: The test client
    """
    # Arrange
    relation_id = "non-existent"

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_update_relation_success(client: TestClient) -> None:
    """Test successful relation update.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities and a relation
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }
    create_relation_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_relation_response.json()["id"]

    # Update data
    update_data = {
        "properties": {"since": 2024},
    }

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == relation_id
    assert response.json()["properties"]["since"] == 2024


def test_update_relation_not_found(client: TestClient) -> None:
    """Test relation update with not found error.

    Args:
        client: The test client
    """
    # Arrange
    relation_id = "non-existent"
    update_data = {
        "properties": {"since": 2024},
    }

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_delete_relation_success(client: TestClient) -> None:
    """Test successful relation deletion.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities and a relation
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }
    create_relation_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_relation_response.json()["id"]

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Relation deleted successfully"

    # Verify relation is actually deleted
    get_response = client.get(f"/api/v1/relations/{relation_id}")
    assert get_response.status_code == 404


def test_delete_relation_not_found(client: TestClient) -> None:
    """Test relation deletion with not found error.

    Args:
        client: The test client
    """
    # Arrange
    relation_id = "non-existent"

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_query_relations_success(client: TestClient) -> None:
    """Test successful relation query.

    Args:
        client: The test client
    """
    # Arrange
    # First create two entities and a relation
    entity1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe"},
    }
    entity2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe"},
    }
    create_response1 = client.post("/api/v1/entities", json=entity1_data)
    create_response2 = client.post("/api/v1/entities", json=entity2_data)
    entity1_id = create_response1.json()["id"]
    entity2_id = create_response2.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
        "to_entity": entity2_id,
        "properties": {"since": 2023},
    }
    create_relation_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_relation_response.json()["id"]

    # Query data
    query_data = {
        "relation_type": "KNOWS",
        "from_entity": entity1_id,
    }

    # Act
    response = client.post("/api/v1/query", json=query_data)

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == relation_id
    assert response.json()[0]["relation_type"] == "KNOWS"
    assert response.json()[0]["from_entity"] == entity1_id
    assert response.json()[0]["to_entity"] == entity2_id
    assert response.json()[0]["properties"]["since"] == 2023


def test_query_relations_validation_error(client: TestClient) -> None:
    """Test relation query with validation error.

    Args:
        client: The test client
    """
    # Arrange
    query_data = {
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "properties": {"since": "invalid"},
    }

    # Act
    response = client.post("/api/v1/query", json=query_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid since type"
    assert response.json()["detail"]["field"] == "since"
    assert response.json()["detail"]["constraint"] == "must be integer"


def test_query_relations_schema_error(client: TestClient) -> None:
    """Test relation query with schema error.

    Args:
        client: The test client
    """
    # Arrange
    query_data = {
        "relation_type": "INVALID",
        "from_entity": "person-1",
    }

    # Act
    response = client.post("/api/v1/query", json=query_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid relation type"
    assert response.json()["detail"]["schema_type"] == "relation_type"
