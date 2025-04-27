"""Graph service implementation using graph-context library.

This module provides the core service layer for graph operations,
handling business logic and orchestration.
"""

from typing import Any, Dict, List, Optional

from fastapi import Request

from graph_context import (
    EntityNotFoundError,
    GraphContext,
    RelationNotFoundError,
    TransactionError,
    ValidationError,
)

from ..models.base import EntityCreate, EntityUpdate, RelationCreate, RelationUpdate


class GraphService:
    """Service class for graph operations.

    This class provides business logic and orchestration for graph operations,
    including validation, error handling, and transaction management.
    """

    def __init__(self, context: GraphContext):
        """Initialize the graph service.

        Args:
            context: GraphContext instance to use for operations
        """
        self._context = context

    async def create_entity(self, entity: EntityCreate) -> Dict[str, Any]:
        """Create a new entity.

        Args:
            entity: Entity creation model with type and properties

        Returns:
            Dict[str, Any]: Created entity data

        Raises:
            ValidationError: If entity data is invalid
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            entity_id = await self._context.create_entity(
                entity_type=entity.entity_type, properties=entity.properties
            )
            await self._context.commit_transaction()
            return await self._context.get_entity(entity_id)
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get an entity by ID.

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            Dict[str, Any]: Entity data

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        return await self._context.get_entity(entity_id)

    async def update_entity(
        self, entity_id: str, entity: EntityUpdate
    ) -> Dict[str, Any]:
        """Update an existing entity.

        Args:
            entity_id: ID of the entity to update
            entity: Entity update model with properties

        Returns:
            Dict[str, Any]: Updated entity data

        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If update data is invalid
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            await self._context.update_entity(entity_id, properties=entity.properties)
            await self._context.commit_transaction()
            return await self._context.get_entity(entity_id)
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def delete_entity(self, entity_id: str) -> None:
        """Delete an entity.

        Args:
            entity_id: ID of the entity to delete

        Raises:
            EntityNotFoundError: If entity doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            await self._context.delete_entity(entity_id)
            await self._context.commit_transaction()
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def create_relation(self, relation: RelationCreate) -> Dict[str, Any]:
        """Create a new relation.

        Args:
            relation: Relation creation model with type and properties

        Returns:
            Dict[str, Any]: Created relation data

        Raises:
            ValidationError: If relation data is invalid
            EntityNotFoundError: If source or target entity doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            relation_id = await self._context.create_relation(
                relation_type=relation.relation_type,
                from_entity=relation.from_entity,
                to_entity=relation.to_entity,
                properties=relation.properties,
            )
            await self._context.commit_transaction()
            return await self._context.get_relation(relation_id)
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def get_relation(self, relation_id: str) -> Dict[str, Any]:
        """Get a relation by ID.

        Args:
            relation_id: ID of the relation to retrieve

        Returns:
            Dict[str, Any]: Relation data

        Raises:
            RelationNotFoundError: If relation doesn't exist
        """
        return await self._context.get_relation(relation_id)

    async def update_relation(
        self, relation_id: str, relation: RelationUpdate
    ) -> Dict[str, Any]:
        """Update an existing relation.

        Args:
            relation_id: ID of the relation to update
            relation: Relation update model with properties

        Returns:
            Dict[str, Any]: Updated relation data

        Raises:
            RelationNotFoundError: If relation doesn't exist
            ValidationError: If update data is invalid
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            await self._context.update_relation(
                relation_id, properties=relation.properties
            )
            await self._context.commit_transaction()
            return await self._context.get_relation(relation_id)
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def delete_relation(self, relation_id: str) -> None:
        """Delete a relation.

        Args:
            relation_id: ID of the relation to delete

        Raises:
            RelationNotFoundError: If relation doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            await self._context.begin_transaction()
            await self._context.delete_relation(relation_id)
            await self._context.commit_transaction()
        except Exception as e:
            await self._context.rollback_transaction()
            raise e

    async def query(self, query_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query relations based on the provided specification.

        Args:
            query_spec: Query specification with entity_type and conditions

        Returns:
            List[Dict[str, Any]]: List of matching relations

        Raises:
            EntityNotFoundError: If referenced entities don't exist
            ValidationError: If query specification is invalid
        """
        return await self._context.query(query_spec)


async def get_graph_service(request: Request) -> GraphService:
    """Get a graph service instance from the request's app state.

    Args:
        request: The FastAPI request object

    Returns:
        GraphService: An instance of the graph service
    """
    context = request.app.state.graph_context
    return GraphService(context)
