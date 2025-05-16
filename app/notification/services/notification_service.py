import json

import aiohttp
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from notification.repositories.fcm_token_repository import FCMTokenRepository
from config import __log__


class NotificationService:
    def __init__(
        self, service_account_path: str, project_id: str, session: AsyncSession
    ):
        self.project_id = project_id
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        self.fcm_token_repo = FCMTokenRepository(session=session)

    async def _send(self, message: dict):
        self.credentials.refresh(Request())
        access_token = self.credentials.token

        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            json_payload = json.loads(json.dumps({"message": message}))
        except TypeError as e:
            __log__.error(f"Ошибка сериализации сообщения в JSON: {e}")
            raise

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json_payload) as resp:
                data = await resp.json()
                if resp.status != 200:
                    __log__.error(f"FCM error: {resp.status} - {data}")
                    raise Exception(f"FCM error: {resp.status} - {data}")

                return data

    async def _send_to_tokens(self, message_body: dict, tokens: list[str]):
        tokens_to_remove = []

        async def send_single(token):
            message = {"token": token, **message_body}
            try:
                result = await self._send(message)
                return {"token": token, "status": "success", "response": result}
            except Exception as e:
                __log__.warning(f"FCM token {token} failed: {e}")
                tokens_to_remove.append(token)
                return {"token": token, "status": "error", "error": str(e)}

        await asyncio.gather(*(send_single(token) for token in tokens))

        for token in tokens_to_remove:
            await self.fcm_token_repo.delete_not_work_fcm_token(token=token)

    async def send_push_from_users(
        self, message: dict, user_ids: list[int] | None = None, is_base: bool = None
    ):
        """
        Отправка уведомлений пользователям по user_id
        :param message: уведомление
        :param user_ids: id пользователей, если None, то отправляем всем пользователям
        :param is_base: базовый параметр, если True, то отправляем всем пользователям с базовой подпиской
        """
        if not user_ids:
            tokens = await self.fcm_token_repo.get_fcm_token(is_base=is_base)
            if not tokens:
                return
            await self._send_to_tokens(message_body=message, tokens=tokens)
            return

        for user_id in user_ids:
            tokens = await self.fcm_token_repo.get_fcm_token(
                user_id=user_id, is_base=is_base
            )
            if not tokens:
                continue
            await self._send_to_tokens(message_body=message, tokens=tokens)
