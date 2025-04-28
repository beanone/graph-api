"""API router for graph operations.

This module defines the FastAPI router for graph operations,
including entity and relation management.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
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
    error = {"message": str(e)}
    if hasattr(e, "field"):
        error["field"] = e.field
    if hasattr(e, "constraint"):
        error["constraint"] = e.constraint
    raise HTTPException(status_code=400, detail=error)


def handle_schema_error(e: SchemaError) -> HTTPException:
    """Handle schema errors.

    Args:
        e: The schema error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(status_code=400, detail={"message": str(e)})


def handle_not_found_error(e: Exception) -> HTTPException:
    """Handle not found errors.

    Args:
        e: The not found error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(status_code=404, detail={"message": str(e)})


def handle_transaction_error(e: TransactionError) -> HTTPException:
    """Handle transaction errors.

    Args:
        e: The transaction error

    Returns:
        HTTPException: The HTTP exception to raise
    """
    return HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Create a new entity.

    Args:
        entity: The entity to create
        service: The graph service

    Returns:
        dict: The created entity with id, entity_type, and properties
    """
    try:
        return await service.create_entity(
            entity_type=entity.entity_type, properties=entity.properties
        )
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
    entity_update: EntityUpdate,
    graph_service: GraphService = Depends(get_graph_service),
) -> EntityResponse:
    """Update an entity.

    Args:
        entity_id: ID of the entity to update
        entity_update: Updated entity properties
        graph_service: Graph service instance

    Returns:
        EntityResponse: Updated entity
    """
    try:
        entity = await graph_service.update_entity(entity_id, entity_update.dict())
        return entity
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)})
    except TransactionError as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


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
        await service.delete_entity(entity_id)
        return {"message": f"Entity {entity_id} deleted successfully"}
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
        dict: The created relation with id, relation_type, from_entity, to_entity, and properties
    """
    try:
        return await service.create_relation(
            relation_type=relation.relation_type,
            from_entity=relation.from_entity,
            to_entity=relation.to_entity,
            properties=relation.properties,
        )
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
    relation_update: RelationUpdate,
    graph_service: GraphService = Depends(get_graph_service),
) -> RelationResponse:
    """Update a relation.

    Args:
        relation_id: ID of the relation to update
        relation_update: Updated relation properties
        graph_service: Graph service instance

    Returns:
        RelationResponse: Updated relation
    """
    try:
        relation = await graph_service.update_relation(
            relation_id, relation_update.dict()
        )
        return relation
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})
    except RelationNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)})
    except TransactionError as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


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
        await service.delete_relation(relation_id)
        return {"message": f"Relation {relation_id} deleted successfully"}
    except RelationNotFoundError as e:
        raise handle_not_found_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.post("/query", response_model=List[EntityResponse])
async def query_entities(
    query_request: QueryRequest,
    graph_service: GraphService = Depends(get_graph_service),
) -> List[EntityResponse]:
    """Query entities.

    Args:
        query_request: Query request
        graph_service: Graph service instance

    Returns:
        List[EntityResponse]: List of entities matching the query
    """
    try:
        entities = await graph_service.query(query_request.query_spec)
        return entities
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})
    except SchemaError as e:
        raise HTTPException(status_code=400, detail={"message": str(e)})
    except TransactionError as e:
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/entity-types")
async def register_entity_type(
    request: Request, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Register a new entity type.

    Args:
        request: The request
        service: The graph service

    Returns:
        dict: The registration status
    """
    try:
        data = await request.json()
        entity_type = EntityType(**data)
        await service.register_entity_type(entity_type)
        return {"message": f"Entity type {entity_type.name} registered successfully"}
    except ValidationError as e:
        raise handle_validation_error(e)
    except SchemaError as e:
        raise handle_schema_error(e)
    except TransactionError as e:
        raise handle_transaction_error(e)
    except Exception as e:
        raise handle_validation_error(ValidationError(str(e)))


@router.post("/relation-types")
async def register_relation_type(
    request: Request, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Register a new relation type.

    Args:
        request: The request
        service: The graph service

    Returns:
        dict: The registration status
    """
    try:
        data = await request.json()
        relation_type = RelationType(**data)
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
    except Exception as e:
        raise handle_validation_error(ValidationError(str(e)))


@router.get("/entity-types/{entity_type}")
async def has_entity_type(
    entity_type: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Check if an entity type exists.

    Args:
        entity_type: The entity type name to check
        service: The graph service

    Returns:
        dict: The existence status
    """
    try:
        exists = await service.has_entity_type(entity_type)
        if not exists:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Entity type {entity_type} not found"},
            )
        return {"message": f"Entity type {entity_type} exists"}
    except TransactionError as e:
        raise handle_transaction_error(e)


@router.get("/relation-types/{relation_type}")
async def has_relation_type(
    relation_type: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Check if a relation type exists.

    Args:
        relation_type: The relation type name to check
        service: The graph service

    Returns:
        dict: The existence status
    """
    try:
        exists = await service.has_relation_type(relation_type)
        if not exists:
            raise HTTPException(
                status_code=404,
                detail={"message": f"Relation type {relation_type} not found"},
            )
        return {"message": f"Relation type {relation_type} exists"}
    except TransactionError as e:
        raise handle_transaction_error(e)
