"""API router for graph operations.

This module defines the FastAPI router for graph operations,
including entity and relation management.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from graph_context.exceptions import (
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
    RelationType,
)

from ..models.base import (
    EntityCreate,
    EntityResponse,
    EntityUpdate,
    QueryRequest,
    RelationCreate,
    RelationResponse,
    RelationUpdate,
)
from ..services.graph_service import get_graph_service, GraphService

# Configure logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/api/v1")


def handle_validation_error(e: ValidationError) -> HTTPException:
    """Handle validation errors.

    Args:
        e: The validation error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(
        status_code=400,
        detail={
            "message": str(e),
            "field": e.field,
            "constraint": e.constraint,
        },
    )


def handle_schema_error(e: SchemaError) -> HTTPException:
    """Handle schema errors.

    Args:
        e: The schema error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    print("--------------------------------")
    print("Schema error: ", e)
    print("--------------------------------")
    return HTTPException(
        status_code=400,
        detail={
            "message": str(e),
        },
    )


def handle_not_found_error(e: Exception) -> HTTPException:
    """Handle not found errors.

    Args:
        e: The not found error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(status_code=404, detail=str(e))


def handle_transaction_error(e: TransactionError) -> HTTPException:
    """Handle transaction errors.

    Args:
        e: The transaction error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(status_code=500, detail=str(e))


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Create a new entity.

    Args:
        entity: The entity to create
        service: The graph service

    Returns:
        dict: The created entity
    """
    try:
        return await service.create_entity(entity)
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get an entity by ID.

    Args:
        entity_id: The entity ID
        service: The graph service

    Returns:
        dict: The entity
    """
    try:
        return await service.get_entity(entity_id)
    except EntityNotFoundError as e:
        raise handle_not_found_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.put("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    entity: EntityUpdate,
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Update an entity.

    Args:
        entity_id: The entity ID
        entity: The entity update
        service: The graph service

    Returns:
        dict: The updated entity
    """
    try:
        return await service.update_entity(entity_id, entity)
    except EntityNotFoundError as e:
        raise handle_not_found_error(e)
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Delete an entity.

    Args:
        entity_id: The entity ID
        service: The graph service

    Returns:
        dict: The deletion status
    """
    try:
        return await service.delete_entity(entity_id)
    except EntityNotFoundError as e:
        raise handle_not_found_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.post("/relations", response_model=RelationResponse)
async def create_relation(
    relation: RelationCreate, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Create a new relation.

    Args:
        relation: The relation to create
        service: The graph service

    Returns:
        dict: The created relation
    """
    try:
        return await service.create_relation(relation)
    except EntityNotFoundError as e:
        raise handle_not_found_error(e)
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.get("/relations/{relation_id}", response_model=RelationResponse)
async def get_relation(
    relation_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get a relation by ID.

    Args:
        relation_id: The relation ID
        service: The graph service

    Returns:
        dict: The relation
    """
    try:
        return await service.get_relation(relation_id)
    except RelationNotFoundError as e:
        raise handle_not_found_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.put("/relations/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: str,
    relation: RelationUpdate,
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Update a relation.

    Args:
        relation_id: The relation ID
        relation: The relation update
        service: The graph service

    Returns:
        dict: The updated relation
    """
    try:
        return await service.update_relation(relation_id, relation)
    except RelationNotFoundError as e:
        raise handle_not_found_error(e)
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Delete a relation.

    Args:
        relation_id: The relation ID
        service: The graph service

    Returns:
        dict: The deletion status
    """
    try:
        return await service.delete_relation(relation_id)
    except RelationNotFoundError as e:
        raise handle_not_found_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.post("/query", response_model=List[RelationResponse])
async def query_relations(
    query: QueryRequest, service: GraphService = Depends(get_graph_service)
) -> List[Dict[str, Any]]:
    """Query relations.

    Args:
        query: The query request
        service: The graph service

    Returns:
        list: The matching relations
    """
    try:
        return await service.query_relations(query)
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.post("/entity-types")
async def register_entity_type(
    entity_type: EntityType, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Register a new entity type.

    Args:
        entity_type: The entity type definition to register
        service: The graph service

    Returns:
        dict: Success message
    """
    try:
        await service.register_entity_type(entity_type)
        return {"message": f"Entity type {entity_type.name} registered successfully"}
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.post("/relation-types")
async def register_relation_type(
    relation_type: RelationType, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Register a new relation type.

    Args:
        relation_type: The relation type definition to register
        service: The graph service

    Returns:
        dict: Success message
    """
    try:
        await service.register_relation_type(relation_type)
        return {
            "message": f"Relation type {relation_type.name} registered successfully"
        }
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)
