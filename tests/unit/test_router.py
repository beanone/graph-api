"""Unit tests for the FastAPI router.

This module contains unit tests for the FastAPI router, which provides
the HTTP endpoints for graph operations.
"""

from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from graph_api.api.router import router
from graph_api.services.graph_service import GraphService
from graph_context import (
    BaseGraphContext,
    EntityNotFoundError,
    RelationNotFoundError,
    SchemaError,
    TransactionError,
    ValidationError,
)
from graph_context.types import (
    EntityType,
    PropertyDefinition,
    PropertyType,
    QueryCondition,
    QueryOperator,
    QuerySpec,
    RelationType,
)


@pytest_asyncio.fixture
async def graph_context() -> AsyncGenerator[BaseGraphContext, None]:
    """Create a real graph context for testing.

    Yields:
        BaseGraphContext: A real graph context instance.
    """
    context = BaseGraphContext()

    # Register entity types
    person_type = EntityType(
        name="Person",
        description="A person entity",
        properties={
            "name": PropertyDefinition(type=PropertyType.STRING, required=True),
            "age": PropertyDefinition(type=PropertyType.INTEGER, required=True),
        },
        indexes=["name", "age"],
    )
    await context.register_entity_type(person_type)

    # Register relation types
    knows_type = RelationType(
        name="KNOWS",
        description="A relationship between two people",
        properties={
            "since": PropertyDefinition(type=PropertyType.INTEGER, required=True)
        },
        indexes=["since"],
        from_types=["Person"],
        to_types=["Person"],
    )
    await context.register_relation_type(knows_type)

    yield context

    # Cleanup after tests
    try:
        entities = await context.query({"entity_type": "*"})
        for entity in entities:
            await context.delete_entity(entity["id"])
    except Exception as e:
        print(f"Error during test cleanup: {e}")
        raise  # Re-raise the exception to ensure cleanup failures are visible


@pytest_asyncio.fixture
async def graph_service(graph_context: BaseGraphContext) -> GraphService:
    """Create a test graph service with real context.

    Args:
        graph_context: The real graph context fixture.

    Returns:
        GraphService: A configured graph service instance.
    """
    return GraphService(graph_context)


@pytest.fixture
def app(graph_service: GraphService, graph_context: BaseGraphContext) -> FastAPI:
    """Create a FastAPI application for testing.

    Args:
        graph_service: The graph service fixture.
        graph_context: The graph context fixture.

    Returns:
        FastAPI: A configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(router)
    app.state.graph_context = graph_context
    app.dependency_overrides = {"get_graph_service": lambda: graph_service}
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application.

    Args:
        app: The FastAPI application fixture.

    Returns:
        TestClient: A configured test client.
    """
    return TestClient(app)


@pytest.mark.asyncio
async def test_create_entity_success(client: TestClient) -> None:
    """Test successful entity creation."""
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_create_entity_validation_error(client: TestClient) -> None:
    """Test entity creation with validation error."""
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": "invalid"},  # Invalid age type
    }

    # Act
    response = client.post("/api/v1/entities", json=entity_data)

    # Assert
    assert response.status_code == 400
    error = response.json()
    assert "message" in error["detail"]
    assert "Value must be an integer" in error["detail"]["message"]


@pytest.mark.asyncio
async def test_get_entity_success(client: TestClient) -> None:
    """Test successful entity retrieval."""
    # Arrange
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
    result = response.json()
    assert result["id"] == entity_id
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_get_entity_not_found(client: TestClient) -> None:
    """Test entity retrieval when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"

    # Act
    response = client.get(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_update_entity_success(client: TestClient) -> None:
    """Test successful entity update."""
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    create_response = client.post("/api/v1/entities", json=entity_data)
    entity_id = create_response.json()["id"]

    update_data = {"name": "John Doe Updated", "age": 31}

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    if response.status_code != 200:
        print(f"Update entity error: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == entity_id
    assert result["properties"]["name"] == "John Doe Updated"
    assert result["properties"]["age"] == 31


@pytest.mark.asyncio
async def test_update_entity_not_found(client: TestClient) -> None:
    """Test entity update when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"
    update_data = {"properties": {"age": 31}}

    # Act
    response = client.put(f"/api/v1/entities/{entity_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_delete_entity_success(client: TestClient) -> None:
    """Test successful entity deletion."""
    # Arrange
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

    # Verify entity is deleted
    get_response = client.get(f"/api/v1/entities/{entity_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_entity_not_found(client: TestClient) -> None:
    """Test entity deletion when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"

    # Act
    response = client.delete(f"/api/v1/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_create_relation_success(client: TestClient) -> None:
    """Test successful relation creation."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": 2020},
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["type"] == "KNOWS"
    assert result["from_entity"] == person1_id
    assert result["to_entity"] == person2_id
    assert result["properties"]["since"] == 2020


@pytest.mark.asyncio
async def test_create_relation_validation_error(client: TestClient) -> None:
    """Test relation creation with validation error."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": "invalid"},  # Invalid since type
    }

    # Act
    response = client.post("/api/v1/relations", json=relation_data)

    # Assert
    assert response.status_code == 400
    error = response.json()
    assert "message" in error["detail"]
    assert "Value must be an integer" in error["detail"]["message"]


@pytest.mark.asyncio
async def test_get_relation_success(client: TestClient) -> None:
    """Test successful relation retrieval."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": 2020},
    }
    create_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_response.json()["id"]

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == relation_id
    assert result["type"] == "KNOWS"
    assert result["from_entity"] == person1_id
    assert result["to_entity"] == person2_id
    assert result["properties"]["since"] == 2020


@pytest.mark.asyncio
async def test_get_relation_not_found(client: TestClient) -> None:
    """Test relation retrieval when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"

    # Act
    response = client.get(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_update_relation_success(client: TestClient) -> None:
    """Test successful relation update."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": 2020},
    }
    create_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_response.json()["id"]

    update_data = {"since": 2021}

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    if response.status_code != 200:
        print(f"Update relation error: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == relation_id
    assert result["type"] == "KNOWS"
    assert result["properties"]["since"] == 2021


@pytest.mark.asyncio
async def test_update_relation_not_found(client: TestClient) -> None:
    """Test relation update when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"
    update_data = {"properties": {"since": 2021}}

    # Act
    response = client.put(f"/api/v1/relations/{relation_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_delete_relation_success(client: TestClient) -> None:
    """Test successful relation deletion."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": 2020},
    }
    create_response = client.post("/api/v1/relations", json=relation_data)
    relation_id = create_response.json()["id"]

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 200

    # Verify relation is deleted
    get_response = client.get(f"/api/v1/relations/{relation_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_relation_not_found(client: TestClient) -> None:
    """Test relation deletion when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"

    # Act
    response = client.delete(f"/api/v1/relations/{relation_id}")

    # Assert
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error


@pytest.mark.asyncio
async def test_query_success(client: TestClient) -> None:
    """Test successful query."""
    # Arrange
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_response = client.post("/api/v1/entities", json=person1_data)
    person2_response = client.post("/api/v1/entities", json=person2_data)
    person1_id = person1_response.json()["id"]
    person2_id = person2_response.json()["id"]

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_id,
        "to_entity": person2_id,
        "properties": {"since": 2020},
    }
    client.post("/api/v1/relations", json=relation_data)

    query_data = {
        "query_spec": {
            "entity_type": "Person",
            "conditions": [
                {
                    "field": "name",
                    "operator": "eq",
                    "value": "John Doe",
                }
            ],
        }
    }

    # Act
    response = client.post("/api/v1/query", json=query_data)

    # Assert
    if response.status_code != 200:
        print(f"Query error: {response.json()}")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["id"] == person1_id
    assert results[0]["entity_type"] == "Person"
    assert results[0]["properties"]["name"] == "John Doe"
    assert results[0]["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_query_validation_error(client: TestClient) -> None:
    """Test query with validation error."""
    # Arrange
    query_data = {
        "query_spec": {
            "conditions": [
                {
                    "field": "invalid_field",
                    "operator": "INVALID_OPERATOR",
                    "value": "invalid_value",
                }
            ]
        }
    }

    # Act
    response = client.post("/api/v1/query", json=query_data)

    # Assert
    assert response.status_code == 422
    error = response.json()
    print("--------------------------------")
    print(error)
    print("--------------------------------")
    assert "missing" == error["detail"][0]["type"]


@pytest.mark.asyncio
async def test_register_entity_type_success(client: TestClient) -> None:
    """Test successful entity type registration."""
    # Arrange
    entity_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "founded": {"type": "integer", "required": True},
        },
        "indexes": ["name", "founded"],
    }

    # Act
    response = client.post("/api/v1/entity-types", json=entity_type_data)

    # Assert
    if response.status_code != 200:
        print(f"Register entity type error: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "Company" in result["message"]


@pytest.mark.asyncio
async def test_register_entity_type_validation_error(client: TestClient) -> None:
    """Test entity type registration with validation error."""
    # Arrange
    entity_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "INVALID_TYPE", "required": True},  # Invalid type
        },
        "indexes": ["name"],
    }

    # Act
    response = client.post("/api/v1/entity-types", json=entity_type_data)

    # Assert
    assert response.status_code == 400
    error = response.json()
    assert "message" in error["detail"]


@pytest.mark.asyncio
async def test_register_relation_type_success(client: TestClient) -> None:
    """Test successful relation type registration."""
    # Arrange
    # First register the Company entity type
    company_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "founded": {"type": "integer", "required": True},
        },
        "indexes": ["name", "founded"],
    }
    company_response = client.post("/api/v1/entity-types", json=company_type_data)
    assert company_response.status_code == 200

    # Now register the relation type
    relation_type_data = {
        "name": "WORKS_AT",
        "description": "A relationship between a person and a company",
        "properties": {
            "role": {"type": "string", "required": True},
            "start_date": {"type": "integer", "required": True},
        },
        "indexes": ["role", "start_date"],
        "from_types": ["Person"],
        "to_types": ["Company"],
    }

    # Act
    response = client.post("/api/v1/relation-types", json=relation_type_data)

    # Assert
    if response.status_code != 200:
        print(f"Register relation type error: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert "WORKS_AT" in result["message"]


@pytest.mark.asyncio
async def test_register_relation_type_validation_error(client: TestClient) -> None:
    """Test relation type registration with validation error."""
    # Arrange
    relation_type_data = {
        "name": "WORKS_AT",
        "description": "A relationship between a person and a company",
        "properties": {
            "role": {"type": "INVALID_TYPE", "required": True},  # Invalid type
        },
        "indexes": ["role"],
        "from_types": ["Person"],
        "to_types": ["Company"],
    }

    # Act
    response = client.post("/api/v1/relation-types", json=relation_type_data)

    # Assert
    assert response.status_code == 400
    error = response.json()
    assert "message" in error["detail"]


@pytest.mark.asyncio
async def test_has_entity_type_exists(client: TestClient) -> None:
    """Test checking if an entity type exists."""
    # First register an entity type
    entity_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "founded": {"type": "integer", "required": True},
        },
        "indexes": ["name", "founded"],
    }
    client.post("/api/v1/entity-types", json=entity_type_data)

    # Check if it exists
    response = client.get("/api/v1/entity-types/Company")
    assert response.status_code == 200
    assert response.json()["message"] == "Entity type Company exists"


@pytest.mark.asyncio
async def test_has_entity_type_not_exists(client: TestClient) -> None:
    """Test checking if a non-existent entity type exists."""
    response = client.get("/api/v1/entity-types/NonExistentType")
    assert response.status_code == 404
    assert (
        response.json()["detail"]["message"] == "Entity type NonExistentType not found"
    )


@pytest.mark.asyncio
async def test_has_relation_type_exists(client: TestClient) -> None:
    """Test checking if a relation type exists."""
    # First register required entity types
    company_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
        },
    }
    client.post("/api/v1/entity-types", json=company_type_data)

    # Register a relation type
    relation_type_data = {
        "name": "WORKS_AT",
        "description": "A relationship between person and company",
        "properties": {
            "role": {"type": "string", "required": True},
        },
        "from_types": ["Person"],
        "to_types": ["Company"],
    }
    client.post("/api/v1/relation-types", json=relation_type_data)

    # Check if it exists
    response = client.get("/api/v1/relation-types/WORKS_AT")
    assert response.status_code == 200
    assert response.json()["message"] == "Relation type WORKS_AT exists"


@pytest.mark.asyncio
async def test_has_relation_type_not_exists(client: TestClient) -> None:
    """Test checking if a non-existent relation type exists."""
    response = client.get("/api/v1/relation-types/NonExistentType")
    assert response.status_code == 404
    assert (
        response.json()["detail"]["message"]
        == "Relation type NonExistentType not found"
    )


@pytest.mark.asyncio
async def test_register_entity_type_already_exists(client: TestClient) -> None:
    """Test registering an entity type that already exists."""
    # First register an entity type
    entity_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "founded": {"type": "integer", "required": True},
        },
        "indexes": ["name", "founded"],
    }
    client.post("/api/v1/entity-types", json=entity_type_data)

    # Try to register the same entity type again
    response = client.post("/api/v1/entity-types", json=entity_type_data)
    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "Entity type Company already exists"


@pytest.mark.asyncio
async def test_register_relation_type_already_exists(client: TestClient) -> None:
    """Test registering a relation type that already exists."""
    # First register required entity types
    company_type_data = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
        },
    }
    client.post("/api/v1/entity-types", json=company_type_data)

    # Register a relation type
    relation_type_data = {
        "name": "WORKS_AT",
        "description": "A relationship between person and company",
        "properties": {
            "role": {"type": "string", "required": True},
        },
        "from_types": ["Person"],
        "to_types": ["Company"],
    }
    client.post("/api/v1/relation-types", json=relation_type_data)

    # Try to register the same relation type again
    response = client.post("/api/v1/relation-types", json=relation_type_data)
    assert response.status_code == 409
    assert (
        response.json()["detail"]["message"] == "Relation type WORKS_AT already exists"
    )
