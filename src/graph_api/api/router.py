"""API router for graph operations.

This module defines the FastAPI router for graph operations,
including entity and relation management.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from graph_context.exceptions import (
    EntityNotFoundError,
    RelationNotFoundError,
    SchemaError,
    TransactionError,
    ValidationError,
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

router = APIRouter(prefix="/api/v1")


@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity: EntityCreate, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Create a new entity.

    Args:
        entity: Entity creation model with type and properties
        service: Graph service instance

    Returns:
        Dict[str, Any]: Created entity data

    Raises:
        HTTPException: If entity creation fails
    """
    try:
        result = await service.create_entity(entity)
        return {"id": result["id"], **result}
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "field": getattr(e, "field", None),
                "constraint": getattr(e, "constraint", None),
            },
        )
    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "schema_type": getattr(e, "schema_type", None),
            },
        )
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get an entity by ID.

    Args:
        entity_id: ID of the entity to retrieve
        service: Graph service instance

    Returns:
        Dict[str, Any]: Entity data

    Raises:
        HTTPException: If entity doesn't exist
    """
    try:
        result = await service.get_entity(entity_id)
        return {"id": entity_id, **result}
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")


@router.put("/entities/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    entity: EntityUpdate,
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Update an entity.

    Args:
        entity_id: ID of the entity to update
        entity: Entity update model with properties
        service: Graph service instance

    Returns:
        Dict[str, Any]: Updated entity data

    Raises:
        HTTPException: If entity update fails
    """
    try:
        result = await service.update_entity(entity_id, entity)
        return {"id": entity_id, **result}
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "field": getattr(e, "field", None),
                "constraint": getattr(e, "constraint", None),
            },
        )
    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "schema_type": getattr(e, "schema_type", None),
            },
        )
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Delete an entity.

    Args:
        entity_id: ID of the entity to delete
        service: Graph service instance

    Returns:
        Dict[str, Any]: Success message

    Raises:
        HTTPException: If entity deletion fails
    """
    try:
        await service.delete_entity(entity_id)
        return {"message": "Entity deleted successfully"}
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relations", response_model=RelationResponse)
async def create_relation(
    relation: RelationCreate, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Create a new relation.

    Args:
        relation: Relation creation model with type and properties
        service: Graph service instance

    Returns:
        Dict[str, Any]: Created relation data

    Raises:
        HTTPException: If relation creation fails
    """
    try:
        result = await service.create_relation(relation)
        return {"id": result["id"], **result}
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "field": getattr(e, "field", None),
                "constraint": getattr(e, "constraint", None),
            },
        )
    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "schema_type": getattr(e, "schema_type", None),
            },
        )
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relations/{relation_id}", response_model=RelationResponse)
async def get_relation(
    relation_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get a relation by ID.

    Args:
        relation_id: ID of the relation to retrieve
        service: Graph service instance

    Returns:
        Dict[str, Any]: Relation data

    Raises:
        HTTPException: If relation doesn't exist
    """
    try:
        result = await service.get_relation(relation_id)
        return {"id": relation_id, **result}
    except RelationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Relation {relation_id} not found")


@router.put("/relations/{relation_id}", response_model=RelationResponse)
async def update_relation(
    relation_id: str,
    relation: RelationUpdate,
    service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Update a relation.

    Args:
        relation_id: ID of the relation to update
        relation: Relation update model with properties
        service: Graph service instance

    Returns:
        Dict[str, Any]: Updated relation data

    Raises:
        HTTPException: If relation update fails
    """
    try:
        result = await service.update_relation(relation_id, relation)
        return {"id": relation_id, **result}
    except RelationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Relation {relation_id} not found")
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "field": getattr(e, "field", None),
                "constraint": getattr(e, "constraint", None),
            },
        )
    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "schema_type": getattr(e, "schema_type", None),
            },
        )
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: str, service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Delete a relation.

    Args:
        relation_id: ID of the relation to delete
        service: Graph service instance

    Returns:
        Dict[str, Any]: Success message

    Raises:
        HTTPException: If relation deletion fails
    """
    try:
        await service.delete_relation(relation_id)
        return {"message": "Relation deleted successfully"}
    except RelationNotFoundError:
        raise HTTPException(status_code=404, detail=f"Relation {relation_id} not found")
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_relations(
    query: QueryRequest, service: GraphService = Depends(get_graph_service)
) -> List[Dict[str, Any]]:
    """Query relations based on specified conditions.

    Args:
        query: Query request model with conditions
        service: Graph service instance

    Returns:
        List[Dict[str, Any]]: List of matching relations

    Raises:
        HTTPException: If query execution fails
    """
    try:
        return await service.query_relations(query)
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "field": getattr(e, "field", None),
                "constraint": getattr(e, "constraint", None),
            },
        )
    except SchemaError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(e),
                "schema_type": getattr(e, "schema_type", None),
            },
        )
    except TransactionError as e:
        raise HTTPException(status_code=500, detail=str(e))
