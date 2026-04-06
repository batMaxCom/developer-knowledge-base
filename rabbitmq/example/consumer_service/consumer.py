import asyncio
import json
import logging
from functools import partial
from typing import Optional

from fastapi import WebSocket

from aio_pika import (
    Exchange,
    ExchangeType,
    Message,
    RobustChannel,
    RobustConnection,
    connect_robust,
)
from aio_pika.abc import AbstractIncomingMessage

from config import settings

exchange_map = {
    ExchangeType.DIRECT: "direct_exchange",
    ExchangeType.FANOUT: "fanout_exchange",
    ExchangeType.TOPIC: "topic_exchange"
}

class RabbitMQConsumer:
    def __init__(self, exchange_type: ExchangeType, routing_key: str):
        self.exchange_type = exchange_type
        self.routing_key = routing_key
        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None
        self.exchange: Exchange | None = None
        self.request_queue = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    async def connect(self) -> None:
        """Установка соединения с автоматическими повторными попытками"""
        attempt = 0
        while attempt < settings.rmq_max_reconnect_attempts:
            try:
                self.connection = await connect_robust(  # Создаем подключение к брокеру
                    settings.rmq_uri,
                    timeout=10  # Таймаут подключения
                )
                self.channel = await self.connection.channel()  # Создание канала для взаимодействия с RabbitMQ
                self.exchange = await self.channel.declare_exchange(
                    "monitoring", # exchange_map.get(self.exchange_type),
                    self.exchange_type,
                    durable=True,  # Сохранение exchange при перезагрузке RabbitMQ
                    auto_delete=False,  # Не удалять exchange при отсутствии подписчиков
                )
                # обрабатываем
                self.request_queue = await self.channel.declare_queue(
                    "monitoring_event", # exchange_map.get(self.exchange_type).replace("exchange", "queue"),
                    auto_delete=True,
                    durable=False,
                    arguments={  # Дополнительные аргументы очереди
                        'x-message-ttl': 60000,  # Время жизни сообщений (60 секунд)
                        'x-dead-letter-exchange': f'{settings.rmq_exchange_name}.dlx'  # Exchange для мертвых сообщений
                    }
                )
                # Привязка очереди к exchange с ключом маршрутизации
                await self.request_queue.bind(self.exchange, routing_key=self.routing_key)
                logging.info("Successfully connected to RabbitMQ")
                return

            except Exception as e:
                attempt += 1
                logging.error(f"Connection attempt {attempt} failed: {e}")
                if attempt >= settings.rmq_max_reconnect_attempts:
                    raise
                await asyncio.sleep(settings.rmq_reconnect_delay * attempt)  # Exponential backoff

    async def _send_response(
        self, reply_to_rk: str, corr_id: str, data: dict = None
    ) -> None:
        """Отправляет ответ во ВРЕМЕННУЮ очередь клиента."""
        try:
            response_message = Message(
                body=json.dumps(data).encode(),
                correlation_id=corr_id,
                content_type="application/json",
                expiration=10000  # Время жизни ответа (10 секунд)
            )
            await self.exchange.publish(response_message, routing_key=reply_to_rk)
        except Exception as e:
            logging.error(f"Failed to send response for {corr_id}: {e}")

    async def _process_message(self, message: AbstractIncomingMessage) -> dict:
        """Обработка сообщения"""
        try:
            request_data = json.loads(message.body.decode())
            logging.info(f"Processing request: {request_data}")
            # Здесь должна быть ваша бизнес-логика обработки запроса
            return {"response": "ok", "processed": True}  # Заглушка успешной обработки
        except json.JSONDecodeError:
            logging.error("Invalid JSON in message")
            return {"error": "Invalid JSON format"}
        except Exception as e:
            logging.exception("Error processing message")
            return {"error": str(e)}

    async def handle(self, message: AbstractIncomingMessage, websocket: WebSocket) -> None:
        async with message.process():
            try:
                # Получение адреса очереди для ответа
                reply_to = message.reply_to
                # Получение ID корреляции для сопоставления запроса-ответа
                correlation_id = message.correlation_id
                # Получение ключа маршрутизации сообщения
                if not reply_to:
                    reply_to = None
                    # logging.error("No 'reply_to' in message. Cannot send response.")
                    # return
                # Обработка сообщения (вызов метода обработки)
                result = await self._process_message(message)
                # Если очередь слушает по паттерну "response.*" отправляем туда
                if self.exchange_type == ExchangeType.TOPIC:
                    reply_to = f"response.{reply_to}"
                await websocket.send_text(message.body.__str__())
                await self._send_response(reply_to, correlation_id, result)
                logging.info(f"Request {correlation_id} processed successfully")
            except Exception as e:
                logging.exception("Failed to process RPC request")
                if reply_to and correlation_id:
                    error_data = {"error": f"Internal server error: {str(e)}"}
                    await self._send_response(reply_to, correlation_id, error_data)

    async def start_consuming(self, websocket: WebSocket) -> None:
        """Начинаем слушать очередь запросов."""
        handler = partial(self.handle, websocket=websocket)
        await self.request_queue.consume(handler, no_ack=False)
        logging.info("RPC Consumer started listening on 'data_requests_queue'")
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            logging.info("Consumer stopped by cancellation")
        except Exception as e:
            logging.error(f"Consumer stopped with error: {e}")

    async def stop(self) -> None:
        """Корректное завершение работы потребителя"""
        try:
            if self.connection and not self.connection.is_closed:
                # Закрытие соединения с RabbitMQ
                await self.connection.close()
            logging.info("RabbitMQ connection closed")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
