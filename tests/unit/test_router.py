"""Unit tests for the API router.

This module contains unit tests for the FastAPI router endpoints,
including entity and relation management.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from graph_api.api.router import router
from graph_api.models.base import (
    EntityCreate,
    EntityUpdate,
    QuerySpec,
    RelationCreate,
    RelationUpdate,
)
from graph_api.services.graph_service import GraphService
from graph_context.exceptions import (
    EntityNotFoundError,
    RelationNotFoundError,
    SchemaError,
    TransactionError,
    ValidationError,
)


@pytest.fixture
def mock_service() -> AsyncMock:
    """Create a mock graph service.

    Returns:
        AsyncMock: A mock graph service instance
    """
    return AsyncMock(spec=GraphService)


@pytest.fixture
def app(mock_service: AsyncMock) -> FastAPI:
    """Create a FastAPI test application.

    Args:
        mock_service: The mock graph service

    Returns:
        FastAPI: A configured FastAPI application
    """
    app = FastAPI()
    app.include_router(router)

    async def get_service() -> GraphService:
        return mock_service

    app.dependency_overrides[GraphService] = get_service
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


def test_create_entity_success(client: TestClient, mock_service: AsyncMock) -> None:
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
    mock_service.create_entity.return_value = {
        "id": "entity-123",
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == "entity-123"
    assert response.json()["entity_type"] == "Person"
    assert response.json()["properties"]["name"] == "John Doe"
    assert response.json()["properties"]["age"] == 30


def test_create_entity_validation_error(
    client: TestClient, mock_service: AsyncMock
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
        "Invalid age type",
        field="age",
        constraint="must be integer",
    )

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid age type"
    assert response.json()["detail"]["field"] == "age"
    assert response.json()["detail"]["constraint"] == "must be integer"


def test_create_entity_schema_error(
    client: TestClient, mock_service: AsyncMock
) -> None:
    """Test entity creation with schema error.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_data = {
        "entity_type": "InvalidType",
        "properties": {"name": "John Doe"},
    }
    mock_service.create_entity.side_effect = SchemaError(
        "Invalid entity type",
        schema_type="entity_type",
    )

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid entity type"
    assert response.json()["detail"]["schema_type"] == "entity_type"


def test_get_entity_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful entity retrieval.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "entity-123"
    mock_service.get_entity.return_value = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }

    # Act
    response = client.get(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == entity_id
    assert response.json()["entity_type"] == "Person"
    assert response.json()["properties"]["name"] == "John Doe"
    assert response.json()["properties"]["age"] == 30


def test_get_entity_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test entity retrieval when entity doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "non-existent"
    mock_service.get_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act
    response = client.get(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_update_entity_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful entity update.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "entity-123"
    update_data = {"properties": {"age": 31}}
    mock_service.update_entity.return_value = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 31},
    }

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == entity_id
    assert response.json()["properties"]["age"] == 31


def test_update_entity_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test entity update when entity doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "non-existent"
    update_data = {"properties": {"age": 31}}
    mock_service.update_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_delete_entity_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful entity deletion.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "entity-123"

    # Act
    response = client.delete(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Entity deleted successfully"


def test_delete_entity_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test entity deletion when entity doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    entity_id = "non-existent"
    mock_service.delete_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act
    response = client.delete(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Entity {entity_id} not found"


def test_create_relation_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful relation creation.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }
    mock_service.create_relation.return_value = {
        "id": "relation-123",
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == "relation-123"
    assert response.json()["relation_type"] == "KNOWS"
    assert response.json()["from_entity"] == "person-1"
    assert response.json()["to_entity"] == "person-2"
    assert response.json()["properties"]["since"] == 2023


def test_create_relation_entity_not_found(
    client: TestClient, mock_service: AsyncMock
) -> None:
    """Test relation creation when entity doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": "non-existent",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }
    mock_service.create_relation.side_effect = EntityNotFoundError(
        "Entity non-existent not found"
    )

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Entity non-existent not found"


def test_get_relation_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful relation retrieval.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "relation-123"
    mock_service.get_relation.return_value = {
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == relation_id
    assert response.json()["relation_type"] == "KNOWS"
    assert response.json()["from_entity"] == "person-1"
    assert response.json()["to_entity"] == "person-2"
    assert response.json()["properties"]["since"] == 2023


def test_get_relation_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test relation retrieval when relation doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "non-existent"
    mock_service.get_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_update_relation_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful relation update.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "relation-123"
    update_data = {"properties": {"since": 2024}}
    mock_service.update_relation.return_value = {
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2024},
    }

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == relation_id
    assert response.json()["properties"]["since"] == 2024


def test_update_relation_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test relation update when relation doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "non-existent"
    update_data = {"properties": {"since": 2024}}
    mock_service.update_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_delete_relation_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful relation deletion.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "relation-123"

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Relation deleted successfully"


def test_delete_relation_not_found(client: TestClient, mock_service: AsyncMock) -> None:
    """Test relation deletion when relation doesn't exist.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    relation_id = "non-existent"
    mock_service.delete_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == f"Relation {relation_id} not found"


def test_query_relations_success(client: TestClient, mock_service: AsyncMock) -> None:
    """Test successful relations query.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    query_spec = {
        "entity_type": "Person",
        "conditions": [
            {
                "relation_type": "KNOWS",
                "from_entity": "person-1",
                "direction": "outbound",
            }
        ],
    }
    mock_service.query.return_value = [
        {
            "id": "relation-123",
            "relation_type": "KNOWS",
            "from_entity": "person-1",
            "to_entity": "person-2",
            "properties": {"since": 2023},
        }
    ]

    # Act
    response = client.post("/api/v1/query", json=query_spec)

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "relation-123"
    assert response.json()[0]["relation_type"] == "KNOWS"
    assert response.json()[0]["from_entity"] == "person-1"
    assert response.json()[0]["to_entity"] == "person-2"
    assert response.json()[0]["properties"]["since"] == 2023


def test_query_relations_validation_error(
    client: TestClient, mock_service: AsyncMock
) -> None:
    """Test relations query with validation error.

    Args:
        client: The test client
        mock_service: The mock graph service
    """
    # Arrange
    query_spec = {
        "entity_type": "Person",
        "conditions": [
            {
                "relation_type": "INVALID",
                "from_entity": "person-1",
                "direction": "outbound",
            }
        ],
    }
    mock_service.query.side_effect = ValidationError(
        "Invalid relation type",
        field="relation_type",
        constraint="must be one of [KNOWS]",
    )

    # Act
    response = client.post("/api/v1/query", json=query_spec)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"]["message"] == "Invalid relation type"
    assert response.json()["detail"]["field"] == "relation_type"
    assert response.json()["detail"]["constraint"] == "must be one of [KNOWS]"
