"""Integration tests for the graph context system."""

import pytest

from graph_context.context_base import BaseGraphContext
from graph_context.types.type_base import EntityType, PropertyDefinition, RelationType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_wrapping_for_entity_creation():
    """Test proper transaction wrapping for entity creation and related operations."""
    # Create a fresh context for this test
    context = BaseGraphContext()

    try:
        # Define test data
        person_type = "Person"
        company_type = "Company"
        person_props = {"name": "John Doe", "age": 30}
        company_props = {"name": "Acme Corp", "industry": "Technology"}
        relation_type = "WORKS_AT"
        relation_props = {"start_date": "2023-01-01", "role": "Engineer"}

        # Register entity types
        person_entity_type = EntityType(
            name=person_type,
            properties={
                "name": PropertyDefinition(type="string", required=True),
                "age": PropertyDefinition(type="integer", required=True),
            },
        )
        company_entity_type = EntityType(
            name=company_type,
            properties={
                "name": PropertyDefinition(type="string", required=True),
                "industry": PropertyDefinition(type="string", required=True),
            },
        )
        await context.register_entity_type(person_entity_type)
        await context.register_entity_type(company_entity_type)

        # Register relation type
        works_at_relation_type = RelationType(
            name=relation_type,
            from_types=[person_type],
            to_types=[company_type],
            properties={
                "start_date": PropertyDefinition(type="string", required=True),
                "role": PropertyDefinition(type="string", required=True),
            },
        )
        await context.register_relation_type(works_at_relation_type)

        try:
            # Start transaction
            await context.begin_transaction()

            # Create person entity
            person_id = await context.create_entity(person_type, person_props)
            assert person_id is not None

            # Create company entity
            company_id = await context.create_entity(company_type, company_props)
            assert company_id is not None

            # Create relation between person and company
            relation_id = await context.create_relation(
                relation_type, person_id, company_id, relation_props
            )
            assert relation_id is not None

            # Verify entities and relation exist within transaction
            person = await context.get_entity(person_id)
            assert person is not None
            assert person.type == person_type
            assert person.properties == person_props

            company = await context.get_entity(company_id)
            assert company is not None
            assert company.type == company_type
            assert company.properties == company_props

            relation = await context.get_relation(relation_id)
            assert relation is not None
            assert relation.type == relation_type
            assert relation.from_entity == person_id
            assert relation.to_entity == company_id
            assert relation.properties == relation_props

            # Commit transaction
            await context.commit_transaction()

            # Verify entities and relation still exist after commit
            person = await context.get_entity(person_id)
            assert person is not None
            company = await context.get_entity(company_id)
            assert company is not None
            relation = await context.get_relation(relation_id)
            assert relation is not None

        except Exception as e:
            # Rollback transaction on error
            await context.rollback_transaction()
            raise e

        # Test rollback behavior
        try:
            await context.begin_transaction()

            # Create an entity
            entity_id = await context.create_entity(person_type, person_props)
            assert entity_id is not None

            # Simulate an error condition
            raise ValueError("Simulated error")

        except ValueError:
            # Rollback should undo the entity creation
            await context.rollback_transaction()

            # Verify entity doesn't exist after rollback
            entity = await context.get_entity(entity_id)
            assert entity is None

    finally:
        # Clean up the context
        await context.cleanup()
