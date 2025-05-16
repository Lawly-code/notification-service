from datetime import datetime, UTC

from lawly_db.db_models import FCMToken, RefreshSession, Subscribe
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from notification.repositories.base_repository import BaseRepository


class FCMTokenRepository(BaseRepository):
    model = FCMToken

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_fcm_token(
        self, user_id: int | None = None, is_base: bool | None = None
    ) -> list[str] | None:
        """
        Получение FCM токенов по уникальным device_id.
        """
        dt = datetime.now(UTC)
        unix_time = int(dt.timestamp())

        stmt = (
            select(func.max(self.model.token))
            .select_from(self.model)
            .join(
                RefreshSession,
                and_(
                    self.model.user_id == RefreshSession.user_id,
                    self.model.device_id == RefreshSession.device_id,
                ),
            )
        )

        if is_base is not None:
            conditions = [Subscribe.is_base == is_base]

            if is_base is False:
                conditions.append(Subscribe.end_date > datetime.now())

            stmt = stmt.join(Subscribe, self.model.user_id == Subscribe.user_id).where(
                *conditions
            )

        stmt = stmt.where(RefreshSession.expires_in > unix_time)

        if user_id is not None:
            stmt = stmt.where(self.model.user_id == user_id)

        stmt = stmt.group_by(self.model.device_id)

        result = await self.session.execute(stmt)
        tokens = list(result.scalars().all())
        return tokens

    async def delete_not_work_fcm_token(self, token: str):
        """
        Удаление неработающего FCM токена
        :param token: FCM токен
        :return: None
        """
        query = select(self.model).where(self.model.token == token)
        result = await self.session.execute(query)
        fcm_tokens = result.scalars().all()
        if fcm_tokens:
            for fcm_token in fcm_tokens:
                await self.session.delete(fcm_token)
            await self.session.commit()
