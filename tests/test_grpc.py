import pytest

from notification.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_send_push_from_users(
    mock_session, mock_fcm_repo, mock_credentials, mock_aiohttp_post
):
    service = NotificationService(
        service_account_path="dummy_path.json",
        project_id="dummy_project",
        session=mock_session,
    )

    message = {
        "notification": {"title": "Test Title", "body": "Test Body"},
        "data": {"key": "value"},
    }

    await service.send_push_from_users(message=message, user_ids=[1])

    assert mock_fcm_repo.get_fcm_token.called
    assert mock_aiohttp_post.called


@pytest.mark.asyncio
async def test_send_push_no_users(
    mock_session, mock_fcm_repo, mock_credentials, mock_aiohttp_post
):
    service = NotificationService(
        service_account_path="dummy_path.json",
        project_id="dummy_project",
        session=mock_session,
    )

    message = {"notification": {"title": "Broadcast", "body": "To all users"}}

    await service.send_push_from_users(message=message)

    assert mock_fcm_repo.get_fcm_token.called
    assert mock_aiohttp_post.called
