"""Integration tests for knowledge graph operations.

This module contains end-to-end tests for constructing and manipulating
a knowledge graph using the API.
"""

import pytest
from fastapi.testclient import TestClient

from graph_api.api.router import router
from graph_api.services.graph_service import GraphService
from graph_context import BaseGraphContext


@pytest.fixture
def app():
    """Create a FastAPI application for testing."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    app.state.graph_context = BaseGraphContext()
    app.dependency_overrides = {
        "get_graph_service": lambda: GraphService(app.state.graph_context)
    }
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.mark.integration
def test_knowledge_graph_construction(client: TestClient):
    """Test constructing and manipulating a knowledge graph end-to-end."""
    # 1. Register entity types
    person_type = {
        "name": "Person",
        "description": "A person entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "age": {"type": "integer", "required": True},
            "occupation": {"type": "string", "required": False},
        },
        "indexes": ["name", "age"],
    }

    company_type = {
        "name": "Company",
        "description": "A company entity",
        "properties": {
            "name": {"type": "string", "required": True},
            "founded": {"type": "integer", "required": True},
            "industry": {"type": "string", "required": False},
        },
        "indexes": ["name", "founded"],
    }

    # Register entity types
    person_response = client.post("/api/v1/entity-types", json=person_type)
    assert person_response.status_code == 200

    company_response = client.post("/api/v1/entity-types", json=company_type)
    assert company_response.status_code == 200

    # 2. Register relation types
    works_at_type = {
        "name": "WORKS_AT",
        "description": "A relationship between a person and a company",
        "properties": {
            "role": {"type": "string", "required": True},
            "start_date": {"type": "integer", "required": True},
        },
        "indexes": ["role", "start_date"],
        "from_types": ["Person"],
        "to_types": ["Company"],
    }

    knows_type = {
        "name": "KNOWS",
        "description": "A relationship between two people",
        "properties": {"since": {"type": "integer", "required": True}},
        "indexes": ["since"],
        "from_types": ["Person"],
        "to_types": ["Person"],
    }

    # Register relation types
    works_at_response = client.post("/api/v1/relation-types", json=works_at_type)
    assert works_at_response.status_code == 200

    knows_response = client.post("/api/v1/relation-types", json=knows_type)
    assert knows_response.status_code == 200

    # 3. Create entities
    # Create people
    alice_data = {
        "entity_type": "Person",
        "properties": {
            "name": "Alice Smith",
            "age": 30,
            "occupation": "Software Engineer",
        },
    }

    bob_data = {
        "entity_type": "Person",
        "properties": {
            "name": "Bob Johnson",
            "age": 35,
            "occupation": "Data Scientist",
        },
    }

    # Create companies
    tech_corp_data = {
        "entity_type": "Company",
        "properties": {"name": "TechCorp", "founded": 2010, "industry": "Technology"},
    }

    # Create entities
    alice_response = client.post("/api/v1/entities", json=alice_data)
    assert alice_response.status_code == 200
    alice_id = alice_response.json()["id"]

    bob_response = client.post("/api/v1/entities", json=bob_data)
    assert bob_response.status_code == 200
    bob_id = bob_response.json()["id"]

    tech_corp_response = client.post("/api/v1/entities", json=tech_corp_data)
    assert tech_corp_response.status_code == 200
    tech_corp_id = tech_corp_response.json()["id"]

    # 4. Create relations
    # Alice works at TechCorp
    alice_works_at_tech = {
        "relation_type": "WORKS_AT",
        "from_entity": alice_id,
        "to_entity": tech_corp_id,
        "properties": {"role": "Senior Engineer", "start_date": 2020},
    }

    # Bob works at TechCorp
    bob_works_at_tech = {
        "relation_type": "WORKS_AT",
        "from_entity": bob_id,
        "to_entity": tech_corp_id,
        "properties": {"role": "Lead Data Scientist", "start_date": 2019},
    }

    # Alice knows Bob
    alice_knows_bob = {
        "relation_type": "KNOWS",
        "from_entity": alice_id,
        "to_entity": bob_id,
        "properties": {"since": 2021},
    }

    # Create relations
    alice_works_response = client.post("/api/v1/relations", json=alice_works_at_tech)
    assert alice_works_response.status_code == 200

    bob_works_response = client.post("/api/v1/relations", json=bob_works_at_tech)
    assert bob_works_response.status_code == 200

    alice_knows_response = client.post("/api/v1/relations", json=alice_knows_bob)
    assert alice_knows_response.status_code == 200

    # 5. Query the graph
    # Query all people
    people_query = {"query_spec": {"entity_type": "Person", "conditions": []}}

    people_response = client.post("/api/v1/query", json=people_query)
    assert people_response.status_code == 200
    people = people_response.json()
    assert len(people) == 2

    # Query people who work at TechCorp
    tech_employees_query = {
        "query_spec": {
            "entity_type": "Person",
            "conditions": [{"field": "name", "operator": "eq", "value": "Alice Smith"}],
        }
    }

    tech_employees_response = client.post("/api/v1/query", json=tech_employees_query)
    assert tech_employees_response.status_code == 200
    tech_employees = tech_employees_response.json()
    assert len(tech_employees) == 1

    # 6. Update entities
    # Update Alice's age
    alice_update = {"name": "Alice Smith", "age": 31}

    alice_update_response = client.put(
        f"/api/v1/entities/{alice_id}", json=alice_update
    )
    assert alice_update_response.status_code == 200
    updated_alice = alice_update_response.json()
    assert updated_alice["properties"]["age"] == 31

    # 7. Update relations
    # Update Alice's role at TechCorp
    alice_works_id = alice_works_response.json()["id"]
    alice_role_update = {
        "role": "Principal Engineer",
        "start_date": 2020,  # Include the existing start_date
    }

    alice_role_update_response = client.put(
        f"/api/v1/relations/{alice_works_id}", json=alice_role_update
    )
    assert alice_role_update_response.status_code == 200
    updated_alice_works = alice_role_update_response.json()
    assert updated_alice_works["properties"]["role"] == "Principal Engineer"

    # 8. Delete relations
    # Delete Alice's relationship with Bob
    alice_knows_id = alice_knows_response.json()["id"]
    delete_knows_response = client.delete(f"/api/v1/relations/{alice_knows_id}")
    assert delete_knows_response.status_code == 200

    # Verify the relation is deleted
    get_knows_response = client.get(f"/api/v1/relations/{alice_knows_id}")
    assert get_knows_response.status_code == 404

    # 9. Delete entities
    # Delete Bob
    delete_bob_response = client.delete(f"/api/v1/entities/{bob_id}")
    assert delete_bob_response.status_code == 200

    # Verify Bob is deleted
    get_bob_response = client.get(f"/api/v1/entities/{bob_id}")
    assert get_bob_response.status_code == 404

    # Verify Bob's relations are also deleted
    bob_works_id = bob_works_response.json()["id"]
    get_bob_works_response = client.get(f"/api/v1/relations/{bob_works_id}")
    assert get_bob_works_response.status_code == 404
