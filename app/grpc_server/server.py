import grpc
import logging
from typing import Optional

from google.protobuf import empty_pb2
from google.protobuf.json_format import MessageToDict

from lawly_db.db_models.db_session import create_session
from protos.notification_service import (
    notification_service_pb2_grpc as notification_pb2_grpc,
)

from config import SERVICE_ACCOUNT_PATH, PROJECT_ID
from notification.services.notification_service import NotificationService


class NotificationServiceServicer(notification_pb2_grpc.NotificationServiceServicer):
    """
    Реализация GRPC сервиса для работы с AI Assistant (асинхронная версия)
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def SendPushFromUsers(self, request, context):
        try:
            message = MessageToDict(request.message)
            user_ids = list(request.user_ids) if request.user_ids else None
            is_base = request.is_base if request.HasField("is_base") else None

            async with create_session() as session:
                service = NotificationService(
                    service_account_path=SERVICE_ACCOUNT_PATH,
                    project_id=PROJECT_ID,
                    session=session,
                )

                await service.send_push_from_users(
                    message=message, user_ids=user_ids, is_base=is_base
                )

            return empty_pb2.Empty()

        except Exception as e:
            self.logger.error(f"❌ Ошибка в SendPushFromUsers: {str(e)}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Внутренняя ошибка: {str(e)}")
            return empty_pb2.Empty()


class AsyncGRPCServer:
    """
    Класс-обертка для запуска асинхронного GRPC сервера
    """

    def __init__(self, port: int = 50051):
        self.port = port
        self.server = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """
        Запуск асинхронного GRPC сервера
        """
        # Создаем экземпляр асинхронного сервера
        self.server = grpc.aio.server()

        # Создаем сервисер и добавляем его на сервер
        servicer = NotificationServiceServicer()
        notification_pb2_grpc.add_NotificationServiceServicer_to_server(
            servicer, self.server
        )

        # Добавляем порт для прослушивания
        listen_addr = f'[::]:{self.port}'
        self.server.add_insecure_port(listen_addr)

        # Запускаем сервер
        await self.server.start()
        self.logger.info(
            f"Асинхронный GRPC сервер Notification Service запущен на порту {self.port}"
        )

        return self

    async def stop(self, grace: Optional[float] = None):
        """
        Остановка GRPC сервера

        Args:
            grace: период ожидания в секундах перед принудительной остановкой
        """
        if self.server:
            await self.server.stop(grace)
            self.logger.info("GRPC сервер Notification Service остановлен")

    async def wait_for_termination(self):
        """
        Ожидание завершения работы сервера
        """
        if self.server:
            await self.server.wait_for_termination()
