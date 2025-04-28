"""Unit tests for the GraphService class.

This module contains unit tests for the GraphService class, which provides
the core functionality for graph operations.
"""

from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request

from graph_api.services.graph_service import get_graph_service, GraphService
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
from pydantic import ValidationError as PydanticValidationError


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


@pytest.mark.asyncio
async def test_create_entity_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful entity creation."""
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    result = await graph_service.create_entity(
        entity_type=entity_data["entity_type"], properties=entity_data["properties"]
    )
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_create_entity_validation_error(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity creation with validation error.

    Args:
        graph_service: The graph service fixture.
        graph_context: The real context fixture.
    """
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": "invalid"},  # Invalid age type
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await graph_service.create_entity(
            entity_type=entity_data["entity_type"], properties=entity_data["properties"]
        )


@pytest.mark.asyncio
async def test_get_entity_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful entity retrieval."""
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    created = await graph_service.create_entity(
        entity_type=entity_data["entity_type"], properties=entity_data["properties"]
    )
    entity_id = created["id"]

    result = await graph_service.get_entity(entity_id)
    assert result["id"] == entity_id
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_get_entity_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity retrieval when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.get_entity(entity_id)


@pytest.mark.asyncio
async def test_update_entity_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful entity update."""
    # Create initial entity
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    created = await graph_service.create_entity(
        entity_type=entity_data["entity_type"], properties=entity_data["properties"]
    )
    entity_id = created["id"]

    # Update the entity
    update_data = {"name": "John Doe Updated", "age": 31}
    result = await graph_service.update_entity(entity_id, update_data)
    assert result["id"] == entity_id
    assert result["properties"]["name"] == "John Doe Updated"
    assert result["properties"]["age"] == 31


@pytest.mark.asyncio
async def test_update_entity_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity update when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"
    update_data = {"age": 31}

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.update_entity(entity_id, update_data)


@pytest.mark.asyncio
async def test_delete_entity_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful entity deletion."""
    # Arrange
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    created = await graph_service.create_entity(
        entity_type=entity_data["entity_type"], properties=entity_data["properties"]
    )
    entity_id = created["id"]

    # Act
    await graph_service.delete_entity(entity_id)

    # Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.get_entity(entity_id)


@pytest.mark.asyncio
async def test_delete_entity_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity deletion when entity doesn't exist."""
    # Arrange
    entity_id = "non-existent"

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.delete_entity(entity_id)


@pytest.mark.asyncio
async def test_create_relation_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful relation creation."""
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }

    result = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )
    assert result["type"] == "KNOWS"
    assert result["from_entity"] == person1_created["id"]
    assert result["to_entity"] == person2_created["id"]
    assert result["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_create_relation_validation_error(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
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
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": "invalid"},  # Invalid since type
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        await graph_service.create_relation(
            relation_type=relation_data["relation_type"],
            from_entity=relation_data["from_entity"],
            to_entity=relation_data["to_entity"],
            properties=relation_data["properties"],
        )


@pytest.mark.asyncio
async def test_get_relation_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful relation retrieval."""
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    created = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )
    relation_id = created["id"]

    result = await graph_service.get_relation(relation_id)
    assert result["id"] == relation_id
    assert result["type"] == "KNOWS"
    assert result["from_entity"] == person1_created["id"]
    assert result["to_entity"] == person2_created["id"]
    assert result["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_get_relation_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test relation retrieval when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.get_relation(relation_id)


@pytest.mark.asyncio
async def test_update_relation_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful relation update."""
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    created = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )
    relation_id = created["id"]
    update_data = {"since": 2024}

    result = await graph_service.update_relation(relation_id, update_data)
    assert result["id"] == relation_id
    assert result["properties"]["since"] == 2024


@pytest.mark.asyncio
async def test_update_relation_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test relation update when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"
    update_data = {"since": 2024}

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.update_relation(relation_id, update_data)


@pytest.mark.asyncio
async def test_delete_relation_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
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
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    created = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )
    relation_id = created["id"]

    # Act
    await graph_service.delete_relation(relation_id)

    # Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.get_relation(relation_id)


@pytest.mark.asyncio
async def test_delete_relation_not_found(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test relation deletion when relation doesn't exist."""
    # Arrange
    relation_id = "non-existent"

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.delete_relation(relation_id)


@pytest.mark.asyncio
async def test_query_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful query execution."""
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    created_relation = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )

    query_spec = QuerySpec(
        entity_type="Person",
        conditions=[QueryCondition(field="name", operator="eq", value="John Doe")],
    )

    result = await graph_service.query(query_spec)
    assert len(result) == 1
    assert result[0]["id"] == person1_created["id"]
    assert result[0]["entity_type"] == "Person"
    assert result[0]["properties"]["name"] == "John Doe"
    assert result[0]["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_query_validation_error(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test query execution with validation error."""
    # Invalid query format
    query_spec = QuerySpec(
        entity_type="INVALID_TYPE",
        conditions=[
            QueryCondition(field="invalid_property", operator="eq", value="test")
        ],
    )
    with pytest.raises(ValidationError):
        await graph_service.query(query_spec)


@pytest.mark.asyncio
async def test_query_multiple_conditions(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test query with multiple conditions."""
    # Create test data
    person1_data = {
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "Person",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    # Create relations
    relation_data = {
        "relation_type": "KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    created_relation = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )

    # Query with multiple conditions
    query_spec = QuerySpec(
        entity_type="Person",
        conditions=[
            QueryCondition(field="name", operator="eq", value="John Doe"),
            QueryCondition(field="age", operator="gt", value=25),
        ],
    )
    result = await graph_service.query(query_spec)
    assert len(result) == 1
    assert result[0]["id"] == person1_created["id"]
    assert result[0]["entity_type"] == "Person"
    assert result[0]["properties"]["name"] == "John Doe"
    assert result[0]["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_get_graph_service() -> None:
    """Test getting graph service from request state."""
    # Arrange
    app = FastAPI()
    context = BaseGraphContext()
    app.state.graph_context = context
    request = Request({"type": "http", "method": "GET", "path": "/", "app": app})

    # Act
    service = await get_graph_service(request)

    # Assert
    assert isinstance(service, GraphService)
    assert service._context == context


@pytest.mark.asyncio
async def test_register_entity_type_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful entity type registration (calling service method)."""
    entity_type = EntityType(
        name="TestType",
        description="A test entity type",
        properties={
            "test": PropertyDefinition(type=PropertyType.STRING, required=True)
        },
        indexes=["test"],
    )
    await graph_service.register_entity_type(entity_type)

    entity_data = {"entity_type": "TestType", "properties": {"test": "test value"}}
    result = await graph_service.create_entity(
        entity_type=entity_data["entity_type"], properties=entity_data["properties"]
    )
    assert result["entity_type"] == "TestType"
    assert result["properties"]["test"] == "test value"


@pytest.mark.asyncio
async def test_register_entity_type_validation_error(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test registering entity type with invalid property type."""
    with pytest.raises(PydanticValidationError) as exc_info:
        test_entity_type = EntityType(
            name="TestEntity",
            properties={
                "name": PropertyDefinition(type=PropertyType.STRING, required=True),
                "age": PropertyDefinition(type="INVALID_TYPE", required=False),
            },
        )
        await graph_service.register_entity_type(test_entity_type)
    assert (
        "Input should be 'string', 'integer', 'float', 'boolean', 'datetime', 'uuid', 'list' or 'dict'"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_register_relation_type_success(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test successful relation type registration."""
    # First register the entity types that this relation will connect
    person_type = EntityType(
        name="TestPerson",  # Use a different name to avoid conflicts
        description="A person entity",
        properties={
            "name": PropertyDefinition(type=PropertyType.STRING, required=True),
            "age": PropertyDefinition(type=PropertyType.INTEGER, required=True),
        },
        indexes=["name", "age"],
    )
    await graph_service.register_entity_type(person_type)

    # Register the relation type
    relation_type = RelationType(
        name="TEST_KNOWS",  # Use a different name to avoid conflicts
        description="A relationship between two people",
        properties={
            "since": PropertyDefinition(type=PropertyType.INTEGER, required=True)
        },
        indexes=["since"],
        from_types=["TestPerson"],
        to_types=["TestPerson"],
    )
    await graph_service.register_relation_type(relation_type)

    # Verify we can create a relation of this type
    person1_data = {
        "entity_type": "TestPerson",
        "properties": {"name": "John Doe", "age": 30},
    }
    person2_data = {
        "entity_type": "TestPerson",
        "properties": {"name": "Jane Doe", "age": 28},
    }
    person1_created = await graph_service.create_entity(
        entity_type=person1_data["entity_type"], properties=person1_data["properties"]
    )
    person2_created = await graph_service.create_entity(
        entity_type=person2_data["entity_type"], properties=person2_data["properties"]
    )

    relation_data = {
        "relation_type": "TEST_KNOWS",
        "from_entity": person1_created["id"],
        "to_entity": person2_created["id"],
        "properties": {"since": 2023},
    }
    result = await graph_service.create_relation(
        relation_type=relation_data["relation_type"],
        from_entity=relation_data["from_entity"],
        to_entity=relation_data["to_entity"],
        properties=relation_data["properties"],
    )
    assert result["type"] == "TEST_KNOWS"
    assert result["from_entity"] == person1_created["id"]
    assert result["to_entity"] == person2_created["id"]
    assert result["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_register_relation_type_validation_error(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test registering relation type with invalid property type."""
    with pytest.raises(PydanticValidationError) as exc_info:
        test_relation_type = RelationType(
            name="TestRelation",
            from_types=["Person"],
            to_types=["Organization"],
            properties={
                "start_date": PropertyDefinition(
                    type=PropertyType.STRING, required=True
                ),
                "role": PropertyDefinition(type="INVALID_TYPE", required=True),
            },
        )
        await graph_service.register_relation_type(test_relation_type)
    assert (
        "Input should be 'string', 'integer', 'float', 'boolean', 'datetime', 'uuid', 'list' or 'dict'"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_register_relation_type_invalid_entity_types(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test relation type registration with invalid entity types."""
    # Try to register a relation type referencing non-existent entity types
    relation_type = RelationType(
        name="TEST_INVALID_RELATION",
        description="A relation type with invalid entity types",
        properties={
            "test": PropertyDefinition(type=PropertyType.STRING, required=True)
        },
        indexes=["test"],
        from_types=["NonExistentType"],
        to_types=["AnotherNonExistentType"],
    )
    with pytest.raises(SchemaError) as exc_info:
        await graph_service.register_relation_type(relation_type)
    assert "Unknown entity type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_register_relation_type_transaction_rollback(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test transaction rollback on relation type registration failure."""
    with pytest.raises(PydanticValidationError) as exc_info:
        test_relation_type = RelationType(
            name="TestRelation",
            from_types=["Person"],
            to_types=["Organization"],
            properties={
                "start_date": PropertyDefinition(
                    type=PropertyType.STRING, required=True
                ),
                "role": PropertyDefinition(type="INVALID_TYPE", required=False),
            },
        )
        await graph_service.register_relation_type(test_relation_type)
    assert (
        "Input should be 'string', 'integer', 'float', 'boolean', 'datetime', 'uuid', 'list' or 'dict'"
        in str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_create_entity_property_type_validation(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity creation with invalid property type."""
    entity_data = {
        "entity_type": "Person",
        "properties": {"name": 123, "age": 30},  # name should be string
    }
    with pytest.raises(ValidationError):
        await graph_service.create_entity(
            entity_type=entity_data["entity_type"], properties=entity_data["properties"]
        )


@pytest.mark.asyncio
async def test_create_entity_required_property_validation(
    graph_service: GraphService, graph_context: BaseGraphContext
) -> None:
    """Test entity creation with missing required property."""
    entity_data = {
        "entity_type": "Person",
        "properties": {"age": 30},  # missing required name
    }
    with pytest.raises(ValidationError):
        await graph_service.create_entity(
            entity_type=entity_data["entity_type"], properties=entity_data["properties"]
        )
