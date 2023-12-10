from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base
from sqlalchemy.ext.declarative import declarative_base
import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Set level of logger
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

# Setup the TestClient
client = TestClient(app)
logger.info('TestClient created')

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
# DATABASE_URL = "sqlite:///test.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info('TestingSessionLocal created')

# Dependency to override the get_db dependency in the main app
def override_get_db():
    logger.info('Creating database')
    database = TestingSessionLocal()
    yield database
    database.close()

logger.info('Overriding get_db dependency in main app')
app.dependency_overrides[get_db] = override_get_db


def test_create_item():
    logger.info('Testing create_item')
    response = client.post(
        "/items/", json={"name": "Test Item", "description": "This is a test item"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert "id" in data


def test_read_item():
    logger.info('Testing read_item')
    # Create an item
    response = client.post(
        "/items/", json={"name": "Test Item", "description": "This is a test item"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    item_id = data["id"]

    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "This is a test item"
    assert data["id"] == item_id


def test_update_item():
    item_id = 1
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated Item", "description": "This is an updated item"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["description"] == "This is an updated item"
    assert data["id"] == item_id


def test_delete_item():
    item_id = 1
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == item_id
    # Try to get the deleted item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404, response.text


def setup() -> None:
    # Create the tables in the test database
    Base.metadata.create_all(bind=engine)
    logger.info('Tables created in test database')


def teardown() -> None:
    # Drop the tables in the test database
    Base.metadata.drop_all(bind=engine)
    logger.info('Tables dropped in test database')

