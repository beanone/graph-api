"""Base models for graph operations.

This module defines the base models used for graph operations,
including entity and relation management.
"""

from typing import Any, Dict, List, Optional

from graph_context.types import PropertyDefinition, PropertyType, RelationType

from pydantic import BaseModel, Field, RootModel


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


class EntityUpdate(RootModel):
    """Model for entity updates."""

    root: Dict[str, Any] = Field(..., description="Updated entity properties")

    def dict(self, *args, **kwargs):
        """Convert the model to a dictionary.

        Returns:
            dict: The model as a dictionary
        """
        return self.root


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


class RelationUpdate(RootModel):
    """Model for relation updates."""

    root: Dict[str, Any] = Field(..., description="Updated relation properties")

    def dict(self, *args, **kwargs):
        """Convert the model to a dictionary.

        Returns:
            dict: The model as a dictionary
        """
        return self.root


class RelationResponse(BaseModel):
    """Model for relation responses."""

    id: str = Field(..., description="Relation ID")
    type: str = Field(..., description="Type of the relation")
    from_entity: str = Field(..., description="Source entity ID")
    to_entity: str = Field(..., description="Target entity ID")
    properties: Dict = Field(..., description="Relation properties")

    def dict(self, *args, **kwargs):
        """Convert the model to a dictionary.

        Returns:
            dict: The model as a dictionary
        """
        d = super().dict(*args, **kwargs)
        d["relation_type"] = d.pop("type")
        return d


class QueryCondition(BaseModel):
    """Model for query conditions."""

    field: str = Field(..., description="Field to query on")
    operator: str = Field(..., description="Query operator")
    value: Any = Field(..., description="Query value")


class QuerySpec(BaseModel):
    """Model for query specification."""

    entity_type: str = Field(..., description="Type of entity to query")
    conditions: List[QueryCondition] = Field(
        default_factory=list, description="Query conditions"
    )


class QueryRequest(BaseModel):
    """Model for query requests."""

    query_spec: QuerySpec = Field(..., description="Query specification")
