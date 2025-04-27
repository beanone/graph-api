"""Unit tests for the GraphService class.

This module contains unit tests for the GraphService class, which provides
the core functionality for graph operations.
"""

from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import Request

from graph_api.models.base import (
    EntityCreate,
    EntityUpdate,
    RelationCreate,
    RelationUpdate,
)
from graph_api.services.graph_service import get_graph_service, GraphService
from graph_context import (
    BaseGraphContext,
    EntityNotFoundError,
    RelationNotFoundError,
    TransactionError,
    ValidationError,
)


@pytest_asyncio.fixture
async def mock_context() -> AsyncGenerator[BaseGraphContext, None]:
    """Create a mock graph context for testing.

    Yields:
        BaseGraphContext: A mock graph context instance.
    """
    context = AsyncMock(spec=BaseGraphContext)
    yield context


@pytest_asyncio.fixture
async def graph_service(mock_context: BaseGraphContext) -> GraphService:
    """Create a test graph service with mock context.

    Args:
        mock_context: The mock graph context fixture.

    Returns:
        GraphService: A configured graph service instance.
    """
    return GraphService(mock_context)


@pytest.mark.asyncio
async def test_create_entity_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful entity creation.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity = EntityCreate(
        entity_type="Person", properties={"name": "John Doe", "age": 30}
    )
    mock_context.create_entity.return_value = "entity-123"
    mock_context.get_entity.return_value = {
        "id": "entity-123",
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }

    # Act
    result = await graph_service.create_entity(entity)

    # Assert
    assert result["id"] == "entity-123"
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_create_entity_validation_error(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test entity creation with validation error.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity = EntityCreate(
        entity_type="Person",
        properties={"name": "John Doe", "age": "invalid"},  # Invalid age type
    )
    mock_context.create_entity.side_effect = ValidationError("Invalid age type")

    # Act & Assert
    with pytest.raises(ValidationError):
        await graph_service.create_entity(entity)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_get_entity_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful entity retrieval.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "entity-123"
    mock_context.get_entity.return_value = {
        "id": entity_id,
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 30},
    }

    # Act
    result = await graph_service.get_entity(entity_id)

    # Assert
    assert result["id"] == entity_id
    assert result["entity_type"] == "Person"
    assert result["properties"]["name"] == "John Doe"
    assert result["properties"]["age"] == 30


@pytest.mark.asyncio
async def test_get_entity_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test entity retrieval when entity doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "non-existent"
    mock_context.get_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.get_entity(entity_id)


@pytest.mark.asyncio
async def test_update_entity_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful entity update.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "entity-123"
    update = EntityUpdate(properties={"age": 31})
    mock_context.get_entity.return_value = {
        "id": entity_id,
        "entity_type": "Person",
        "properties": {"name": "John Doe", "age": 31},
    }

    # Act
    result = await graph_service.update_entity(entity_id, update)

    # Assert
    assert result["id"] == entity_id
    assert result["properties"]["age"] == 31
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_update_entity_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test entity update when entity doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "non-existent"
    update = EntityUpdate(properties={"age": 31})
    mock_context.update_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.update_entity(entity_id, update)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_delete_entity_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful entity deletion.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "entity-123"

    # Act
    await graph_service.delete_entity(entity_id)

    # Assert
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_delete_entity_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test entity deletion when entity doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    entity_id = "non-existent"
    mock_context.delete_entity.side_effect = EntityNotFoundError(
        f"Entity {entity_id} not found"
    )

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        await graph_service.delete_entity(entity_id)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_create_relation_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful relation creation.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation = RelationCreate(
        relation_type="KNOWS",
        from_entity="person-1",
        to_entity="person-2",
        properties={"since": 2023},
    )
    mock_context.create_relation.return_value = "relation-123"
    mock_context.get_relation.return_value = {
        "id": "relation-123",
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }

    # Act
    result = await graph_service.create_relation(relation)

    # Assert
    assert result["id"] == "relation-123"
    assert result["relation_type"] == "KNOWS"
    assert result["from_entity"] == "person-1"
    assert result["to_entity"] == "person-2"
    assert result["properties"]["since"] == 2023
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_create_relation_validation_error(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test relation creation with validation error.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation = RelationCreate(
        relation_type="KNOWS",
        from_entity="person-1",
        to_entity="person-2",
        properties={"since": "invalid"},  # Invalid since type
    )
    mock_context.create_relation.side_effect = ValidationError("Invalid since type")

    # Act & Assert
    with pytest.raises(ValidationError):
        await graph_service.create_relation(relation)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_get_relation_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful relation retrieval.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "relation-123"
    mock_context.get_relation.return_value = {
        "id": relation_id,
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2023},
    }

    # Act
    result = await graph_service.get_relation(relation_id)

    # Assert
    assert result["id"] == relation_id
    assert result["relation_type"] == "KNOWS"
    assert result["from_entity"] == "person-1"
    assert result["to_entity"] == "person-2"
    assert result["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_get_relation_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test relation retrieval when relation doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "non-existent"
    mock_context.get_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.get_relation(relation_id)


@pytest.mark.asyncio
async def test_update_relation_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful relation update.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "relation-123"
    update = RelationUpdate(properties={"since": 2024})
    mock_context.get_relation.return_value = {
        "id": relation_id,
        "relation_type": "KNOWS",
        "from_entity": "person-1",
        "to_entity": "person-2",
        "properties": {"since": 2024},
    }

    # Act
    result = await graph_service.update_relation(relation_id, update)

    # Assert
    assert result["id"] == relation_id
    assert result["properties"]["since"] == 2024
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_update_relation_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test relation update when relation doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "non-existent"
    update = RelationUpdate(properties={"since": 2024})
    mock_context.update_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.update_relation(relation_id, update)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_delete_relation_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful relation deletion.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "relation-123"

    # Act
    await graph_service.delete_relation(relation_id)

    # Assert
    mock_context.begin_transaction.assert_called_once()
    mock_context.commit_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_delete_relation_not_found(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test relation deletion when relation doesn't exist.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    relation_id = "non-existent"
    mock_context.delete_relation.side_effect = RelationNotFoundError(
        f"Relation {relation_id} not found"
    )

    # Act & Assert
    with pytest.raises(RelationNotFoundError):
        await graph_service.delete_relation(relation_id)
    mock_context.begin_transaction.assert_called_once()
    mock_context.rollback_transaction.assert_called_once()
    mock_context.commit_transaction.assert_not_called()


@pytest.mark.asyncio
async def test_query_success(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test successful query execution.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
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
    mock_context.query.return_value = [
        {
            "id": "relation-123",
            "relation_type": "KNOWS",
            "from_entity": "person-1",
            "to_entity": "person-2",
            "properties": {"since": 2023},
        }
    ]

    # Act
    result = await graph_service.query(query_spec)

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == "relation-123"
    assert result[0]["relation_type"] == "KNOWS"
    assert result[0]["from_entity"] == "person-1"
    assert result[0]["to_entity"] == "person-2"
    assert result[0]["properties"]["since"] == 2023


@pytest.mark.asyncio
async def test_query_validation_error(
    graph_service: GraphService, mock_context: BaseGraphContext
) -> None:
    """Test query execution with validation error.

    Args:
        graph_service: The graph service fixture.
        mock_context: The mock context fixture.
    """
    # Arrange
    query_spec = {
        "entity_type": "Person",
        "conditions": [
            {
                "relation_type": "INVALID",  # Invalid relation type
                "from_entity": "person-1",
                "direction": "outbound",
            }
        ],
    }
    mock_context.query.side_effect = ValidationError("Invalid relation type")

    # Act & Assert
    with pytest.raises(ValidationError):
        await graph_service.query(query_spec)


@pytest.mark.asyncio
async def test_get_graph_service() -> None:
    """Test getting graph service from request state."""
    # Arrange
    mock_context = AsyncMock(spec=BaseGraphContext)
    mock_request = MagicMock(spec=Request)
    mock_request.app.state.graph_context = mock_context

    # Act
    service = await get_graph_service(mock_request)

    # Assert
    assert isinstance(service, GraphService)
    assert service._context == mock_context
