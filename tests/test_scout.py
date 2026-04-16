import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.features.scout.assessment import enrich_with_scout_assessment

@pytest.fixture
def dummy_workout():
    return {
        "id": 12345,
        "distance": 8000.0,
        "splits_metric": [{"split": 1, "pace": 300, "hr": 150}],
        "weather": {"condition": "Sunny", "temperature": 20},
        "metrics": {"intensity": "Moderate"}
    }

@pytest.mark.asyncio
async def test_enrich_with_scout_assessment_success(dummy_workout):
    mock_response = MagicMock()
    mock_response.text = "Paced well. No cardiac drift. Nice weather."
    
    mock_client_instance = MagicMock()
    mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("src.features.scout.assessment.Client") as mock_client_class:
        mock_client_class.return_value = mock_client_instance
        result = await enrich_with_scout_assessment(dummy_workout)

    assert result == "Paced well. No cardiac drift. Nice weather."
    mock_client_instance.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_enrich_with_scout_assessment_failure(dummy_workout):
    mock_client_instance = MagicMock()
    mock_client_instance.aio.models.generate_content = AsyncMock(side_effect=Exception("API failure"))

    with patch("src.features.scout.assessment.Client") as mock_client_class:
        mock_client_class.return_value = mock_client_instance
        result = await enrich_with_scout_assessment(dummy_workout)

    assert result is None
