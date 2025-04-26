import pytest
from fastapi.testclient import TestClient
from main import app
from utils.nlu_processor import NLUProcessor

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def nlu_processor():
    return NLUProcessor()