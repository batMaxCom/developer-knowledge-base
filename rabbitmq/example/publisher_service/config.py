from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class MessageBrokerSettings(BaseSettings):
    rmq_user: str = Field(alias="RMQ_USER", default="rmq_user")
    rmq_password: str = Field(alias="RMQ_PASSWORD", default="rmq_pass")
    rmq_host: str = Field(alias="RMQ_HOST", default="localhost")
    rmq_port: int = Field(alias="RMQ_PORT", default=5672)
    # rmq_exchange_name: str = Field(
    #     alias="RMQ_EXCHANGE_NAME", default="data_updates"
    # )
    rmq_reconnect_delay: int = Field(alias="RMQ_RECONNECT_DELAY", default=5)
    rmq_max_reconnect_attempts: int = Field(alias="RMQ_MAX_RECONNECT_ATTEMPTS", default=10)

    @property
    def rmq_uri(self) -> str:
        return (
            f"amqp://{self.rmq_user}:{self.rmq_password}@{self.rmq_host}:{self.rmq_port}/"
        )

@lru_cache
def get_settings() -> MessageBrokerSettings:
    """
    Функция для получения экземпляра настроек с использованием кэширования.
    """
    return MessageBrokerSettings()


settings = get_settings()
