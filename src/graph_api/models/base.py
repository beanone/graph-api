"""Base models for graph operations.

This module defines the base models used for graph operations,
including entity and relation management.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntityBase(BaseModel):
    """Base model for entity operations."""

    entity_type: str = Field(..., description="Type of the entity")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Entity properties"
    )


class EntityCreate(BaseModel):
    """Model for entity creation."""

    entity_type: str = Field(..., description="Type of the entity")
    properties: Dict = Field(default_factory=dict, description="Entity properties")


class EntityUpdate(BaseModel):
    """Model for entity updates."""

    properties: Dict = Field(..., description="Updated entity properties")


class EntityResponse(BaseModel):
    """Model for entity responses."""

    id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Type of the entity")
    properties: Dict = Field(..., description="Entity properties")


class RelationBase(BaseModel):
    """Base model for relation operations."""

    relation_type: str = Field(..., description="Type of the relation")
    from_entity: str = Field(..., description="Source entity ID")
    to_entity: str = Field(..., description="Target entity ID")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Relation properties"
    )


class RelationCreate(BaseModel):
    """Model for relation creation."""

    relation_type: str = Field(..., description="Type of the relation")
    from_entity: str = Field(..., description="Source entity ID")
    to_entity: str = Field(..., description="Target entity ID")
    properties: Dict = Field(default_factory=dict, description="Relation properties")


class RelationUpdate(BaseModel):
    """Model for relation updates."""

    properties: Dict = Field(..., description="Updated relation properties")


class RelationResponse(BaseModel):
    """Model for relation responses."""

    id: str = Field(..., description="Relation ID")
    relation_type: str = Field(..., description="Type of the relation")
    from_entity: str = Field(..., description="Source entity ID")
    to_entity: str = Field(..., description="Target entity ID")
    properties: Dict = Field(..., description="Relation properties")


class QueryCondition(BaseModel):
    """Model for query conditions."""

    relation_type: str = Field(..., description="Type of relation to query")
    from_entity: Optional[str] = Field(None, description="Source entity ID")
    to_entity: Optional[str] = Field(None, description="Target entity ID")
    direction: Optional[str] = Field(
        None, description="Direction of traversal (inbound/outbound)"
    )


class QueryRequest(BaseModel):
    """Model for graph query requests."""

    entity_type: str = Field(..., description="Type of entity to query")
    conditions: List[QueryCondition] = Field(..., description="Query conditions")


class TraversalRequest(BaseModel):
    """Model for graph traversal requests."""

    start_entity: str = Field(..., description="Starting entity ID")
    max_depth: int = Field(2, description="Maximum traversal depth")
    relation_types: Optional[list[str]] = Field(
        None, description="Types of relations to traverse"
    )
    direction: Optional[str] = Field(
        None, description="Direction of traversal (inbound/outbound)"
    )
