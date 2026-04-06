import asyncio
import json
import logging
import uuid
from datetime import date, datetime
from typing import Any, MutableMapping, Optional
from uuid import UUID

from aio_pika import (
    Exchange,
    ExchangeType,
    Message,
    RobustChannel,
    RobustConnection,
    connect_robust,
)
from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from config import settings

exchange_map = {
    ExchangeType.DIRECT: "direct_exchange",
    ExchangeType.FANOUT: "fanout_exchange",
    ExchangeType.TOPIC: "topic_exchange"
}

class RabbitMQProducer:
    def __init__(self, exchange_type: ExchangeType):
        self.exchange_type = exchange_type
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.exchange: Exchange | None = None
        self.callback_queue: Optional[AbstractQueue] = None
        self.futures: MutableMapping[str, asyncio.Future] = {}

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


    async def connect(self) -> None:
        """
        Инициализация соединения с брокером сообщений и открытие канала.
        """
        attempt = 0
        while attempt < settings.rmq_max_reconnect_attempts:
            try:
                self.connection = await connect_robust(
                    settings.rmq_uri, loop=asyncio.get_running_loop()
                )
                self.channel = await self.connection.channel()
                self.exchange = await self.channel.declare_exchange(
                    "core", # exchange_map.get(self.exchange_type),
                    self.exchange_type,
                    durable=True,
                    auto_delete=False,
                )
                # Создание callback очереди для ответа
                self.callback_queue = await self.channel.declare_queue(
                    exclusive=True,
                    auto_delete=True,
                    durable=False,
                )
                if self.exchange_type == ExchangeType.DIRECT:
                    # Для DIRECT: привязываем очередь к exchange с конкретным routing_key
                    await self.callback_queue.bind(
                        self.exchange,
                        routing_key=self.callback_queue.name
                    )

                elif self.exchange_type == ExchangeType.FANOUT:
                    # Для FANOUT: привязываем без routing_key (сообщения получат все очереди, подключенные к exchange)
                    await self.callback_queue.bind(self.exchange)

                elif self.exchange_type == ExchangeType.TOPIC:
                    # Для TOPIC: используем pattern-based routing
                    # Например, все ответы будут приходить с routing_key pattern "response.*"
                    topic_routing_key = f"response.*"
                    await self.callback_queue.bind(
                        self.exchange,
                        routing_key=topic_routing_key
                    )

                else:
                    # Fallback для неизвестных типов
                    await self.callback_queue.bind(
                        self.exchange,
                        routing_key=self.callback_queue.name
                    )
                await self.callback_queue.consume(self.on_response)
                logging.info("RPC Client successfully connected to RabbitMQ")
                return

            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Failed to connect to broker (attempt {attempt}):"
                    f" {e.__class__.__name__}: {e}"
                )
                await asyncio.sleep(settings.rmq_reconnect_delay)

    async def stop(self) -> None:
        """Очистка и закрытие соединения и канала с брокером."""
        try:
            # Отмена всех ожидающих futures
            for corr_id, future in list(self.futures.items()):
                if not future.done():
                    future.set_exception(asyncio.CancelledError("RPC client stopped"))
                del self.futures[corr_id]
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            logging.info("RPC Client connection closed")
        except Exception as e:
            logging.error(f"Error during RPC client shutdown: {e}")


    @staticmethod
    def json_serializer(obj: Any) -> str:
        """Конвертация нестандартных типов в JSON-совместимый формат."""
        if isinstance(obj, (UUID, datetime, date)):
            return str(obj)
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")  # или base64 при необходимости
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        """Обработчик ответных сообщений"""
        if not message.correlation_id:
            logging.error("Received message without correlation_id")
            return
        try:
            future = self.futures.pop(message.correlation_id)
            if not future.done():
                future.set_result(message.body)
        except KeyError:
            logging.warning(f"Unknown correlation_id: {message.correlation_id}")
        except Exception as e:
            logging.error(f"Error processing response: {e}")

    async def publish(
        self,
        event: Any,
        routing_key: str,
        timeout: float = 10.0,  # Таймаут ожидания ответа
    ) -> None:
        """Публикация RPC запроса и ожидание ответа"""
        # Попытка переподключение если соединение оборвалось
        if not self.connection or self.connection.is_closed:
            await self.connect()
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        try:
            # Создаем сообщение
            message = Message(
                body=json.dumps(json.loads(event), default=self.json_serializer).encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
                content_type="application/json",
                expiration=int(timeout * 1000),
            )
            # Для FANOUT exchange routing_key игнорируется
            if self.exchange_type == ExchangeType.FANOUT:
                routing_key = ""

            await self.exchange.publish(message, routing_key=routing_key, mandatory=True)
            logging.debug(f"Message published to {routing_key}: {event}")
            # Ждем ответа с таймаутом
            response_body = await asyncio.wait_for(future, timeout=timeout)
            response_data = json.loads(response_body.decode())
            logging.debug(f"Received response: {response_data}")
            return response_data
        except asyncio.TimeoutError:
            logging.error(f"Timeout waiting for response to {correlation_id}")
            raise TimeoutError("Server did not respond within timeout")
        except Exception:
            logging.exception(f"Failed to publish message to routing_key={routing_key}")
        finally:
            # Очищаем future только если он еще существует
            if correlation_id and correlation_id in self.futures:
                fut = self.futures.pop(correlation_id)
                if not fut.done():
                    fut.cancel()
