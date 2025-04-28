# Graph API

A REST API wrapper for the [graph-context](https://github.com/beanone/graph-context) library, built with FastAPI.

## Features

- Full CRUD operations for entities and relations
- Graph traversal and querying capabilities
- Type-safe API with Pydantic models
- OpenAPI documentation
- Async support
- Docker support for development and production

## Requirements

- Python 3.11+
- FastAPI
- Uvicorn
- graph-context>=0.3.3
- Docker and Docker Compose (optional)

## Installation

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/graph-api.git
cd graph-api
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
# Install test dependencies for local development
pip install -r requirements-tests.txt
```

### Docker Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/graph-api.git
cd graph-api
```

2. Build and start the development container:
```bash
docker-compose up --build api
```

The development container includes:
- Hot-reload for code changes
- Mounted source code and tests
- Development environment configuration
- Health checks
- Automatic restart on failure

To stop the development container:
```bash
docker-compose down
```

### Docker Development

The development container will automatically start with hot-reload enabled. The API will be available at `http://localhost:8000`.

Development container features:
- Hot-reload for code changes
- Mounted source code and tests
- Development environment configuration
- Health checks
- Automatic restart on failure

### Docker Production

To run the production container:

```bash
docker-compose up --build api-prod
```

Production container features:
- Multi-stage build for smaller image size
- Non-root user for security
- Resource limits and reservations
- Health checks
- Multiple workers for better performance
- Environment set to production
- No volume mounts (code is built into the image)

To stop the production container:
```bash
docker-compose down
```

Both development and production containers:
- Expose port 8000
- Have health checks configured
- Use `restart: unless-stopped` policy
- Set `PYTHONPATH=/app`

### Docker Environment Variables

The following environment variables can be set in the `docker-compose.yml` file or passed to the container:

- `PYTHONPATH`: Set to `/app` by default
- `ENVIRONMENT`: Set to `development` or `production`
- `WORKERS`: Number of Uvicorn workers (default: 1 for development, 4 for production)
- `HOST`: Host to bind to (default: 0.0.0.0)
- `PORT`: Port to bind to (default: 8000)

### Docker Health Checks

The containers include health checks that verify:
- The API is running and responding
- The server is accepting connections
- The application is healthy

Health check endpoint: `http://localhost:8000/health`

### Docker Logs

To view container logs:
```bash
# Development container
docker-compose logs -f api

# Production container
docker-compose logs -f api-prod
```

### Docker Cleanup

To clean up Docker resources:
```bash
# Stop and remove containers
docker-compose down

# Remove all unused containers, networks, images
docker system prune

# Remove all unused volumes
docker volume prune
```

### Docker Troubleshooting

Common issues and solutions:

1. Port already in use:
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

2. Container not starting:
```bash
# Check container logs
docker-compose logs api
# Check container status
docker-compose ps
```

3. Permission issues:
```bash
# Fix permissions on mounted volumes
sudo chown -R 1000:1000 .
```

4. Build cache issues:
```bash
# Rebuild without cache
docker-compose build --no-cache api
```

## Running the API

### Local Development

Start the API server:

```bash
uvicorn src.graph_api.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Docker Development

The development container will automatically start with hot-reload enabled. The API will be available at `http://localhost:8000`.

Development container features:
- Hot-reload for code changes
- Mounted source code and tests
- Development environment configuration
- Health checks
- Automatic restart on failure

### Docker Production

To run the production container:

```bash
docker-compose up --build api-prod
```

Production container features:
- Multi-stage build for smaller image size
- Non-root user for security
- Resource limits and reservations
- Health checks
- Multiple workers for better performance
- Environment set to production
- No volume mounts (code is built into the image)

To stop the production container:
```bash
docker-compose down
```

Both development and production containers:
- Expose port 8000
- Have health checks configured
- Use `restart: unless-stopped` policy
- Set `PYTHONPATH=/app`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## API Endpoints

### Entities

- `POST /api/v1/entities` - Create a new entity
- `GET /api/v1/entities/{entity_id}` - Get an entity by ID
- `PUT /api/v1/entities/{entity_id}` - Update an entity
- `DELETE /api/v1/entities/{entity_id}` - Delete an entity

### Relations

- `POST /api/v1/relations` - Create a new relation
- `GET /api/v1/relations/{relation_id}` - Get a relation by ID
- `PUT /api/v1/relations/{relation_id}` - Update a relation
- `DELETE /api/v1/relations/{relation_id}` - Delete a relation

### Graph Operations

- `POST /api/v1/query` - Query relations from a starting entity
- `POST /api/v1/traverse` - Traverse the graph from a starting entity

## Example Usage

### Creating an Entity

```python
import requests

# Create a person entity
response = requests.post(
    "http://localhost:8000/api/v1/entities",
    json={
        "entity_type": "Person",
        "properties": {
            "name": "John Doe",
            "age": 30
        }
    }
)
entity_id = response.json()["id"]
```

### Creating a Relation

```python
# Create a relation between two entities
response = requests.post(
    "http://localhost:8000/api/v1/relations",
    json={
        "relation_type": "KNOWS",
        "from_entity": entity_id_1,
        "to_entity": entity_id_2,
        "properties": {
            "since": 2023
        }
    }
)
```

### Querying Relations

```python
# Query all relations from an entity
response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "start": entity_id,
        "relation": "KNOWS",
        "direction": "outbound"
    }
)
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/graph_api

# Run specific test file
pytest tests/unit/test_api.py
```

### Code Style

This project uses Ruff for code formatting and linting:

```bash
# Format code
ruff format .

# Check code style
ruff check .
```

### Development Setup

1. Create a clean virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install test dependencies:
```bash
pip install -r requirements-tests.txt
```

3. Set up pre-commit hooks (optional):
```bash
pre-commit install
```

### Docker Development

The development container includes:
- Hot-reload for code changes
- Mounted source code and tests
- Development environment configuration

### Docker Production

The production container includes:
- Multi-stage build for smaller image size
- Non-root user for security
- Resource limits and reservations
- Health checks
- Multiple workers for better performance

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.