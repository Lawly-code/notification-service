from pydantic import BaseModel, Field, field_validator, constr
from typing import Dict, Any, List
import re


class Notification(BaseModel):
    title: str | None = Field(default=None, description="Заголовок уведомления")
    body: str | None = Field(default=None, description="Тело уведомления")


class FCMMessageDTO(BaseModel):
    to: constr(strip_whitespace=True, min_length=1) | None = Field(
        default=None, description="Один FCM токен, /topics/название или condition"
    )
    registration_ids: List[constr(strip_whitespace=True, min_length=10)] | None = Field(
        default=None, description="Список токенов устройств, если массовая отправка"
    )
    priority: constr(strip_whitespace=True, pattern="^(high|normal)$") | None = Field(
        default="high", description="Приоритет уведомления: high или normal"
    )
    notification: Notification | None = Field(
        default=None, description="Отображаемая часть уведомления: заголовок и тело"
    )
    data: Dict[str, Any] | None = Field(
        default_factory=dict,
        description="Произвольные кастомные данные, которые можно обработать в клиенте",
    )
    collapse_key: str | None = Field(
        default=None, description="Ключ для схлопывания одинаковых сообщений"
    )
    content_available: bool | None = Field(
        default=None, description="Для silent push (например, обновить контент в фоне)"
    )
    mutable_content: bool | None = Field(
        default=None, description="Позволяет изменять уведомление до показа (iOS)"
    )
    time_to_live: int | None = Field(
        default=None,
        ge=0,
        le=2419200,
        description="Время жизни уведомления в секундах (0 - 2419200)",
    )

    @field_validator("to")
    @classmethod
    def validate_to(cls, v: str | None) -> str | None:
        if v is None:
            return v
        pattern = r"^(/topics/|/conditions/)?[a-zA-Z0-9\-_:.]+$"
        if not re.match(pattern, v):
            raise ValueError("Поле 'to' должно быть FCM токеном, темой или условием")
        return v

    @field_validator("registration_ids")
    @classmethod
    def validate_registration_ids(cls, v: List[str] | None) -> List[str] | None:
        if v is None:
            return v
        if not (1 <= len(v) <= 1000):
            raise ValueError("registration_ids должен содержать от 1 до 1000 токенов")
        return v
