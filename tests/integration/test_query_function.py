import pytest

from graph_context.context_base import BaseGraphContext
from graph_context.types.type_base import EntityType, PropertyDefinition, RelationType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_operations():
    """Test query operations with multiple conditions."""
    # Create a fresh context for this test
    context = BaseGraphContext()

    try:
        # Register entity type
        person_type = "Person"
        person_entity_type = EntityType(
            name=person_type,
            properties={
                "name": PropertyDefinition(type="string", required=True),
                "age": PropertyDefinition(type="integer", required=True),
            },
        )
        await context.register_entity_type(person_entity_type)

        # Register relation type
        knows_type = "KNOWS"
        knows_relation_type = RelationType(
            name=knows_type,
            from_types=[person_type],
            to_types=[person_type],
            properties={
                "since": PropertyDefinition(type="integer", required=True),
            },
        )
        await context.register_relation_type(knows_relation_type)

        # Create entities and relation in a transaction
        await context.begin_transaction()
        try:
            # Create first person
            person1_id = await context.create_entity(
                person_type, {"name": "John Doe", "age": 30}
            )

            # Create second person
            person2_id = await context.create_entity(
                person_type, {"name": "Jane Doe", "age": 28}
            )

            # Create relation
            await context.create_relation(
                knows_type, person1_id, person2_id, {"since": 2023}
            )
            await context.commit_transaction()
        except Exception:
            await context.rollback_transaction()
            raise

        # Test single condition query
        query_spec = {
            "type": person_type,
            "conditions": [{"field": "name", "operator": "eq", "value": "John Doe"}],
        }
        results = await context.query(query_spec)
        assert len(results) == 1
        assert results[0].id == person1_id
        assert results[0].type == person_type
        assert results[0].properties["name"] == "John Doe"
        assert results[0].properties["age"] == 30

        # Test multiple conditions
        query_spec = {
            "type": person_type,
            "conditions": [
                {"field": "name", "operator": "eq", "value": "John Doe"},
                {"field": "age", "operator": "gt", "value": 25},
            ],
        }
        results = await context.query(query_spec)
        assert len(results) == 1
        assert results[0].id == person1_id

        # Test no results query
        query_spec = {
            "type": person_type,
            "conditions": [{"field": "name", "operator": "eq", "value": "Bob Smith"}],
        }
        results = await context.query(query_spec)
        assert len(results) == 0

    finally:
        # Clean up the context
        await context.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_with_multiple_conditions():
    """Test query with multiple conditions."""
    # Create a fresh context for this test
    context = BaseGraphContext()

    try:
        # Register entity type
        await context.register_entity_type(
            EntityType(
                name="Person",
                properties={
                    "name": PropertyDefinition(type="string", required=True),
                    "age": PropertyDefinition(type="integer", required=True),
                    "city": PropertyDefinition(type="string", required=True),
                },
            )
        )

        # Begin transaction
        await context.begin_transaction()

        # Create test entities
        await context.create_entity(
            "Person", {"name": "John Doe", "age": 30, "city": "New York"}
        )
        await context.create_entity(
            "Person", {"name": "Jane Doe", "age": 28, "city": "Boston"}
        )
        await context.create_entity(
            "Person", {"name": "John Smith", "age": 30, "city": "New York"}
        )

        # Commit transaction
        await context.commit_transaction()

        # Test query with multiple conditions
        query_spec = {
            "entity_type": "Person",
            "conditions": [
                {"field": "age", "operator": "eq", "value": 30},
                {"field": "city", "operator": "eq", "value": "New York"},
            ],
        }
        results = await context.query(query_spec)
        assert len(results) == 2
        names = {result.properties["name"] for result in results}
        assert names == {"John Doe", "John Smith"}

        # Test query with no matching results
        query_spec = {
            "entity_type": "Person",
            "conditions": [
                {"field": "age", "operator": "eq", "value": 30},
                {"field": "city", "operator": "eq", "value": "Boston"},
            ],
        }
        results = await context.query(query_spec)
        assert len(results) == 0

    finally:
        # Clean up the context
        await context.cleanup()
