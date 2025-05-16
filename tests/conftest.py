import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_fcm_repo():
    with patch(
        "notification.services.notification_service.FCMTokenRepository"
    ) as mock_repo:
        repo_instance = mock_repo.return_value
        repo_instance.get_fcm_token = AsyncMock(
            return_value=["mock_token_1", "mock_token_2"]
        )
        repo_instance.delete_not_work_fcm_token = AsyncMock()
        yield repo_instance


@pytest.fixture
def mock_credentials():
    with patch(
        "notification.services.notification_service.service_account.Credentials"
    ) as mock_credentials_cls:
        mock_credentials = mock_credentials_cls.from_service_account_file.return_value
        mock_credentials.token = "mock_token"
        mock_credentials.refresh = MagicMock()
        yield mock_credentials


@pytest.fixture
def mock_aiohttp_post():
    with patch(
        "notification.services.notification_service.aiohttp.ClientSession.post"
    ) as mock_post:
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_post.return_value = mock_response
        yield mock_post
