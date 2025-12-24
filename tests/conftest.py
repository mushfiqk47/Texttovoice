import pytest
from backend.services import tts_service

@pytest.fixture
def mock_tts_service():
    """Returns the singleton service instance."""
    return tts_service
