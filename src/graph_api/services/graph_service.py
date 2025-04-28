"""Graph service implementation using graph-context library.

This module provides the core service layer for graph operations,
handling business logic and orchestration.
"""

from typing import Any, Dict, List

from fastapi import Request

from graph_context import (
    EntityNotFoundError,
    GraphContext,
    RelationNotFoundError,
    SchemaError,
    TransactionError,
    ValidationError,
)
from graph_context.types import (
    EntityType,
    PropertyDefinition,
    PropertyType,
    QuerySpec,
    RelationType,
)


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

    async def register_entity_type(self, entity_type: EntityType) -> None:
        """Register a new entity type.

        Args:
            entity_type: The entity type definition to register. Properties should be defined using PropertyDefinition
                        with proper PropertyType values.

        Raises:
            ValidationError: If entity type definition is invalid
            TransactionError: If transaction management fails
        """
        try:
            # Validate that properties are using PropertyDefinition with proper PropertyType

            for prop_name, prop_def in entity_type.properties.items():
                if not isinstance(prop_def, PropertyDefinition):
                    raise ValidationError(
                        f"Property {prop_name} must be defined using PropertyDefinition"
                    )
                if not isinstance(prop_def.type, PropertyType):
                    raise ValidationError(
                        f"Property {prop_name} type must be a PropertyType enum value"
                    )
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.register_entity_type(entity_type)
                await self._context.commit_transaction()
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except ValidationError:
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def register_relation_type(self, relation_type: RelationType) -> None:
        """Register a new relation type.

        Args:
            relation_type: The relation type definition to register. Properties should be defined using PropertyDefinition
                         with proper PropertyType values.

        Raises:
            ValidationError: If relation type definition is invalid
            SchemaError: If referenced entity types don't exist
            TransactionError: If transaction management fails
        """
        try:
            # Validate that properties are using PropertyDefinition with proper PropertyType

            for prop_name, prop_def in relation_type.properties.items():
                if not isinstance(prop_def, PropertyDefinition):
                    raise ValidationError(
                        f"Property {prop_name} must be defined using PropertyDefinition"
                    )
                if not isinstance(prop_def.type, PropertyType):
                    raise ValidationError(
                        f"Property {prop_name} type must be a PropertyType enum value"
                    )
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.register_relation_type(relation_type)
                await self._context.commit_transaction()
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except (ValidationError, SchemaError):
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def create_entity(
        self, entity_type: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new entity.

        Args:
            entity_type: Type of the entity to create
            properties: Entity properties

        Returns:
            Dict[str, Any]: Created entity data

        Raises:
            ValidationError: If entity data is invalid
            TransactionError: If transaction management fails
        """
        try:
            # Start transaction

            await self._context.begin_transaction()
            try:
                entity_id = await self._context.create_entity(
                    entity_type=entity_type, properties=properties
                )
                entity = await self._context.get_entity(entity_id)
                await self._context.commit_transaction()
                return {
                    "id": entity_id,
                    "entity_type": entity.type,
                    "properties": entity.properties,
                }
            except Exception as e:
                await self._context.rollback_transaction()
                raise e
        except ValidationError:
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get an entity by ID.

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            Dict[str, Any]: Entity data

        Raises:
            EntityNotFoundError: If entity doesn't exist
        """
        try:
            entity = await self._context.get_entity(entity_id)
            return {
                "id": entity_id,
                "entity_type": entity.type,
                "properties": entity.properties,
            }
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise EntityNotFoundError(f"Entity {entity_id} not found: {str(e)}")

    async def update_entity(
        self, entity_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing entity.

        Args:
            entity_id: ID of the entity to update
            properties: Updated entity properties

        Returns:
            Dict[str, Any]: Updated entity data

        Raises:
            EntityNotFoundError: If entity doesn't exist
            ValidationError: If update data is invalid
            TransactionError: If transaction management fails
        """
        try:
            # Check if entity exists first

            try:
                await self._context.get_entity(entity_id)
            except EntityNotFoundError:
                raise EntityNotFoundError(f"Entity {entity_id} not found")
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.update_entity(entity_id, properties=properties)
                entity = await self._context.get_entity(entity_id)
                await self._context.commit_transaction()
                return {
                    "id": entity_id,
                    "entity_type": entity.type,
                    "properties": entity.properties,
                }
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except (EntityNotFoundError, ValidationError):
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def delete_entity(self, entity_id: str) -> None:
        """Delete an entity.

        Args:
            entity_id: ID of the entity to delete

        Raises:
            EntityNotFoundError: If entity doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            # Check if entity exists first

            try:
                entity = await self._context.get_entity(entity_id)
                if not entity:
                    raise EntityNotFoundError(f"Entity {entity_id} not found")
            except EntityNotFoundError:
                raise EntityNotFoundError(f"Entity {entity_id} not found")
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.delete_entity(entity_id)
                await self._context.commit_transaction()
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except EntityNotFoundError:
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def create_relation(
        self,
        relation_type: str,
        from_entity: str,
        to_entity: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a new relation.

        Args:
            relation_type: Type of the relation to create
            from_entity: Source entity ID
            to_entity: Target entity ID
            properties: Relation properties

        Returns:
            Dict[str, Any]: Created relation data

        Raises:
            ValidationError: If relation data is invalid
            EntityNotFoundError: If source or target entity doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            # Start transaction

            await self._context.begin_transaction()
            try:
                relation_id = await self._context.create_relation(
                    relation_type=relation_type,
                    from_entity=from_entity,
                    to_entity=to_entity,
                    properties=properties,
                )
                relation = await self._context.get_relation(relation_id)
                await self._context.commit_transaction()
                return {
                    "id": relation_id,
                    "type": relation.type,
                    "from_entity": relation.from_entity,
                    "to_entity": relation.to_entity,
                    "properties": relation.properties,
                }
            except Exception as e:
                await self._context.rollback_transaction()
                raise e
        except (ValidationError, EntityNotFoundError):
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def get_relation(self, relation_id: str) -> Dict[str, Any]:
        """Get a relation by ID.

        Args:
            relation_id: ID of the relation to retrieve

        Returns:
            Dict[str, Any]: Relation data

        Raises:
            RelationNotFoundError: If relation doesn't exist
        """
        try:
            relation = await self._context.get_relation(relation_id)
            return {
                "id": relation_id,
                "type": relation.type,
                "from_entity": relation.from_entity,
                "to_entity": relation.to_entity,
                "properties": relation.properties,
            }
        except RelationNotFoundError:
            raise
        except Exception as e:
            raise RelationNotFoundError(f"Relation {relation_id} not found: {str(e)}")

    async def update_relation(
        self, relation_id: str, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing relation.

        Args:
            relation_id: ID of the relation to update
            properties: Updated relation properties

        Returns:
            Dict[str, Any]: Updated relation data

        Raises:
            RelationNotFoundError: If relation doesn't exist
            ValidationError: If update data is invalid
            TransactionError: If transaction management fails
        """
        try:
            # Check if relation exists first

            try:
                relation = await self._context.get_relation(relation_id)
                if not relation:
                    raise RelationNotFoundError(f"Relation {relation_id} not found")
            except RelationNotFoundError:
                raise RelationNotFoundError(f"Relation {relation_id} not found")
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.update_relation(relation_id, properties=properties)
                relation = await self._context.get_relation(relation_id)
                await self._context.commit_transaction()
                return {
                    "id": relation_id,
                    "type": relation.type,
                    "from_entity": relation.from_entity,
                    "to_entity": relation.to_entity,
                    "properties": relation.properties,
                }
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except (RelationNotFoundError, ValidationError):
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def delete_relation(self, relation_id: str) -> None:
        """Delete a relation.

        Args:
            relation_id: ID of the relation to delete

        Raises:
            RelationNotFoundError: If relation doesn't exist
            TransactionError: If transaction management fails
        """
        try:
            # Check if relation exists first

            try:
                relation = await self._context.get_relation(relation_id)
                if not relation:
                    raise RelationNotFoundError(f"Relation {relation_id} not found")
            except RelationNotFoundError:
                raise RelationNotFoundError(f"Relation {relation_id} not found")
            # Start transaction

            await self._context.begin_transaction()
            try:
                await self._context.delete_relation(relation_id)
                await self._context.commit_transaction()
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except RelationNotFoundError:
            raise
        except Exception as e:
            raise TransactionError(str(e))

    async def query(self, query_spec: QuerySpec) -> List[Dict[str, Any]]:
        """Query entities based on the provided query specification.

        Args:
            query_spec: The query specification containing entity type, conditions, and optional limit/offset.

        Returns:
            A list of dictionaries containing the matching entities.

        Raises:
            ValidationError: If query specification is invalid
            EntityNotFoundError: If entity type does not exist
        """
        try:
            # Convert QuerySpec to dict for the store

            query_dict = query_spec.model_dump()

            # Convert conditions to dicts as well

            if query_dict.get("conditions"):
                query_dict["conditions"] = [
                    cond.model_dump() for cond in query_spec.conditions
                ]
            try:
                results = await self._context.query(query_dict)
                return [
                    {
                        "id": result.id,
                        "entity_type": result.type,
                        "properties": result.properties,
                    }
                    for result in results
                ]
            except Exception as e:
                if self._context._transaction._in_transaction:
                    await self._context.rollback_transaction()
                raise e
        except (ValidationError, EntityNotFoundError) as ee:
            raise
        except Exception as e:
            raise ValidationError(f"Invalid query specification: {str(e)}")


async def get_graph_service(request: Request) -> GraphService:
    """Get a graph service instance from the request's app state.

    Args:
        request: The FastAPI request object

    Returns:
        GraphService: An instance of the graph service
    """
    context = request.app.state.graph_context
    return GraphService(context)
